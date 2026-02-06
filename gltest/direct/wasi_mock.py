"""
Mock implementation of _genlayer_wasi module.

Provides drop-in replacements for WASI functions that contracts use:
- storage_read / storage_write
- get_balance / get_self_balance
- gl_call

This module is injected into sys.modules before importing contracts.
"""

from __future__ import annotations

import io
import os
import threading
import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .vm import VMContext

# Thread-local VM context for parallel test safety
_local = threading.local()

# Original os.fdopen reference (saved once at module load)
_original_fdopen = os.fdopen


def set_vm(vm: "VMContext") -> None:
    """Set the active VM context for WASI operations."""
    _local.vm = vm
    _local.fd_counter = 100
    _local.fd_buffers = {}


def get_vm() -> "VMContext":
    """Get the active VM context."""
    vm = getattr(_local, 'vm', None)
    if vm is None:
        raise RuntimeError("No VM context active. Call VMContext.activate() first.")
    return vm


def clear_vm() -> None:
    """Clear the VM context and clean up resources."""
    if hasattr(_local, 'fd_buffers'):
        for buf in _local.fd_buffers.values():
            buf.close()
        _local.fd_buffers.clear()
    _local.vm = None
    _local.fd_counter = 100


def storage_read(slot: bytes, off: int, buf: bytearray, /) -> None:
    """Read from storage slot into buffer."""
    vm = get_vm()
    data = vm._storage.do_read(slot, off, len(buf))
    buf[:] = data


def storage_write(slot: bytes, off: int, what: bytes, /) -> None:
    """Write to storage slot."""
    vm = get_vm()
    vm._storage.do_write(slot, off, what)


def get_balance(address: bytes, /) -> int:
    """Get balance of an address."""
    vm = get_vm()
    return vm._balances.get(address, 0)


def get_self_balance() -> int:
    """Get balance of current contract."""
    vm = get_vm()
    contract_addr = vm._contract_address
    if contract_addr is None:
        return 0
    addr_bytes = bytes(contract_addr) if hasattr(contract_addr, '__bytes__') else contract_addr
    return vm._balances.get(addr_bytes, 0)


def gl_call(data: bytes, /) -> int:
    """
    Execute a GenVM call operation.

    Returns file descriptor for reading response, or 2^32-1 on failure.
    """
    vm = get_vm()
    fd_buffers = getattr(_local, 'fd_buffers', {})

    try:
        from genlayer.py import calldata
        request = calldata.decode(data)
    except Exception as e:
        vm._trace(f"gl_call decode error: {e}")
        return 2**32 - 1

    response = _handle_gl_call(vm, request)

    if response is None:
        return 2**32 - 1

    # If response is already bytes (from RunNondet), use directly
    # RunNondet handles its own ResultCode prefix for sub-VM result format
    if isinstance(response, bytes):
        encoded = response
    else:
        # Regular responses (web, llm, etc) are just calldata-encoded
        # The SDK's _decode_nondet expects plain {"ok": ...} format
        try:
            from genlayer.py import calldata
            encoded = calldata.encode(response)
        except Exception as e:
            vm._trace(f"gl_call encode error: {e}")
            return 2**32 - 1

    fd_counter = getattr(_local, 'fd_counter', 100)
    fd = fd_counter
    _local.fd_counter = fd_counter + 1

    buf = io.BytesIO(encoded)
    fd_buffers[fd] = buf
    _local.fd_buffers = fd_buffers

    return fd


