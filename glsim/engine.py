"""Contract execution engine for glsim.

Wraps gltest.direct to provide persistent contract deployment and execution.
Unlike test mode, the VM context persists across requests and web/LLM calls
can be routed to real services.
"""

from __future__ import annotations

import builtins
import copy
import hashlib
import inspect
import io
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from gltest.direct.vm import VMContext, InmemManager
from gltest.direct.loader import deploy_contract, create_address, _allocate_contract

from .state import StateStore
from .tx_decoder import decode_calldata_bytes, encode_calldata_result
from .genvm_stubs import install_genvm_stubs, uninstall_genvm_stubs

_real_open = builtins.open


class SimEngine:
    """Persistent contract execution engine."""

    def __init__(
        self,
        state: StateStore,
        web_handler: Optional[Callable] = None,
        llm_handler: Optional[Callable] = None,
    ):
        self.state = state
        self.vm = VMContext()
        self.vm.sender = create_address("default_deployer")
        self._activated = False
        self._activation_ctx = None
        self._web_handler = web_handler
        self._llm_handler = llm_handler
        # Map contract address -> instance
        self._instances: Dict[str, Any] = {}
        # Map contract address -> class (for schema extraction)
        self._classes: Dict[str, type] = {}
        # Cache: resolved path -> contract class (avoid SDK re-import errors)
        self._class_cache: Dict[str, type] = {}
        # Cache: code content hash -> contract class (matches deploy ↔ schema)
        self._code_hash_cache: Dict[str, type] = {}
        # Per-contract isolated storage
        self._storages: Dict[str, InmemManager] = {}
        # PostMessage queue (fire-and-forget calls executed after current call)
        self._post_queue: List[Dict] = []
        self._call_depth: int = 0
        self._draining: bool = False
        # Cross-contract activity captured during a top-level call.
        # Used to expose Studio-like triggered transaction graphs.
        self._captured_triggered_ops: List[Dict[str, Any]] = []
        # Virtual filesystem: /contract/ → extracted temp dir (for ZIP packages)
        self._vfs_contract_dir: Optional[str] = None
        # Snapshots
        self._snapshots: Dict[int, Dict] = {}
        self._snapshot_counter: int = 0

    def activate(self) -> None:
        """Activate the VM context (call once at startup)."""
        if self._activated:
            return
        self._activation_ctx = self.vm.activate()
        self._activation_ctx.__enter__()
        self._activated = True
        install_genvm_stubs()
        self.install_cross_contract_hook()
        self._install_vfs_open_patch()

    def deactivate(self) -> None:
        """Deactivate the VM context (call at shutdown)."""
        if not self._activated:
            return
        self._activation_ctx.__exit__(None, None, None)
        self._activated = False
        self._activation_ctx = None
        builtins.open = _real_open

    def create_snapshot(self) -> int:
        """Snapshot engine + state store. Returns snapshot ID."""
        self._snapshot_counter += 1
        sid = self._snapshot_counter
        self._snapshots[sid] = {
            "state_accounts": copy.deepcopy(self.state.accounts),
            "state_contracts": {k: v.address for k, v in self.state.contracts.items()},
            "state_transactions": dict(self.state.transactions),
            "state_block_number": self.state.block_number,
            "state_next_gl_tx_id": self.state._next_gl_tx_id,
            "state_gl_to_hash": dict(self.state._gl_to_hash),
            "state_eth_hash_to_hash": dict(self.state._eth_hash_to_hash),
            "instances_keys": set(self._instances.keys()),
            "storages_keys": set(self._storages.keys()),
            "classes_keys": set(self._classes.keys()),
        }
        return sid

    def restore_snapshot(self, snapshot_id: int) -> bool:
        """Restore engine + state to a previous snapshot."""
        snap = self._snapshots.get(snapshot_id)
        if snap is None:
            return False

        self.state.accounts = copy.deepcopy(snap["state_accounts"])
        self.state.block_number = snap["state_block_number"]
        self.state._next_gl_tx_id = snap["state_next_gl_tx_id"]
        self.state._gl_to_hash = dict(snap["state_gl_to_hash"])
        self.state._eth_hash_to_hash = dict(snap["state_eth_hash_to_hash"])
        self.state.transactions = dict(snap["state_transactions"])

        # Remove contracts/instances added after snapshot
        for key in list(self._instances.keys()):
            if key not in snap["instances_keys"]:
                del self._instances[key]
        for key in list(self._storages.keys()):
            if key not in snap["storages_keys"]:
                del self._storages[key]
        for key in list(self._classes.keys()):
            if key not in snap["classes_keys"]:
                del self._classes[key]
        for key in list(self.state.contracts.keys()):
            if key not in snap["state_contracts"]:
                del self.state.contracts[key]

        return True

    def deploy(
        self,
        code_path: str,
        args: list | None = None,
        kwargs: dict | None = None,
        sender: Optional[str] = None,
    ) -> Tuple[str, Any]:
        """Deploy a contract, return (address, instance)."""
        args = args or []
        kwargs = kwargs or {}

        path = Path(code_path).resolve()
        if not path.exists():
            for base in [Path.cwd(), Path.cwd() / "contracts"]:
                candidate = base / code_path
                if candidate.exists():
                    path = candidate.resolve()
                    break

        if not path.exists():
            raise FileNotFoundError(f"Contract not found: {code_path}")

        # Generate contract address
        deployer = sender or "0x" + self.vm._to_bytes(self.vm.sender).hex()
        nonce = self.state.get_nonce(deployer)
        contract_addr = self.state.generate_contract_address(deployer, nonce)
        self.state.increment_nonce(deployer)

        addr_key = contract_addr.lower()
        addr_bytes = bytes.fromhex(contract_addr[2:])
        self.vm._contract_address = addr_bytes

        if sender:
            self.vm.sender = bytes.fromhex(sender[2:]) if sender.startswith("0x") else sender

        self._install_live_handlers()

        # Give this contract its own storage
        storage = InmemManager()
        self._storages[addr_key] = storage
        self.vm._storage = storage

        # Set gl.message so __init__ can read contract_address if needed
        self._set_message_context(
            contract_address=addr_bytes,
            sender=self.vm.sender,
        )

        # Deploy: reuse cached class for same file to avoid SDK re-import errors
        path_key = str(path)
        cached_cls = self._class_cache.get(path_key)
        if cached_cls is not None:
            instance = _allocate_contract(cached_cls, self.vm, *args, **kwargs)
        else:
            self._reset_contract_registry()
            instance = deploy_contract(path, self.vm, *args, sdk_version=None, **kwargs)

        self._instances[addr_key] = instance

        # Extract and cache the contract class
        contract_cls = type(instance)
        for cls in type(instance).__mro__:
            if hasattr(cls, '__annotations__') and cls.__module__.startswith("_contract_"):
                contract_cls = cls
                break
        self._classes[addr_key] = contract_cls
        self._class_cache[path_key] = contract_cls
        # Also cache by content hash for gen_getContractSchemaForCode
        try:
            code_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
            self._code_hash_cache[code_hash] = contract_cls
        except OSError:
            pass

        # Register in state
        schema = self._extract_schema(contract_cls)
        self.state.register_contract(contract_addr, str(path), instance, schema)

        return contract_addr, instance

    def call_method(
        self,
        contract_address: str,
        method_name: str,
        args: list | None = None,
        kwargs: dict | None = None,
        sender: Optional[str] = None,
    ) -> Any:
        """Call a method on a deployed contract."""
        args = args or []
        kwargs = kwargs or {}
        addr = contract_address.lower()

        instance = self._instances.get(addr)
        if instance is None:
            raise ValueError(f"No contract deployed at {contract_address}")

        if sender:
            self.vm.sender = bytes.fromhex(sender[2:]) if sender.startswith("0x") else sender

        self._install_live_handlers()

        # Swap to this contract's storage and address
        addr_bytes = bytes.fromhex(addr[2:])
        self.vm._contract_address = addr_bytes
        storage = self._storages.get(addr)
        if storage is not None:
            self.vm._storage = storage

        # Update gl.message so contract code can read contract_address/sender
        self._set_message_context(
            contract_address=addr_bytes,
            sender=self.vm.sender,
        )

        method = getattr(instance, method_name, None)
        if method is None:
            raise AttributeError(f"Contract has no method '{method_name}'")

        self._call_depth += 1
        try:
            result = method(*args, **kwargs)
        finally:
            self._call_depth -= 1

        # Drain exactly one queued PostMessage at the top level only.
        # The _draining flag prevents the drained call from draining further,
        # matching real GenLayer where PostMessage is async (next block).
        if self._call_depth == 0 and not self._draining and self._post_queue:
            msg = self._post_queue.pop(0)
            self._post_queue.clear()
            self._draining = True
            try:
                self.call_method(
                    msg['address'], msg['method'],
                    msg.get('args', []), msg.get('kwargs', {}),
                    sender=msg.get('sender'),
                )
            except Exception as e:
                self.vm._trace(f"PostMessage error: {e}")
            finally:
                self._draining = False

        return result

    def get_schema(self, contract_address: str) -> Optional[Dict]:
        """Get the ABI/schema for a deployed contract."""
        contract = self.state.get_contract(contract_address)
        if contract and contract.schema:
            return contract.schema

        cls = self._classes.get(contract_address.lower())
        if cls:
            return self._extract_schema(cls)

        return None

    def _extract_schema(self, cls: type) -> Dict:
        """Extract a JSON schema from a contract class."""
        methods = []
        for name in dir(cls):
            if name.startswith("_"):
                continue
            obj = getattr(cls, name, None)
            if obj is None or not callable(obj):
                continue

            sig = None
            try:
                sig = inspect.signature(obj)
            except (ValueError, TypeError):
                continue

            params = []
            for pname, param in sig.parameters.items():
                if pname == "self":
                    continue
                ptype = "any"
                if param.annotation != inspect.Parameter.empty:
                    ptype = getattr(param.annotation, "__name__", str(param.annotation))
                params.append({"name": pname, "type": ptype})

            ret_type = "any"
            if sig.return_annotation != inspect.Signature.empty:
                ret_type = getattr(sig.return_annotation, "__name__", str(sig.return_annotation))

            methods.append({
                "name": name,
                "params": params,
                "return_type": ret_type,
            })

        return {"class_name": cls.__name__, "methods": methods}

    def deploy_from_code(
        self,
        code_bytes: bytes,
        calldata_bytes: bytes,
        sender: Optional[str] = None,
    ) -> Tuple[str, Any]:
        """Deploy a contract from raw Python source bytes (as sent by SDK).

        Handles both single-file (.py) and multi-file (ZIP package) contracts.
        Uses content-hash-based filenames so the same contract code always
        maps to the same path (enabling class cache hits and avoiding the
        SDK's single-contract-per-module restriction).
        """
        code_hash = hashlib.sha256(code_bytes).hexdigest()[:16]
        tmp_path = self._unpack_contract_code(code_bytes, code_hash)

        # Decode constructor calldata
        args = []
        kwargs = {}
        if calldata_bytes:
            cd = decode_calldata_bytes(calldata_bytes)
            args = cd.get("args", [])
            kwargs = cd.get("kwargs", {})

        addr, instance = self.deploy(tmp_path, args, kwargs, sender)
        # Cache by content hash too (so gen_getContractSchemaForCode hits cache)
        cls = self._classes.get(addr.lower())
        if cls is not None:
            self._code_hash_cache[code_hash] = cls
        return addr, instance

    def _unpack_contract_code(self, code_bytes: bytes, code_hash: str) -> str:
        """Write contract code to temp path. Unpacks ZIP packages to directory."""
        if code_bytes[:2] == b'PK':
            # ZIP package — extract to temp dir
            extract_dir = Path(tempfile.gettempdir()) / f"glsim_pkg_{code_hash}"
            if not extract_dir.exists():
                extract_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(io.BytesIO(code_bytes)) as zf:
                    zf.extractall(extract_dir)
            # Set VFS mapping so /contract/* reads redirect here
            contract_dir = extract_dir / "contract"
            if contract_dir.is_dir():
                self._vfs_contract_dir = str(contract_dir)
            # Entry point: contract/__init__.py (standard gltest ZIP layout)
            entry = contract_dir / "__init__.py"
            if not entry.exists():
                # Fallback: look for any __init__.py
                for p in extract_dir.rglob("__init__.py"):
                    entry = p
                    break
            return str(entry)
        else:
            # Single .py file
            tmp_path = str(Path(tempfile.gettempdir()) / f"glsim_contract_{code_hash}.py")
            Path(tmp_path).write_bytes(code_bytes)
            return tmp_path

    def _install_vfs_open_patch(self) -> None:
        """Patch builtins.open to redirect /contract/ reads to extracted temp dir."""
        engine = self

        def patched_open(filename, *args, **kwargs):
            fname = str(filename)
            vfs_dir = engine._vfs_contract_dir
            if vfs_dir and fname.startswith("/contract/"):
                redirected = fname.replace("/contract/", vfs_dir + "/", 1)
                return _real_open(redirected, *args, **kwargs)
            return _real_open(filename, *args, **kwargs)

        builtins.open = patched_open

    def call_from_calldata(
        self,
        contract_address: str,
        calldata_bytes: bytes,
        sender: Optional[str] = None,
    ) -> Tuple[Any, bytes]:
        """Call a contract method using raw calldata bytes.

        Returns (result, result_encoded_bytes).
        """
        cd = decode_calldata_bytes(calldata_bytes)
        method = cd.get("method")
        args = cd.get("args", [])
        kwargs = cd.get("kwargs", {})

        if not method:
            raise ValueError("No method in calldata")

        result = self.call_method(contract_address, method, args, kwargs, sender)
        result_bytes = encode_calldata_result(result)
        return result, result_bytes

    def reset_triggered_ops(self) -> None:
        """Clear captured cross-contract ops for a new top-level transaction."""
        self._captured_triggered_ops.clear()

    def get_triggered_ops(self) -> List[Dict[str, Any]]:
        """Return a copy of captured cross-contract ops from the latest call."""
        return list(self._captured_triggered_ops)

    def get_sdk_schema(self, contract_address: str) -> Optional[Dict]:
        """Get schema in SDK-compatible ContractSchema format."""
        cls = self._classes.get(contract_address.lower())
        if cls is None:
            return None
        return self._extract_sdk_schema(cls)

    def get_sdk_schema_for_code(self, code: bytes) -> Dict:
        """Extract schema from source code without deploying."""
        code_hash = hashlib.sha256(code).hexdigest()[:16]

        # Check code-hash cache first (populated by deploy_from_code)
        cached_cls = self._code_hash_cache.get(code_hash)
        if cached_cls is not None:
            return self._extract_sdk_schema(cached_cls)

        # Check path-based cache
        tmp_path = str(Path(tempfile.gettempdir()) / f"glsim_contract_{code_hash}.py")
        Path(tmp_path).write_bytes(code)
        path = Path(tmp_path).resolve()
        path_key = str(path)

        cached_cls = self._class_cache.get(path_key)
        if cached_cls is not None:
            return self._extract_sdk_schema(cached_cls)

        # Load the class without deploying
        from gltest.direct.loader import load_contract_class
        self._reset_contract_registry()
        vm = VMContext()
        with vm.activate():
            cls = load_contract_class(path, vm, sdk_version=None)
        self._class_cache[path_key] = cls
        self._code_hash_cache[code_hash] = cls
        return self._extract_sdk_schema(cls)

    def _extract_sdk_schema(self, cls: type) -> Dict:
        """Extract schema in SDK ContractSchema format.

        Format: {
            "ctor": {"params": [...], "kwparams": {}},
            "methods": {"name": {"params": [...], "kwparams": {}, "ret": str, "readonly": bool}}
        }
        """
        ctor_params = []
        ctor_kwparams = {}
        methods = {}

        # Find __init__ for constructor params
        init = getattr(cls, "__init__", None)
        if init:
            try:
                sig = inspect.signature(init)
                for pname, param in sig.parameters.items():
                    if pname == "self":
                        continue
                    ptype = "any"
                    if param.annotation != inspect.Parameter.empty:
                        ptype = getattr(param.annotation, "__name__", str(param.annotation))
                    if param.default != inspect.Parameter.empty:
                        ctor_kwparams[pname] = ptype
                    else:
                        ctor_params.append(ptype)
            except (ValueError, TypeError):
                pass

        # Extract public methods (marked with @gl.public.write or @gl.public.view)
        for name in dir(cls):
            if name.startswith("_"):
                continue
            obj = getattr(cls, name, None)
            if obj is None or not callable(obj):
                continue

            # Only include methods marked as public by the SDK
            if not getattr(obj, "__gl_public__", False):
                continue

            try:
                sig = inspect.signature(obj)
            except (ValueError, TypeError):
                continue

            params = []
            kwparams = {}
            for pname, param in sig.parameters.items():
                if pname == "self":
                    continue
                ptype = "any"
                if param.annotation != inspect.Parameter.empty:
                    ptype = getattr(param.annotation, "__name__", str(param.annotation))
                if param.default != inspect.Parameter.empty:
                    kwparams[pname] = ptype
                else:
                    params.append(ptype)

            ret_type = "any"
            if sig.return_annotation != inspect.Signature.empty:
                ret_type = getattr(sig.return_annotation, "__name__", str(sig.return_annotation))

            readonly = getattr(obj, "__gl_readonly__", False)

            methods[name] = {
                "params": params,
                "kwparams": kwparams,
                "ret": ret_type,
                "readonly": readonly,
            }

        return {
            "ctor": {"params": ctor_params, "kwparams": ctor_kwparams},
            "methods": methods,
        }

    @staticmethod
    def _reset_contract_registry() -> None:
        """Reset the genlayer SDK's global contract class registry.

        The SDK only allows one Contract subclass. Different SDK versions
        use different variable names (``__known_contact__`` vs
        ``__known_contract__``). We clear whichever exists.
        """
        mod = sys.modules.get("genlayer.gl.genvm_contracts")
        if mod is None:
            return
        for attr in ("__known_contact__", "__known_contract__"):
            if hasattr(mod, attr):
                setattr(mod, attr, None)

    def _install_live_handlers(self) -> None:
        """Install live web/LLM handlers on the VM context."""
        if self._web_handler:
            self.vm._live_web_handler = self._web_handler
        if self._llm_handler:
            self.vm._live_llm_handler = self._llm_handler

    def install_cross_contract_hook(self) -> None:
        """Install gl_call hook for cross-contract calls (DeployContract, CallContract, PostMessage)."""
        engine = self

        def hook(vm, request):
            if "DeployContract" in request:
                return engine._handle_deploy_in_contract(vm, request["DeployContract"])
            if "CallContract" in request:
                return engine._handle_call_in_contract(vm, request["CallContract"])
            if "PostMessage" in request:
                return engine._handle_post_in_contract(vm, request["PostMessage"])
            return None

        self.vm._gl_call_hook = hook

    def _handle_deploy_in_contract(self, vm: Any, data: Dict) -> bytes:
        """Handle gl.deploy_contract() from within a running contract."""
        from genlayer.py import calldata
        from genlayer.py.types import Address

        code = data.get('code', b'')
        calldata_obj = data.get('calldata', {})
        args = calldata_obj.get('args', [])
        kwargs = calldata_obj.get('kwargs', {})

        # Write code to temp file (handles ZIP packages too)
        code_hash = hashlib.sha256(code).hexdigest()[:16]
        tmp_path = self._unpack_contract_code(code, code_hash)

        # Generate address for child contract
        deployer = "0x" + vm._contract_address.hex() if isinstance(vm._contract_address, bytes) else str(vm._contract_address)
        nonce = self.state.get_nonce(deployer)
        child_addr = self.state.generate_contract_address(deployer, nonce)
        self.state.increment_nonce(deployer)

        addr_key = child_addr.lower()
        child_addr_bytes = bytes.fromhex(child_addr[2:])

        # Save parent context
        parent_storage = vm._storage
        parent_contract_address = vm._contract_address

        # Set up child storage
        child_storage = InmemManager()
        self._storages[addr_key] = child_storage
        vm._storage = child_storage
        vm._contract_address = child_addr_bytes

        try:
            # Deploy child contract
            path = Path(tmp_path).resolve()
            path_key = str(path)
            cached_cls = self._class_cache.get(path_key)

            if cached_cls is not None:
                instance = _allocate_contract(cached_cls, vm, *args, **kwargs)
            else:
                self._reset_contract_registry()
                instance = deploy_contract(path, vm, *args, sdk_version=None, **kwargs)

            self._instances[addr_key] = instance

            # Cache the class
            contract_cls = type(instance)
            for cls in type(instance).__mro__:
                if hasattr(cls, '__annotations__') and cls.__module__.startswith("_contract_"):
                    contract_cls = cls
                    break
            self._classes[addr_key] = contract_cls
            self._class_cache[path_key] = contract_cls
            self._code_hash_cache[code_hash] = contract_cls

            # Register in state
            schema = self._extract_schema(contract_cls)
            self.state.register_contract(child_addr, str(path), instance, schema)
            self._captured_triggered_ops.append({
                "type": "deploy",
                "address": child_addr,
            })

        finally:
            # Restore parent context
            vm._storage = parent_storage
            vm._contract_address = parent_contract_address
            # Restore parent as the "known" contract class
            self._reset_contract_registry()

        return calldata.encode({'ok': None})

    def _handle_call_in_contract(self, vm: Any, data: Dict) -> bytes:
        """Handle gl.contract_at().view().method() from within a running contract."""
        from genlayer.py import calldata
        from genlayer.py.types import Address

        address = data.get('address')
        calldata_obj = data.get('calldata', {})
        method_name = calldata_obj.get('method')
        args = calldata_obj.get('args', [])
        kwargs = calldata_obj.get('kwargs', {})

        # Normalize address
        if isinstance(address, Address):
            addr_key = "0x" + address.as_bytes.hex()
        elif isinstance(address, bytes):
            addr_key = "0x" + address.hex()
        else:
            addr_key = str(address)
        addr_key = addr_key.lower()

        instance = self._instances.get(addr_key)
        if instance is None:
            error_msg = f"Contract not found at {addr_key}"
            return bytes([1]) + error_msg.encode('utf-8')

        # Save parent context
        parent_storage = vm._storage
        parent_contract_address = vm._contract_address

        # Swap to target contract context
        target_storage = self._storages.get(addr_key)
        if target_storage is not None:
            vm._storage = target_storage
        vm._contract_address = bytes.fromhex(addr_key[2:])

        # Swap gl.message context
        saved_message = self._swap_message_context(
            vm,
            sender=parent_contract_address,
            contract_address=bytes.fromhex(addr_key[2:]),
        )

        try:
            method = getattr(instance, method_name)
            result = method(*args, **kwargs)
            encoded = calldata.encode(result)
            return bytes([0]) + encoded  # ResultCode.RETURN = success
        except Exception as e:
            error_msg = str(e)
            return bytes([1]) + error_msg.encode('utf-8')
        finally:
            vm._storage = parent_storage
            vm._contract_address = parent_contract_address
            self._restore_message_context(saved_message)

    def _handle_post_in_contract(self, vm: Any, data: Dict) -> Dict:
        """Handle gl.contract_at().emit().method() — enqueue for after current call."""
        from genlayer.py.types import Address

        address = data.get('address')
        calldata_obj = data.get('calldata', {})
        method_name = calldata_obj.get('method')
        args = calldata_obj.get('args', [])
        kwargs = calldata_obj.get('kwargs', {})

        if isinstance(address, Address):
            addr_key = "0x" + address.as_bytes.hex()
        elif isinstance(address, bytes):
            addr_key = "0x" + address.hex()
        else:
            addr_key = str(address).lower()

        if method_name and self._instances.get(addr_key) is not None:
            sender = vm._contract_address
            self._post_queue.append({
                'address': addr_key,
                'method': method_name,
                'args': args,
                'kwargs': kwargs,
                'sender': "0x" + sender.hex() if isinstance(sender, bytes) else str(sender),
            })
            self._captured_triggered_ops.append({
                "type": "post",
                "address": addr_key,
                "method": method_name,
            })

        return {'ok': None}

    @staticmethod
    def _swap_message_context(vm: Any, sender: Any, contract_address: Any) -> Optional[Dict]:
        """Swap gl.message for cross-contract calls. Returns saved state."""
        if 'genlayer.gl' not in sys.modules:
            return None
        try:
            gl = sys.modules['genlayer.gl']
            from genlayer.py.types import Address

            if isinstance(sender, bytes):
                sender = Address(sender)
            if isinstance(contract_address, bytes):
                contract_address = Address(contract_address)

            saved = {}
            if hasattr(gl, 'message') and gl.message is not None:
                saved['message'] = gl.message
                gl.message = gl.MessageType(
                    contract_address=contract_address,
                    sender_address=sender,
                    origin_address=gl.message.origin_address,
                    value=gl.message.value,
                    chain_id=gl.message.chain_id,
                )
            return saved
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def _set_message_context(contract_address: Any, sender: Any) -> None:
        """Set gl.message for top-level calls (call_method / deploy)."""
        if 'genlayer.gl' not in sys.modules:
            return
        try:
            gl = sys.modules['genlayer.gl']
            from genlayer.py.types import Address

            if isinstance(contract_address, bytes):
                contract_address = Address(contract_address)
            if isinstance(sender, bytes):
                sender = Address(sender)

            if hasattr(gl, 'message') and gl.message is not None:
                gl.message = gl.MessageType(
                    contract_address=contract_address,
                    sender_address=sender,
                    origin_address=gl.message.origin_address,
                    value=gl.message.value,
                    chain_id=gl.message.chain_id,
                )
        except (ImportError, AttributeError):
            pass

    @staticmethod
    def _restore_message_context(saved: Optional[Dict]) -> None:
        """Restore gl.message after cross-contract call."""
        if saved is None:
            return
        gl = sys.modules.get('genlayer.gl')
        if gl is None:
            return
        if 'message' in saved:
            gl.message = saved['message']
