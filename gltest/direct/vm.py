"""
VMContext - Foundry-style test VM for GenLayer contracts.

Provides cheatcodes for:
- Setting sender/value (vm.sender, vm.value)
- Snapshots and reverts (vm.snapshot(), vm.revert())
- Mocking nondet operations (vm.mock_web(), vm.mock_llm())
- Expecting reverts (vm.expect_revert())
- Pranking (vm.prank(), vm.startPrank(), vm.stopPrank())
"""

from __future__ import annotations

import re
import sys
import hashlib
import datetime as _dt_module
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass, field
from typing import Any, Optional, Pattern, List, Tuple, Dict
from unittest.mock import patch

from ..types import MockedWebResponseData

_sentinel = object()


def _now_iso() -> str:
    """Return current UTC time as ISO string (default for _datetime)."""
    return _dt_module.datetime.now(_dt_module.timezone.utc).isoformat().replace('+00:00', 'Z')


@dataclass
class Snapshot:
    """Full VM state snapshot for revert functionality."""
    id: int
    storage_data: Dict[bytes, bytes]
    balances: Dict[bytes, int]
    web_mocks: List[Tuple[Any, Any]]
    llm_mocks: List[Tuple[Any, str]]
    prank_stack: List[Any]
    captured_validators: List[Tuple[Any, Any, Any]]
    sender: Any
    origin: Any
    value: int
    chain_id: int
    datetime: str
    live_web_handler: Optional[Any] = None
    live_llm_handler: Optional[Any] = None


class InmemManager:
    """
    In-memory storage manager compatible with genlayer.py.storage.
    """

    def __init__(self):
        self._parts: Dict[bytes, Tuple["Slot", bytearray]] = {}

    def get_store_slot(self, slot_id: bytes) -> "Slot":
        res = self._parts.get(slot_id)
        if res is None:
            slot = Slot(slot_id, self)
            self._parts[slot_id] = (slot, bytearray())
            return slot
        return res[0]

    def do_read(self, slot_id: bytes, off: int, length: int) -> bytes:
        res = self._parts.get(slot_id)
        if res is None:
            slot = Slot(slot_id, self)
            mem = bytearray()
            self._parts[slot_id] = (slot, mem)
        else:
            _, mem = res

        needed = off + length
        if len(mem) < needed:
            mem.extend(b'\x00' * (needed - len(mem)))

        return bytes(memoryview(mem)[off:off + length])

    def do_write(self, slot_id: bytes, off: int, what: bytes) -> None:
        res = self._parts.get(slot_id)
        if res is None:
            slot = Slot(slot_id, self)
            mem = bytearray()
            self._parts[slot_id] = (slot, mem)
        else:
            _, mem = res

        what_view = memoryview(what)
        length = len(what_view)

        needed = off + length
        if len(mem) < needed:
            mem.extend(b'\x00' * (needed - len(mem)))

        memoryview(mem)[off:off + length] = what_view

    def snapshot(self) -> Dict[bytes, bytes]:
        return {
            slot_id: bytes(mem)
            for slot_id, (_, mem) in self._parts.items()
        }

    def restore(self, data: Dict[bytes, bytes]) -> None:
        self._parts.clear()
        for slot_id, mem_data in data.items():
            slot = Slot(slot_id, self)
            self._parts[slot_id] = (slot, bytearray(mem_data))


class Slot:
    """Storage slot compatible with genlayer.py.storage."""

    __slots__ = ('id', 'manager', '_indir_cache')

    def __init__(self, slot_id: bytes, manager: InmemManager):
        self.id = slot_id
        self.manager = manager
        self._indir_cache = hashlib.sha3_256(slot_id)

    def __reduce__(self):
        # _indir_cache (hashlib.HASH) is not picklable; recompute on unpickle
        return (Slot, (self.id, self.manager))

    def read(self, off: int, length: int) -> bytes:
        return self.manager.do_read(self.id, off, length)

    def write(self, off: int, what: bytes) -> None:
        self.manager.do_write(self.id, off, what)

    def indirect(self, off: int) -> "Slot":
        hasher = self._indir_cache.copy()
        hasher.update(off.to_bytes(4, 'little'))
        return self.manager.get_store_slot(hasher.digest())


