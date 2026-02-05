"""
Contract loader for direct test runner.

Handles:
- SDK version setup based on contract headers
- Message context injection via stdin
- WASI mock installation
- Contract class discovery and instantiation
"""

from __future__ import annotations

import sys
import hashlib
import importlib.util
from pathlib import Path
from typing import Any, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .vm import VMContext


def load_contract_class(
    contract_path: Path,
    vm: "VMContext",
    sdk_version: Optional[str] = None,
) -> Type[Any]:
    """
    Load a contract class from file.

    Sets up SDK paths, WASI mock, and message context.
    """
    contract_path = Path(contract_path).resolve()

    if not contract_path.exists():
        raise FileNotFoundError(f"Contract not found: {contract_path}")

    # 1. Setup WASI mock FIRST (before genlayer is imported)
    from . import wasi_mock
    wasi_mock.set_vm(vm)
    sys.modules['_genlayer_wasi'] = wasi_mock

    # 2. Setup SDK paths (this adds genlayer to sys.path)
    from .sdk_loader import setup_sdk_paths
    setup_sdk_paths(contract_path, sdk_version)

    # 3. Inject message context into fd 0 BEFORE importing contract
    #    (genlayer reads message from fd 0 at import time)
    _inject_message_to_fd0(vm)

    # 4. Load the contract module
    module = _load_module(contract_path)

    contract_cls = _find_contract_class(module)

    if contract_cls is None:
        raise ValueError(f"No contract class found in {contract_path}")

    return contract_cls


