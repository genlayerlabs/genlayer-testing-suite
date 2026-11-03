"""Helpers for the GenVM SDK layouts.

The v0.3 SDK exposes its modules at the package root (``genlayer.calldata``,
``genlayer.vm``). The v0.2 SDK, still pinned by legacy contracts, keeps them
under ``genlayer.py`` and ``genlayer.gl``.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

_UNSET = object()


def _import_first(*names: str) -> Any:
    for name in names[:-1]:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name is None or not name.startswith(exc.name):
                raise
    return importlib.import_module(names[-1])


def import_calldata() -> Any:
    """Return the calldata module from the active SDK path."""
    return _import_first("genlayer.calldata", "genlayer.py.calldata")


def import_types() -> Any:
    """Return the types module from the active SDK path."""
    return _import_first("genlayer.types", "genlayer.py.types")


def import_vm() -> Any:
    """Return the vm module from the active SDK path."""
    return _import_first("genlayer.vm", "genlayer.gl.vm")


def import_address() -> type:
    return import_types().Address


def import_address_u256() -> tuple[type, Any]:
    sdk_types = import_types()
    return sdk_types.Address, sdk_types.u256


def import_lazy() -> Any:
    return import_types().Lazy


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
    """Synchronize the loaded message context without triggering a fresh import."""
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

    _sync_legacy_message(updates)


def message_context_loaded() -> bool:
    return "genlayer.message" in sys.modules or "genlayer.gl" in sys.modules


def _sync_legacy_message(updates: dict[str, Any]) -> None:
    # v0.2 keeps gl.message_raw (dict) and gl.message (NamedTuple) on genlayer.gl.
    gl_mod = sys.modules.get("genlayer.gl")
    if gl_mod is None:
        return
    changed = {k: v for k, v in updates.items() if v is not _UNSET}
    raw = getattr(gl_mod, "message_raw", None)
    if isinstance(raw, dict):
        raw.update(changed)
    message = getattr(gl_mod, "message", None)
    if message is not None and hasattr(message, "_replace"):
        fields = getattr(message, "_fields", ())
        gl_mod.message = message._replace(
            **{k: v for k, v in changed.items() if k in fields}
        )