ROOT_SLOT_ID = b'\x00' * 32


@dataclass
class VMContext:
    """
    Test VM context providing Foundry-style cheatcodes.

    Usage:
        vm = VMContext()
        vm.sender = Address("0x" + "a" * 40)
        vm.mock_web("api.example.com", {"status": 200, "body": "{}"})

        with vm.activate():
            contract = deploy_contract("Token.py", vm, owner)
            contract.transfer(bob, 100)
    """

    # Message context
    _sender: Optional[Any] = None
    _origin: Optional[Any] = None
    _contract_address: Optional[Any] = None
    _value: int = 0
    _chain_id: int = 1
    _datetime: str = field(default_factory=_now_iso)

    # Storage
    _storage: InmemManager = field(default_factory=InmemManager)
    _balances: Dict[bytes, int] = field(default_factory=dict)

    # Snapshots
    _snapshots: Dict[int, Snapshot] = field(default_factory=dict)
    _snapshot_counter: int = 0

    # Mocks
    _web_mocks: List[Tuple[Pattern, MockedWebResponseData]] = field(default_factory=list)
    _llm_mocks: List[Tuple[Pattern, str]] = field(default_factory=list)

    # Expect revert
    _expect_revert: Optional[str] = None
    _expect_revert_any: bool = False

    # Prank stack
    _prank_stack: List[Any] = field(default_factory=list)

    # Return value capture
    _return_value: Any = None
    _returned: bool = False

    # Validator capture (from run_nondet calls)
    _captured_validators: List[Tuple[Any, Any, Any]] = field(default_factory=list)

    # Pickling validation (opt-in)
    _check_pickling: bool = False

    # Strict mock tracking (opt-in)
    _strict_mocks: bool = False
    _web_mocks_hit: set = field(default_factory=set)
    _llm_mocks_hit: set = field(default_factory=set)

    # Live I/O handlers (for glsim — fallback when no mock matches)
    _live_web_handler: Optional[Any] = None
    _live_llm_handler: Optional[Any] = None

    # Cross-contract call hook (for glsim — handles DeployContract/CallContract/PostMessage)
    _gl_call_hook: Optional[Any] = None

    # Debug tracing
    _traces: List[str] = field(default_factory=list)
    _trace_enabled: bool = True

    @property
    def sender(self) -> Any:
        if self._prank_stack:
            return self._prank_stack[-1]
        return self._sender

    @sender.setter
    def sender(self, addr: Any) -> None:
        self._sender = addr
        self._refresh_gl_message()

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = val
        self._refresh_gl_message()

    @property
    def origin(self) -> Any:
        return self._origin or self._sender

    @origin.setter
    def origin(self, addr: Any) -> None:
        self._origin = addr
        self._refresh_gl_message()

    def warp(self, timestamp: str) -> None:
        """Set block timestamp (ISO format)."""
        self._datetime = timestamp
        self._refresh_gl_message()

    @property
    def check_pickling(self) -> bool:
        """Whether to validate pickling of run_nondet closures."""
        return self._check_pickling

    @check_pickling.setter
    def check_pickling(self, val: bool) -> None:
        self._check_pickling = val

    @property
    def strict_mocks(self) -> bool:
        """Whether to warn about unused mocks on cleanup."""
        return self._strict_mocks

    @strict_mocks.setter
    def strict_mocks(self, val: bool) -> None:
        self._strict_mocks = val

    def deal(self, address: Any, amount: int) -> None:
        """Set balance for an address."""
        addr_bytes = self._to_bytes(address)
        self._balances[addr_bytes] = amount

    def snapshot(self) -> int:
        """Take a snapshot of current state. Returns snapshot ID."""
        snap_id = self._snapshot_counter
        self._snapshot_counter += 1

        self._snapshots[snap_id] = Snapshot(
            id=snap_id,
            storage_data=self._storage.snapshot(),
            balances=dict(self._balances),
            web_mocks=list(self._web_mocks),
            llm_mocks=list(self._llm_mocks),
            prank_stack=list(self._prank_stack),
            captured_validators=list(self._captured_validators),
            sender=self._sender,
            origin=self._origin,
            value=self._value,
            chain_id=self._chain_id,
            datetime=self._datetime,
            live_web_handler=self._live_web_handler,
            live_llm_handler=self._live_llm_handler,
        )

        return snap_id

    def revert(self, snapshot_id: int) -> None:
        """Revert to a previous snapshot."""
        if snapshot_id not in self._snapshots:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        snap = self._snapshots[snapshot_id]
        self._storage.restore(snap.storage_data)
        self._balances = dict(snap.balances)
        self._web_mocks = list(snap.web_mocks)
        self._llm_mocks = list(snap.llm_mocks)
        self._prank_stack = list(snap.prank_stack)
        self._captured_validators = list(snap.captured_validators)
        self._sender = snap.sender
        self._origin = snap.origin
        self._value = snap.value
        self._chain_id = snap.chain_id
        self._datetime = snap.datetime
        self._live_web_handler = snap.live_web_handler
        self._live_llm_handler = snap.live_llm_handler
        self._refresh_gl_message()

        self._snapshots = {
            k: v for k, v in self._snapshots.items()
            if k <= snapshot_id
        }

    def mock_web(
        self,
        url_pattern: str,
        response: MockedWebResponseData,
    ) -> None:
        """Mock web requests matching URL pattern."""
        pattern = re.compile(url_pattern)
        self._web_mocks.append((pattern, response))

    def mock_llm(self, prompt_pattern: str, response: str) -> None:
        """Mock LLM prompts matching pattern."""
        pattern = re.compile(prompt_pattern)
        self._llm_mocks.append((pattern, response))

    def clear_mocks(self) -> None:
        """Clear all registered mocks."""
        self._warn_unused_mocks()
        self._web_mocks.clear()
        self._llm_mocks.clear()
        self._web_mocks_hit.clear()
        self._llm_mocks_hit.clear()

    def run_validator(
        self,
        *,
        leader_result: Any = _sentinel,
        leader_error: Optional[Exception] = None,
        index: int = -1,
    ) -> bool:
        """Run a captured validator function from a prior run_nondet call.

        Each ``gl.vm.run_nondet`` call in a contract appends an entry to
        an internal list. Use *index* to select which one (default -1,
        the most recent).

        Mocks still apply: the validator typically re-runs leader_fn
        internally, which hits the current web/LLM mocks. Swap mocks
        between the contract call and ``run_validator()`` to simulate
        the validator seeing different external data.

        Args:
            leader_result: Override the leader's return value.
            leader_error: Simulate a leader exception (gl.vm.UserError).
            index: Which captured validator to run (-1 = last).

        Returns:
            The bool returned by the validator function.
        """
        if not self._captured_validators:
            raise RuntimeError(
                "No validator captured. Call a contract method that uses "
                "gl.vm.run_nondet before calling run_validator()."
            )

        stored_result, leader_fn, validator_fn = self._captured_validators[index]

        import genlayer.gl.vm as gl_vm

        if leader_error is not None:
            wrapped = gl_vm.UserError(message=str(leader_error))
        elif leader_result is not _sentinel:
            wrapped = gl_vm.Return(calldata=leader_result)
        else:
            wrapped = gl_vm.Return(calldata=stored_result)

        return validator_fn(wrapped)

    def clear_validators(self) -> None:
        """Clear the captured validator list."""
        self._captured_validators.clear()

    @contextmanager
    def expect_revert(self, message: Optional[str] = None):
        """Context manager expecting the next call to revert.

        Catches ContractRollback (gl.rollback) and any Exception raised
        by contract code (ValueError, RuntimeError, etc.). If *message*
        is given, the exception text must contain it.
        """
        from .wasi_mock import ContractRollback

        self._expect_revert = message
        self._expect_revert_any = message is None

        try:
            yield
            raise AssertionError(
                f"Expected revert{f' with message: {message}' if message else ''}, but call succeeded"
            )
        except AssertionError:
            raise
        except ContractRollback as e:
            if message is not None and message not in e.message:
                raise AssertionError(
                    f"Expected revert with message '{message}', got '{e.message}'"
                )
        except Exception as e:
            if message is not None and message not in str(e):
                raise AssertionError(
                    f"Expected revert with message '{message}', got '{e}'"
                )
        finally:
            self._expect_revert = None
            self._expect_revert_any = False

    @contextmanager
    def prank(self, address: Any):
        """Context manager to temporarily change sender."""
        self._prank_stack.append(address)
        self._refresh_gl_message()
        try:
            yield
        finally:
            self._prank_stack.pop()
            self._refresh_gl_message()

    def startPrank(self, address: Any) -> None:
        """Start pranking as address (persists until stopPrank)."""
        self._prank_stack.append(address)
        self._refresh_gl_message()

    def stopPrank(self) -> None:
        """Stop the current prank."""
        if self._prank_stack:
            self._prank_stack.pop()
            self._refresh_gl_message()
        else:
            raise RuntimeError("No active prank to stop")

    @contextmanager
    def activate(self):
        """
        Activate this VM context for contract execution.
        Uses proper cleanup via ExitStack for resource management.

        Patches datetime.datetime so that datetime.now() returns the
        warped time set via vm.warp(). This is dynamic: calling warp()
        mid-test updates _datetime and subsequent now() calls reflect it.
        """
        from . import wasi_mock
        import datetime as _dt_module

        _vm_ref = self
        _OrigDatetime = _dt_module.datetime

        class _WarpedDatetime(_OrigDatetime):
            """datetime subclass that returns vm._datetime from now()."""

            @classmethod
            def now(cls, tz=None):
                ts = _vm_ref._datetime
                warped = _OrigDatetime.fromisoformat(ts.replace('Z', '+00:00'))
                if tz is not None:
                    return warped.astimezone(tz)
                return warped.replace(tzinfo=None)

        with ExitStack() as stack:
            wasi_mock.set_vm(self)
            sys.modules['_genlayer_wasi'] = wasi_mock

            stack.enter_context(
                patch('os.fdopen', wasi_mock.patched_fdopen)
            )
            stack.enter_context(
                patch.object(_dt_module, 'datetime', _WarpedDatetime)
            )
            stack.callback(self._cleanup_after_deactivate)

            try:
                yield self
            finally:
                if '_genlayer_wasi' in sys.modules:
                    del sys.modules['_genlayer_wasi']
                wasi_mock.clear_vm()

    def _cleanup_after_deactivate(self) -> None:
        """Clean up resources after VM deactivation."""
        import os as _os

        self._warn_unused_mocks()

        # Restore original stdin if we replaced it
        stdin_fd = getattr(self, '_original_stdin_fd', None)
        if stdin_fd is not None:
            try:
                _os.dup2(stdin_fd, 0)
                _os.close(stdin_fd)
            except OSError:
                pass
            self._original_stdin_fd = None

        modules_to_remove = [
            key for key in sys.modules.keys()
            if (key == 'genlayer' or key.startswith('genlayer.'))
            or key.startswith('_contract_')
            or key.startswith('_deployed_')
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Remove SDK cache paths from sys.path to avoid stale SDK version conflicts
        sys.path[:] = [
            p for p in sys.path
            if 'gltest-direct' not in p
        ]

    def _match_web_mock(self, url: str, method: str = "GET") -> Optional[MockedWebResponseData]:
        for i, (pattern, response) in enumerate(self._web_mocks):
            if pattern.search(url):
                if response.get("method", "GET") == method:
                    self._web_mocks_hit.add(i)
                    return response
        return None

    def _match_llm_mock(self, prompt: str) -> Optional[str]:
        for i, (pattern, response) in enumerate(self._llm_mocks):
            if pattern.search(prompt):
                self._llm_mocks_hit.add(i)
                return response
        return None

    def _warn_unused_mocks(self) -> None:
        """Warn about mocks that were never matched (strict_mocks mode)."""
        if not self._strict_mocks:
            return
        import warnings
        for i, (pattern, _) in enumerate(self._web_mocks):
            if i not in self._web_mocks_hit:
                warnings.warn(
                    f"Web mock never matched: {pattern.pattern}",
                    RuntimeWarning,
                    stacklevel=3,
                )
        for i, (pattern, _) in enumerate(self._llm_mocks):
            if i not in self._llm_mocks_hit:
                warnings.warn(
                    f"LLM mock never matched: {pattern.pattern}",
                    RuntimeWarning,
                    stacklevel=3,
                )

    def _trace(self, message: str) -> None:
        if self._trace_enabled:
            self._traces.append(message)

    def _to_bytes(self, addr: Any) -> bytes:
        if isinstance(addr, bytes):
            return addr
        if hasattr(addr, 'as_bytes'):
            return addr.as_bytes
        if hasattr(addr, '__bytes__'):
            return bytes(addr)
        if isinstance(addr, str):
            if addr.startswith("0x"):
                return bytes.fromhex(addr[2:])
            return bytes.fromhex(addr)
        raise ValueError(f"Cannot convert {type(addr)} to bytes")

    def _refresh_gl_message(self) -> None:
        """
        Refresh gl.message and gl.message_raw to reflect current sender.

        GenLayer SDK caches gl.message at import time. This method updates
        the cached values so contracts see the current vm.sender.

        Only updates if genlayer.gl is already imported - we must not trigger
        a fresh import as that would read from stdin before message is injected.
        """
        # Only proceed if genlayer.gl is already loaded
        if 'genlayer.gl' not in sys.modules:
            return

        try:
            gl = sys.modules['genlayer.gl']
            from genlayer.py.types import Address, u256

            # Convert sender to Address if needed
            sender = self.sender
            if sender is not None and not isinstance(sender, Address):
                if isinstance(sender, bytes):
                    sender = Address(sender)
                elif hasattr(sender, 'as_bytes'):
                    sender = Address(sender.as_bytes)

            origin = self.origin
            if origin is not None and not isinstance(origin, Address):
                if isinstance(origin, bytes):
                    origin = Address(origin)
                elif hasattr(origin, 'as_bytes'):
                    origin = Address(origin.as_bytes)

            # Update message_raw dict (mutable)
            if hasattr(gl, 'message_raw') and gl.message_raw is not None:
                gl.message_raw['sender_address'] = sender
                gl.message_raw['origin_address'] = origin

            # Replace gl.message with new NamedTuple (immutable, must recreate)
            if hasattr(gl, 'message') and gl.message is not None:
                gl.message = gl.MessageType(
                    contract_address=gl.message.contract_address,
                    sender_address=sender,
                    origin_address=origin,
                    value=u256(self._value),
                    chain_id=u256(self._chain_id),
                )
        except ImportError:
            # genlayer not loaded yet, nothing to update
            pass

    def get_message_raw(self) -> Dict[str, Any]:
        """Get MessageRawType dict for stdin injection."""
        return {
            "contract_address": self._contract_address,
            "sender_address": self.sender,
            "origin_address": self.origin,
            "stack": [],
            "value": self._value,
            "datetime": self._datetime,
            "is_init": False,
            "chain_id": self._chain_id,
            "entry_kind": 0,
            "entry_data": b"",
            "entry_stage_data": None,
        }