def deploy_contract(
    contract_path: Path,
    vm: "VMContext",
    *args: Any,
    sdk_version: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Deploy a contract and return an instance."""
    contract_path = Path(contract_path).resolve()

    if vm._contract_address is None:
        addr_hash = hashlib.sha256(str(contract_path).encode()).digest()[:20]
        vm._contract_address = addr_hash

    contract_cls = load_contract_class(contract_path, vm, sdk_version)

    # Patch run_nondet to skip pickling in direct mode
    _patch_run_nondet_for_direct_mode()

    instance = _allocate_contract(contract_cls, vm, *args, **kwargs)

    return instance


def _patch_run_nondet_for_direct_mode() -> None:
    """Replace gl.vm.run_nondet with a direct-mode version.

    The SDK's run_nondet pickles leader_fn via cloudpickle to pass through
    the WASM boundary. In direct mode there's no WASM, and the closure
    captures unpicklable objects (hashlib.HASH, classmethod_descriptor).
    We bypass pickling by calling leader_fn() directly.
    """
    try:
        import genlayer.gl.vm as gl_vm
    except ImportError:
        return

    if getattr(gl_vm, '_direct_mode_patched', False):
        return

    def _direct_run_nondet(leader_fn, validator_fn, /, **kwargs):
        return leader_fn()

    gl_vm.run_nondet = _direct_run_nondet
    gl_vm._direct_mode_patched = True

    # Also mock embeddings (ONNX model not available in direct mode)
    _mock_embeddings_for_direct_mode()


def _mock_embeddings_for_direct_mode() -> None:
    """Replace genlayer_embeddings.SentenceTransformer with a deterministic mock.

    The real SentenceTransformer requires ONNX model files set via
    GENLAYER_EMBEDDINGS_MODELS env var. In direct mode we generate
    deterministic 384-dim vectors from text hashes instead.
    """
    try:
        import genlayer_embeddings as gle
    except ImportError:
        return

    if getattr(gle, '_direct_mode_patched', False):
        return

    import numpy as np

    def _mock_sentence_transformer(model: str):
        def _embed(text: str) -> np.ndarray:
            h = hashlib.sha512(text.encode()).digest()
            # Expand hash to 384 floats deterministically
            arr = np.frombuffer(h * 6, dtype=np.uint8)[:384].astype(np.float32)
            # Normalize to unit vector
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            return arr
        return _embed

    gle.SentenceTransformer = _mock_sentence_transformer
    gle._direct_mode_patched = True


def _inject_message_to_fd0(vm: "VMContext") -> None:
    """Inject message context by replacing stdin (fd 0) with encoded message."""
    import os
    import tempfile

    try:
        from genlayer.py import calldata
        from genlayer.py.types import Address
    except ImportError:
        return

    # Convert addresses to Address type
    sender_addr = vm.sender
    if isinstance(sender_addr, bytes):
        sender_addr = Address(sender_addr)

    contract_addr = vm._contract_address
    if isinstance(contract_addr, bytes):
        contract_addr = Address(contract_addr)

    origin_addr = vm.origin
    if isinstance(origin_addr, bytes):
        origin_addr = Address(origin_addr)

    # Build message dict
    message_data = {
        'contract_address': contract_addr,
        'sender_address': sender_addr,
        'origin_address': origin_addr,
        'stack': [],
        'value': vm._value,
        'datetime': vm._datetime,
        'is_init': False,
        'chain_id': vm._chain_id,
        'entry_kind': 0,
        'entry_data': b'',
        'entry_stage_data': None,
    }

    # Encode the message
    encoded = calldata.encode(message_data)

    # Create a temp file with the encoded message
    fd, path = tempfile.mkstemp()
    try:
        os.write(fd, encoded)
        os.lseek(fd, 0, os.SEEK_SET)  # Reset to beginning

        # Save original stdin fd
        original_stdin = os.dup(0)
        vm._original_stdin_fd = original_stdin

        # Replace stdin with our temp file
        os.dup2(fd, 0)
    finally:
        os.close(fd)
        os.unlink(path)


def _load_module(contract_path: Path) -> Any:
    """Load a Python module from file path."""
    module_name = f"_contract_{contract_path.stem}"

    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, contract_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {contract_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise ImportError(f"Failed to load contract: {e}") from e

    return module


def _find_contract_class(module: Any) -> Optional[Type[Any]]:
    """Find the contract class in a module."""
    import dataclasses

    candidates = []

    for name in dir(module):
        if name.startswith('_'):
            continue

        obj = getattr(module, name)

        if not isinstance(obj, type):
            continue

        # Skip dataclasses - they're storage types, not contracts
        if dataclasses.is_dataclass(obj):
            continue

        # Highest priority: explicit __gl_contract__ marker
        if getattr(obj, '__gl_contract__', False):
            return obj

        # Second priority: inherits from Contract
        for base in obj.__mro__:
            if base.__name__ in ('Contract', 'gl.Contract'):
                return obj

        # Third priority: has storage-like annotations
        # Collect as candidates but don't return immediately
        if hasattr(obj, '__annotations__'):
            annotations = obj.__annotations__
            storage_types = ('TreeMap', 'DynArray', 'Array', 'u256', 'Address')
            for ann in annotations.values():
                ann_str = str(ann)
                if any(st in ann_str for st in storage_types):
                    candidates.append(obj)
                    break

    # Return first candidate if no explicit contract found
    if candidates:
        return candidates[0]

    return None


def _allocate_contract(
    contract_cls: Type[Any],
    vm: "VMContext",
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Allocate and initialize a contract instance."""
    try:
        from genlayer.py.storage import Root, ROOT_SLOT_ID
        from genlayer.py.storage._internal.generate import (
            ORIGINAL_INIT_ATTR,
            _storage_build,
            Lit,
        )

        # Build the storage type descriptor
        td = _storage_build(contract_cls, {})
        assert not isinstance(td, Lit)

        # Use the VM's storage manager
        slot = vm._storage.get_store_slot(ROOT_SLOT_ID)
        instance = td.get(slot, 0)

        # Find and call the original __init__
        init = getattr(td, 'cls', None)
        if init is None:
            init = getattr(contract_cls, '__init__', None)
        else:
            init = getattr(init, '__init__', None)
        if init is not None:
            if hasattr(init, ORIGINAL_INIT_ATTR):
                init = getattr(init, ORIGINAL_INIT_ATTR)
            init(instance, *args, **kwargs)

        return instance

    except ImportError:
        pass

    try:
        from genlayer.py.storage import Root

        Root.MANAGER = vm._storage

        root_slot = vm._storage.get_store_slot(b'\x00' * 32)

        instance = contract_cls.__new__(contract_cls)

        if hasattr(instance, '_storage_slot'):
            instance._storage_slot = root_slot.indirect(0)
            instance._off = 0

        if args or kwargs:
            instance.__init__(*args, **kwargs)

        return instance

    except ImportError:
        pass

    return contract_cls(*args, **kwargs)


def create_address(seed: str) -> Any:
    """Create a deterministic address from seed string."""
    addr_bytes = hashlib.sha256(seed.encode()).digest()[:20]

    try:
        from genlayer.py.types import Address
        return Address(addr_bytes)
    except ImportError:
        return addr_bytes


def create_test_addresses(count: int = 10) -> list:
    """Create a list of test addresses."""
    return [create_address(f"test_address_{i}") for i in range(count)]
