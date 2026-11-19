import base64
import json
from unittest.mock import Mock

import pytest
from eth_account import Account
from genlayer_py.chains import localnet
from genlayer_py.client import GenLayerClient
from genlayer_py.exceptions import GenLayerError

from gltest.clients import _keep_rpc_error_details
from gltest.contracts.contract import Contract
from gltest.exceptions import GenLayerRPCError

STDERR = (
    "Traceback (most recent call last):\n"
    '  File "/contract.py", line 33, in new_encode\n'
    "    return old_encode(x, default=default)\n"
    "TypeError: Object of type Foo is not calldata-encodable\n"
)


def _studio_execution_failed(**genvm_result):
    """Error payload Studio returns when a gen_call/sim_call execution fails."""
    return {
        "code": -32000,
        "message": "execution failed",
        "data": {
            "receipt": {
                "execution_result": "ERROR",
                "result": base64.b64encode(b"\x02exit_code 1").decode(),
                "genvm_result": {"stdout": "", "stderr": STDERR, **genvm_result},
            },
            "params": {"type": "read"},
        },
    }


def _client(monkeypatch, error):
    client = GenLayerClient(localnet, account=Account.create())
    response = Mock()
    response.json.return_value = {"jsonrpc": "2.0", "id": 1, "error": error}
    post = Mock(return_value=response)
    monkeypatch.setattr("genlayer_py.provider.provider.requests.post", post)
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    return _keep_rpc_error_details(client)


@pytest.mark.parametrize("read_only", [True, False])
def test_call_surfaces_genvm_stderr(monkeypatch, read_only):
    _client(monkeypatch, _studio_execution_failed())
    contract = Contract.new(
        "0x" + "12" * 20, {"methods": {"get": {"readonly": read_only}}}
    ).connect(Account.create())

    with pytest.raises(GenLayerRPCError) as excinfo:
        contract.get().call()

    err = excinfo.value
    assert isinstance(err, GenLayerError)
    assert err.method == ("gen_call" if read_only else "sim_call")
    assert err.code == -32000
    assert err.stderr == STDERR
    assert err.execution_error == "exit_code 1"
    message = str(err)
    assert message.startswith(f"{err.method} failed (code=-32000): execution failed")
    assert "execution_result: ERROR" in message
    assert "error: exit_code 1" in message
    assert "TypeError: Object of type Foo is not calldata-encodable" in message


def test_error_description_preferred_over_result_bytes(monkeypatch):
    client = _client(
        monkeypatch, _studio_execution_failed(error_description="contract panicked")
    )
    with pytest.raises(GenLayerRPCError, match="error: contract panicked"):
        client.provider.make_request("gen_call", [{}])


def test_long_stderr_keeps_the_tail():
    stderr = "noise\n" * 2000 + "ValueError: the real cause\n"
    err = GenLayerRPCError(
        "gen_call",
        -32000,
        "execution failed",
        {"receipt": {"genvm_result": {"stderr": stderr}}},
    )
    assert "...(truncated)" in str(err)
    assert str(err).endswith("ValueError: the real cause")
    assert err.stderr == stderr


@pytest.mark.parametrize(
    "error, expected",
    [
        ({"code": -32602, "message": "bad params", "data": {}}, None),
        ({"code": -32001, "message": "nope", "data": {"x": 1}}, 'data: {"x": 1}'),
        ({"message": "no code"}, None),
        ("plain string error", None),
    ],
)
def test_other_rpc_errors(monkeypatch, error, expected):
    client = _client(monkeypatch, error)
    with pytest.raises(GenLayerRPCError) as excinfo:
        client.provider.make_request("gen_call", [{}])
    message = str(excinfo.value)
    first_line = message.splitlines()[0]
    if isinstance(error, dict):
        code = error.get("code", "unknown")
        assert first_line == f"gen_call failed (code={code}): {error['message']}"
        assert excinfo.value.data == error.get("data")
    else:
        assert first_line == "gen_call failed (code=unknown): plain string error"
    if expected is None:
        assert message == first_line
    else:
        assert expected in message
        json.loads(message.split("data: ", 1)[1])


def test_successful_responses_pass_through(monkeypatch):
    client = _client(monkeypatch, None)
    resp = client.provider.make_request("gen_call", [{}])
    assert resp["error"] is None
