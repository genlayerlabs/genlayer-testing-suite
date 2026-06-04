"""Compatibility helpers for GenVM SDK layout changes."""

from __future__ import annotations

import sys
import types
import typing
from typing import Any

_UNSET = object()


class MessageType(typing.NamedTuple):
    contract_address: Any
    sender_address: Any
    origin_address: Any
    value: Any
    chain_id: Any


def import_calldata() -> Any:
    """Return calldata module from either the v0.2 or v0.3 SDK layout."""
    try:
        from genlayer.py import calldata
    except ImportError:
        from genlayer import calldata
    return calldata


def import_types() -> Any:
    """Return types module from either the v0.2 or v0.3 SDK layout."""
    try:
        from genlayer.py import types as sdk_types
    except ImportError:
        from genlayer import types as sdk_types
    return sdk_types


def import_address() -> type:
    return import_types().Address


def import_address_u256() -> tuple[type, Any]:
    sdk_types = import_types()
    return sdk_types.Address, sdk_types.u256


def import_lazy() -> Any:
    return import_types().Lazy


def install_star_import_compat() -> None:
    """Expose old `from genlayer import *` / `gl.*` surface on v0.3 SDKs."""
    import genlayer

    if hasattr(genlayer, "gl") and "genlayer.gl" in sys.modules:
        return

    gl_module = types.ModuleType("genlayer.gl")
    gl_module.__package__ = "genlayer"
    gl_module.__path__ = []

    from genlayer import calldata, chain, contract, eq_principle, evm, message
    from genlayer import nondet, private, public, storage, types as sdk_types, vm

    gl_module.calldata = calldata
    gl_module.chain = chain
    gl_module.contract = contract
    gl_module.eq_principle = eq_principle
    gl_module.evm = evm
    gl_module.message = message
    gl_module.nondet = nondet
    gl_module.public = public
    gl_module.private = private
    gl_module.storage = storage
    gl_module.vm = vm

    gl_module.Contract = contract.Contract
    gl_module.MessageType = MessageType
    gl_module.contract_interface = contract.interface
    gl_module.deploy_contract = contract.deploy
    gl_module.get_contract_at = contract.get_at
    gl_module.get_at = contract.get_at
    gl_module.message_raw = getattr(message, "raw", None)
    gl_module.message = MessageType(
        contract_address=getattr(message, "contract_address", None),
        sender_address=getattr(message, "sender_address", None),
        origin_address=getattr(message, "origin_address", None),
        value=getattr(message, "value", 0),
        chain_id=getattr(message, "chain_id", 0),
    )

    sys.modules["genlayer.gl"] = gl_module
    sys.modules.setdefault("genlayer.gl.vm", vm)
    sys.modules.setdefault("genlayer.gl.nondet", nondet)
    sys.modules.setdefault("genlayer.gl.eq_principle", eq_principle)
    sys.modules.setdefault("genlayer.gl.evm", evm)
    genlayer.gl = gl_module

    py_module = types.ModuleType("genlayer.py")
    py_module.__package__ = "genlayer"
    py_module.__path__ = []
    py_module.calldata = calldata
    py_module.evm = evm
    py_module.types = sdk_types
    sys.modules["genlayer.py"] = py_module
    sys.modules.setdefault("genlayer.py.calldata", calldata)
    sys.modules.setdefault("genlayer.py.evm", evm)
    sys.modules.setdefault("genlayer.py.types", sdk_types)
    genlayer.py = py_module

    exported = list(getattr(genlayer, "__all__", ()))
    if "gl" not in exported:
        genlayer.__all__ = (*exported, "gl")


def _coerce_address(value: Any) -> Any:
    if value is _UNSET or value is None:
        return value
    Address = import_address()
    if isinstance(value, Address):
        return value
    if isinstance(value, bytes):
        return Address(value)
    if hasattr(value, "as_bytes"):
        return Address(value.as_bytes)
    return value


def sync_message_context(
    *,
    contract_address: Any = _UNSET,
    sender_address: Any = _UNSET,
    origin_address: Any = _UNSET,
    value: Any = _UNSET,
    chain_id: Any = _UNSET,
) -> None:
    """Synchronize old `genlayer.gl` message fields and v0.3 message module."""
    contract_address = _coerce_address(contract_address)
    sender_address = _coerce_address(sender_address)
    origin_address = _coerce_address(origin_address)

    message_mod = sys.modules.get("genlayer.message")
    raw = getattr(message_mod, "raw", None) if message_mod is not None else None

    updates = {
        "contract_address": contract_address,
        "sender_address": sender_address,
        "origin_address": origin_address,
        "value": value,
        "chain_id": chain_id,
    }
    for name, next_value in updates.items():
        if next_value is _UNSET:
            continue
        if message_mod is not None:
            setattr(message_mod, name, next_value)
        if isinstance(raw, dict):
            raw[name] = next_value

    gl = sys.modules.get("genlayer.gl")
    if gl is None or not hasattr(gl, "MessageType"):
        return

    current = getattr(gl, "message", None)
    gl.message = gl.MessageType(
        contract_address=(
            contract_address
            if contract_address is not _UNSET
            else getattr(current, "contract_address", getattr(message_mod, "contract_address", None))
        ),
        sender_address=(
            sender_address
            if sender_address is not _UNSET
            else getattr(current, "sender_address", getattr(message_mod, "sender_address", None))
        ),
        origin_address=(
            origin_address
            if origin_address is not _UNSET
            else getattr(current, "origin_address", getattr(message_mod, "origin_address", None))
        ),
        value=value if value is not _UNSET else getattr(current, "value", getattr(message_mod, "value", 0)),
        chain_id=(
            chain_id
            if chain_id is not _UNSET
            else getattr(current, "chain_id", getattr(message_mod, "chain_id", 0))
        ),
    )
    if isinstance(raw, dict):
        gl.message_raw = raw
