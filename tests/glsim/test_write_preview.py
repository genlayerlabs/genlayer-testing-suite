from pathlib import Path
from unittest.mock import Mock

import pytest
import rlp
from eth_account import Account
from genlayer_py.abi import calldata
from genlayer_py.chains import localnet
from genlayer_py.client import GenLayerClient
from genlayer_py.exceptions import GenLayerError
from starlette.testclient import TestClient

from glsim.server import create_app
from gltest.contracts.contract import Contract


@pytest.fixture
def preview(monkeypatch):
    app = create_app(num_validators=1, llm_provider=None, use_browser=False)
    with TestClient(app) as http:

        def rpc(method, params):
            response = http.post(
                "/api",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params,
                },
            ).json()
            if "error" in response:
                raise GenLayerError(response["error"]["message"])
            return response

        sdk = GenLayerClient(localnet, account=Account.create())
        requests = Mock(side_effect=rpc)
        monkeypatch.setattr(sdk.provider, "make_request", requests)
        monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: sdk)
        contracts = []
        for _ in range(2):
            address = rpc(
                "sim_deploy",
                {
                    "code_path": str(
                        Path(__file__).with_name("write_preview_contract.py")
                    ),
                    "args": [],
                },
            )["result"]["contract_address"]
            schema = rpc("gen_getContractSchema", [address])["result"]
            contracts.append(Contract.new(address, schema))
        yield contracts, app.state.engine, requests


@pytest.mark.parametrize("fail", [False, True])
def test_write_call_previews_value_and_messages(preview, monkeypatch, fail):
    (sender, receiver), engine, requests = preview
    execute = Mock(wraps=engine.call_method)
    monkeypatch.setattr(engine, "call_method", execute)
    snapshots = set(engine._snapshots)
    fees = {"distribution": {"leaderTimeunitsAllocation": 1}, "messageAllocations": []}

    if fail:
        with pytest.raises(GenLayerError, match="preview failed after emit"):
            sender.send([receiver.address, True]).call(
                value=37, fees=fees, fee_value=70
            )
    else:
        assert (
            sender.send([receiver.address, False]).call(
                value=37,
                fees=fees,
                fee_value=70,
            )
            == 37
        )
        # Prove the emitted message actually executed inside the preview.
        assert any(call.args[1] == "receive" for call in execute.call_args_list)

    request = requests.call_args
    assert request.kwargs["method"] == "sim_call"
    payload = request.kwargs["params"][0]
    assert payload["type"] == "write"
    assert payload["value"] == "0x25"
    assert int(payload["fees"]["feeValue"]) == 70
    assert engine._post_queue == []
    assert engine._captured_triggered_ops == []
    assert set(engine._snapshots) == snapshots
    assert engine.vm._value == 0

    execute.reset_mock()
    # A subsequent top-level read must not deliver a leaked message.
    assert sender.get_value().call() == 0
    assert receiver.get_received().call() == 0
    assert not any(call.args[1] == "receive" for call in execute.call_args_list)


@pytest.mark.parametrize("value", [0, 123])
def test_payable_write_call_returns_value_without_persisting_it(preview, value):
    (contract, _), engine, _ = preview
    assert contract.take_value().call(value=value) == value
    assert contract.get_value().call() == 0
    assert engine.vm._value == 0


def test_gen_call_failed_emit_does_not_leak_messages(preview, monkeypatch):
    (sender, receiver), engine, requests = preview
    encoded = calldata.encode(
        {
            "": "send",
            "args": [receiver.address, True],
        }
    )
    with pytest.raises(GenLayerError, match="preview failed after emit"):
        requests(
            method="gen_call",
            params=[
                {
                    "type": "read",
                    "to": sender.address,
                    "data": "0x" + rlp.encode([encoded, b"\x00"]).hex(),
                }
            ],
        )

    assert engine._post_queue == []
    assert engine._captured_triggered_ops == []
    execute = Mock(wraps=engine.call_method)
    monkeypatch.setattr(engine, "call_method", execute)
    assert receiver.get_received().call() == 0
    assert not any(call.args[1] == "receive" for call in execute.call_args_list)


def test_view_call_does_not_snapshot_all_state(preview, monkeypatch):
    (sender, _), engine, _ = preview
    snapshot = Mock(side_effect=AssertionError("view call should not snapshot"))
    monkeypatch.setattr(engine, "create_snapshot", snapshot)
    assert sender.get_value().call() == 0
    snapshot.assert_not_called()
