from unittest.mock import Mock

import pytest
from eth_account import Account
from genlayer_py.types import SimConfig

from gltest.contracts.contract import Contract
from gltest.types import TransactionHashVariant


@pytest.mark.parametrize("read_only", [True, False])
@pytest.mark.parametrize("custom_options", [False, True])
def test_call_forwards_to_sdk(monkeypatch, read_only, custom_options):
    client = Mock()
    client.read_contract.return_value = {"value": 42}
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    account = Account.create()
    contract = Contract.new(
        address="0x123",
        schema={"methods": {"method": {"readonly": read_only}}},
    ).connect(account)
    variant = (
        TransactionHashVariant.LATEST_FINAL
        if custom_options
        else TransactionHashVariant.LATEST_NONFINAL
    )
    context = {"genvm_datetime": "2026-01-01T00:00:00Z"} if custom_options else None
    options = (
        {"transaction_hash_variant": variant, "transaction_context": context}
        if custom_options
        else {}
    )

    assert contract.method(args=[42]).call(**options) == {"value": 42}

    client.read_contract.assert_called_once_with(
        address="0x123",
        function_name="method",
        account=account,
        args=[42],
        transaction_hash_variant=variant,
        sim_config=SimConfig(**context) if context else None,
    )
    client.write_contract.assert_not_called()
    client.wait_for_transaction_receipt.assert_not_called()


def test_write_call_propagates_sdk_error(monkeypatch):
    client = Mock()
    client.read_contract.side_effect = RuntimeError("Contract execution failed")
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    contract = Contract.new(
        address="0x123", schema={"methods": {"write": {"readonly": False}}}
    )

    with pytest.raises(RuntimeError, match="Contract execution failed"):
        contract.write().call()

    client.write_contract.assert_not_called()


def test_read_method_still_rejects_transact():
    contract = Contract.new(
        address="0x123", schema={"methods": {"read": {"readonly": True}}}
    )

    with pytest.raises(ValueError, match="Cannot transact read-only method"):
        contract.read().transact()
