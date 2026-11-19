import base64
from unittest.mock import Mock

import pytest
from eth_account import Account
from genlayer_py.types import SimConfig
from genlayer_py.abi import calldata
from genlayer_py.chains import testnet_bradbury as bradbury
from genlayer_py.client import GenLayerClient
from genlayer_py.exceptions import GenLayerError

from gltest.contracts.contract import Contract
from gltest.types import TransactionHashVariant


@pytest.mark.parametrize("read_only", [True, False])
@pytest.mark.parametrize("custom_options", [False, True])
def test_call_forwards_to_sdk(monkeypatch, read_only, custom_options):
    client = Mock()
    client.read_contract.return_value = {"value": 42}
    client.simulate_write_contract.return_value = {
        "execution_result": "SUCCESS",
        "result": base64.b64encode(b"\x00" + calldata.encode({"value": 42})).decode(),
    }
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
    fees = {
        "distribution": {"totalMessageFees": 7},
        "messageAllocations": [{"recipient": "0x456", "budget": 7}],
    }
    if not read_only and custom_options:
        options.update(value=12, fees=fees, fee_value=70)

    assert contract.method(args=[42]).call(**options) == {"value": 42}

    expected = {
        "address": "0x123",
        "function_name": "method",
        "account": account,
        "args": [42],
        "transaction_hash_variant": variant,
        "sim_config": SimConfig(**context) if context else None,
    }
    if read_only:
        client.read_contract.assert_called_once_with(**expected)
        client.simulate_write_contract.assert_not_called()
    else:
        client.simulate_write_contract.assert_called_once_with(
            **expected,
            value=12 if custom_options else 0,
            fees={**fees, "feeValue": 70} if custom_options else None,
        )
        client.read_contract.assert_not_called()
        assert "feeValue" not in fees
    client.write_contract.assert_not_called()
    client.wait_for_transaction_receipt.assert_not_called()


def test_write_call_propagates_sdk_error(monkeypatch):
    client = Mock()
    client.simulate_write_contract.side_effect = RuntimeError(
        "Contract execution failed"
    )
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    contract = Contract.new(
        address="0x123", schema={"methods": {"write": {"readonly": False}}}
    )

    with pytest.raises(RuntimeError, match="Contract execution failed"):
        contract.write().call()

    client.write_contract.assert_not_called()


@pytest.mark.parametrize("result", [None, "hello", 42, b"bytes", [1, False]])
@pytest.mark.parametrize("receipt_format", ["studio", "glsim"])
def test_write_call_decodes_receipt(monkeypatch, result, receipt_format):
    encoded = calldata.encode(result)
    if receipt_format == "studio":
        receipt = {
            "execution_result": "SUCCESS",
            "result": base64.b64encode(b"\x00" + encoded).decode(),
        }
    else:
        receipt = {
            "consensus_data": {
                "leader_receipt": [
                    {
                        "execution_result": "SUCCESS",
                        "result": base64.b64encode(encoded).decode(),
                    }
                ]
            }
        }
    client = Mock()
    client.simulate_write_contract.return_value = receipt
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    contract = Contract.new("0x123", {"methods": {"write": {"readonly": False}}})
    assert contract.write().call() == result


@pytest.mark.parametrize("status", ["ERROR", "SUCCESS"])
def test_write_call_raises_on_failed_result(monkeypatch, status):
    client = Mock()
    client.simulate_write_contract.return_value = {
        "execution_result": status,
        "result": base64.b64encode(b"\x01reverted").decode(),
    }
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    contract = Contract.new("0x123", {"methods": {"write": {"readonly": False}}})
    with pytest.raises(GenLayerError, match="reverted"):
        contract.write().call()


def test_write_call_rejects_unsupported_chain(monkeypatch):
    client = GenLayerClient(bradbury, account=Account.create())
    request = Mock()
    monkeypatch.setattr(client.provider, "make_request", request)
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    contract = Contract.new("0x123", {"methods": {"write": {"readonly": False}}})
    with pytest.raises(GenLayerError, match="only supported on Studio"):
        contract.write().call()
    request.assert_not_called()


@pytest.mark.parametrize("options", [{"value": 1}, {"fees": {}}, {"fee_value": 0}])
def test_read_call_rejects_write_options(options):
    contract = Contract.new("0x123", {"methods": {"read": {"readonly": True}}})
    with pytest.raises(ValueError, match="require a write method"):
        contract.read().call(**options)


def test_read_method_still_rejects_transact():
    contract = Contract.new(
        address="0x123", schema={"methods": {"read": {"readonly": True}}}
    )

    with pytest.raises(ValueError, match="Cannot transact read-only method"):
        contract.read().transact()
