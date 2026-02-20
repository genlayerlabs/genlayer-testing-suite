from pathlib import Path

from starlette.testclient import TestClient

from glsim.server import create_app

FACTORY_CONTRACT = str(Path(__file__).parent / "deterministic_factory_contract.py")


def _rpc(client: TestClient, method: str, params=None, req_id: int = 1):
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params is not None:
        payload["params"] = params
    response = client.post("/api", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == req_id
    return body


def test_deterministic_in_contract_deploy_uses_returned_address():
    app = create_app(num_validators=1, llm_provider=None, use_browser=False, verbose=True)

    with TestClient(app) as client:
        deploy_response = _rpc(
            client,
            "sim_deploy",
            {
                "code_path": FACTORY_CONTRACT,
                "args": [],
            },
        )
        factory_address = deploy_response["result"]["contract_address"]

        call_response = _rpc(
            client,
            "sim_call",
            {
                "to": factory_address,
                "method": "deploy_child",
                "args": [12345],
            },
        )
        child_address = call_response["result"]["result"]
        assert isinstance(child_address, str)
        assert child_address.startswith("0x")

        # The returned deterministic address must be an actually deployed contract.
        ping_response = _rpc(
            client,
            "sim_read",
            {
                "to": child_address,
                "method": "ping",
                "args": [],
            },
        )
        assert ping_response["result"]["result"] == "pong"
