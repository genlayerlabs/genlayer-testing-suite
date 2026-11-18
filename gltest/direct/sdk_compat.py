"""Helpers for the GenVM v0.3 SDK layout."""

from __future__ import annotations

import sys
from typing import Any

_UNSET = object()


def import_calldata() -> Any:
    """Return the v0.3 calldata module from the active SDK path."""
    from genlayer import calldata

    return calldata


def import_types() -> Any:
    """Return the v0.3 types module from the active SDK path."""
    from genlayer import types as sdk_types

    return sdk_types


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
    """Synchronize the v0.3 message module without triggering a fresh import."""
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