def _handle_gl_call(vm: "VMContext", request: Any) -> Any:
    """Handle a gl_call request and return the response."""
    if not isinstance(request, dict):
        return None

    if "Return" in request:
        vm._return_value = request["Return"]
        vm._returned = True
        return None

    if "Rollback" in request:
        raise ContractRollback(request["Rollback"])

    if "Trace" in request:
        trace_data = request["Trace"]
        if "Message" in trace_data:
            vm._trace(trace_data["Message"])
        return {"ok": None}

    if "Sandbox" in request:
        warnings.warn(
            "gl.sandbox is not fully isolated in direct test mode.",
            RuntimeWarning,
            stacklevel=3,
        )
        return {"ok": None}

    if "RunNondet" in request:
        return _handle_run_nondet(vm, request["RunNondet"])

    if "GetWebsite" in request or "WebRequest" in request:
        web_data = request.get("GetWebsite") or request.get("WebRequest", {})
        return _handle_web_request(vm, web_data)

    if "ExecPrompt" in request:
        prompt_data = request["ExecPrompt"]
        return _handle_llm_request(vm, prompt_data)

    vm._trace(f"Unknown gl_call request type: {list(request.keys())}")
    return None


def _handle_web_request(vm: "VMContext", data: Any) -> Any:
    """Handle web request using mocks.

    Accepts two mock formats:
    1. Full: {"method": "GET", "response": {"status": 200, "headers": {}, "body": b"..."}}
    2. Flat: {"method": "GET", "status": 200, "body": "..."}  (auto-adapted)
    """
    url = data.get("url", "")
    method = data.get("method", "GET")

    mock_data = vm._match_web_mock(url, method)
    if mock_data:
        # Full format: already has "response" wrapper
        if "response" in mock_data:
            return {"ok": {"response": mock_data["response"]}}
        # Flat format: auto-adapt {status, body} → SDK response format
        body = mock_data.get("body", "")
        if isinstance(body, str):
            body = body.encode("utf-8")
        return {"ok": {"response": {
            "status": mock_data.get("status", 200),
            "headers": {},
            "body": body,
        }}}

    raise MockNotFoundError(f"No web mock for {method} {url}")


def _handle_llm_request(vm: "VMContext", data: Any) -> Any:
    """Handle LLM prompt request using mocks.

    Auto-parses JSON strings so exec_prompt(response_format='json') gets a dict.
    """
    import json as _json

    prompt = data.get("prompt", "")

    response = vm._match_llm_mock(prompt)
    if response is not None:
        # Auto-parse JSON strings (exec_prompt with response_format='json' expects dict)
        if isinstance(response, str):
            try:
                response = _json.loads(response)
            except (ValueError, TypeError):
                pass
        return {"ok": response}

    raise MockNotFoundError(f"No LLM mock for prompt: {prompt[:100]}...")


def _handle_run_nondet(vm: "VMContext", data: Any) -> Any:
    """Handle RunNondet request by executing the leader function directly.

    In direct mode, we skip the leader/validator consensus and just run
    the leader function, returning its result.
    """
    import cloudpickle
    from genlayer.py import calldata

    data_leader = data.get("data_leader")
    if not data_leader:
        raise ValueError("RunNondet missing data_leader")

    # Unpickle and execute the leader function
    # The lambda expects a stage_data argument, but in leader mode it's None
    leader_fn = cloudpickle.loads(data_leader)

    try:
        result = leader_fn(None)
        # Wrap result in Return format (code 0 + calldata)
        encoded = bytes([0]) + calldata.encode(result)
        return encoded
    except Exception as e:
        # Wrap error in UserError format (code 1 + message)
        error_msg = str(e)
        return bytes([1]) + error_msg.encode('utf-8')


def patched_fdopen(fd_arg: int, mode: str = "r", *args, **kwargs):
    """Patched os.fdopen that intercepts mock file descriptors."""
    fd_buffers = getattr(_local, 'fd_buffers', {})

    if fd_arg in fd_buffers:
        buf = fd_buffers.pop(fd_arg)
        buf.seek(0)
        return buf

    return _original_fdopen(fd_arg, mode, *args, **kwargs)


class ContractRollback(Exception):
    """Raised when a contract calls gl.rollback()."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class MockNotFoundError(Exception):
    """Raised when no mock is found for a nondet operation."""
    pass


__all__ = (
    "storage_read",
    "storage_write",
    "get_balance",
    "get_self_balance",
    "gl_call",
)
