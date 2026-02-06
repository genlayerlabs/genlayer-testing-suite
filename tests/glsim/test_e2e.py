import pytest
from pathlib import Path

STORAGE_CONTRACT = str(Path(__file__).parent.parent / "examples" / "contracts" / "storage.py")


@pytest.fixture
def client():
    """Create a test client for the glsim server."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=1, llm_provider=None, use_browser=False, verbose=False)
    with TestClient(app) as c:
        yield c


def _rpc(client, method, params=None, req_id=1):
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params is not None:
        payload["params"] = params
    resp = client.post("/api", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == req_id
    return data


def _deploy(client, args=None):
    """Helper: deploy storage contract, return address + tx_hash."""
    data = _rpc(client, "sim_deploy", {
        "code_path": STORAGE_CONTRACT,
        "args": args or ["initial"],
    })
    assert "result" in data, f"Deploy failed: {data}"
    return data["result"]["contract_address"], data["result"]["tx_hash"]


# -- Basic RPC --

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ping(client):
    assert _rpc(client, "ping")["result"] == "pong"


def test_eth_chain_id(client):
    data = _rpc(client, "eth_chainId")
    assert data["result"] == hex(61999)


def test_net_version(client):
    assert _rpc(client, "net_version")["result"] == "61999"


def test_eth_gas_price(client):
    assert _rpc(client, "eth_gasPrice")["result"] == "0x0"


def test_method_not_found(client):
    data = _rpc(client, "nonexistent_method")
    assert "error" in data
    assert data["error"]["code"] == -32601


def test_invalid_request(client):
    resp = client.post("/api", json={"not": "jsonrpc"})
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32600


# -- Deploy / Read / Write --

def test_deploy_and_read_write(client):
    addr, _ = _deploy(client, ["hello"])

    # Read initial
    data = _rpc(client, "sim_read", {"to": addr, "method": "get_storage"})
    assert data["result"]["result"] == "hello"

    # Write
    data = _rpc(client, "sim_call", {
        "to": addr, "method": "update_storage", "args": ["world"],
    })
    assert "result" in data

    # Read updated
    data = _rpc(client, "sim_read", {"to": addr, "method": "get_storage"})
    assert data["result"]["result"] == "world"


def test_multiple_deploys(client):
    addr1, _ = _deploy(client, ["first"])
    addr2, _ = _deploy(client, ["second"])
    assert addr1 != addr2

    r1 = _rpc(client, "sim_read", {"to": addr1, "method": "get_storage"})
    r2 = _rpc(client, "sim_read", {"to": addr2, "method": "get_storage"})
    assert r1["result"]["result"] == "first"
    assert r2["result"]["result"] == "second"


# -- Transactions --

def test_tx_receipt_deploy(client):
    addr, tx_hash = _deploy(client)
    data = _rpc(client, "sim_getTransactionReceipt", {"transaction_hash": tx_hash})
    receipt = data["result"]
    assert receipt["status"] == "0x1"
    assert receipt["contractAddress"] == addr


def test_tx_receipt_call(client):
    addr, _ = _deploy(client)
    call_data = _rpc(client, "sim_call", {
        "to": addr, "method": "update_storage", "args": ["new"],
    })
    tx_hash = call_data["result"]["tx_hash"]
    receipt = _rpc(client, "sim_getTransactionReceipt", {"transaction_hash": tx_hash})["result"]
    assert receipt["status"] == "0x1"
    assert receipt["contractAddress"] is None


def test_block_number_increments(client):
    b0 = int(_rpc(client, "eth_blockNumber")["result"], 16)
    _deploy(client)
    b1 = int(_rpc(client, "eth_blockNumber")["result"], 16)
    assert b1 == b0 + 1


# -- Accounts --

def test_fund_and_balance(client):
    addr = "0x" + "ab" * 20

    # Initially 0
    assert _rpc(client, "sim_getBalance", {"account_address": addr})["result"] == 0

    # Fund
    data = _rpc(client, "sim_fundAccount", {"account_address": addr, "amount": 5000})
    assert data["result"]["balance"] == 5000

    # sim_getBalance
    assert _rpc(client, "sim_getBalance", {"account_address": addr})["result"] == 5000

    # eth_getBalance returns hex
    assert _rpc(client, "eth_getBalance", {"account_address": addr})["result"] == hex(5000)


# -- Schema --

def test_contract_schema(client):
    addr, _ = _deploy(client)
    data = _rpc(client, "sim_getContractSchema", {"contract_address": addr})
    schema = data["result"]
    assert schema["class_name"] == "Storage"
    method_names = [m["name"] for m in schema["methods"]]
    assert "get_storage" in method_names
    assert "update_storage" in method_names


# -- Error cases --

def test_call_nonexistent_contract(client):
    data = _rpc(client, "sim_call", {
        "to": "0x" + "00" * 20, "method": "foo",
    })
    assert "error" in data


def test_call_nonexistent_method(client):
    addr, _ = _deploy(client)
    data = _rpc(client, "sim_call", {"to": addr, "method": "nonexistent"})
    assert "error" in data


def test_deploy_missing_file(client):
    data = _rpc(client, "sim_deploy", {"code_path": "/nonexistent/contract.py"})
    assert "error" in data


# -- Batch --

def test_batch_request(client):
    batch = [
        {"jsonrpc": "2.0", "method": "ping", "id": 1},
        {"jsonrpc": "2.0", "method": "eth_chainId", "id": 2},
    ]
    resp = client.post("/api", json=batch)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2
    assert results[0]["result"] == "pong"
    assert results[1]["result"] == hex(61999)
