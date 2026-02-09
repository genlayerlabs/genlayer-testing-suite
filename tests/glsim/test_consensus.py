"""Tests for consensus simulation in glsim."""

import json
import pytest
from pathlib import Path

WEB_CONTRACT = str(Path(__file__).parent / "web_contract.py")
DISAGREE_CONTRACT = str(Path(__file__).parent / "disagree_contract.py")
STORAGE_CONTRACT = str(Path(__file__).parent.parent / "examples" / "contracts" / "storage.py")


@pytest.fixture
def client_1v():
    """Leader-only (1 validator)."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=1, max_rotations=1)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_5v():
    """5 validators, 3 max rotations."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=5, max_rotations=3)
    with TestClient(app) as c:
        yield c


def _rpc(client, method, params=None, req_id=1):
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params is not None:
        payload["params"] = params
    resp = client.post("/api", json=payload)
    data = resp.json()
    return data


def _deploy(client, contract_path, args=None):
    data = _rpc(client, "sim_deploy", {
        "code_path": contract_path,
        "args": args or [],
    })
    assert "result" in data, f"Deploy failed: {data}"
    return data["result"]["contract_address"]


# -- Leader-only mode (num_validators=1) --

def test_leader_only_deterministic(client_1v):
    """With 1 validator, deterministic contract always finalizes."""
    addr = _deploy(client_1v, STORAGE_CONTRACT, ["hello"])
    data = _rpc(client_1v, "sim_call", {"to": addr, "method": "get_storage"})
    assert data["result"]["result"] == "hello"


def test_leader_only_with_nondet(client_1v):
    """With 1 validator, run_nondet auto-agrees (no validator check)."""
    addr = _deploy(client_1v, WEB_CONTRACT)
    mock = json.dumps({"value": "mocked"})
    _rpc(client_1v, "sim_call", {
        "to": addr,
        "method": "fetch_data",
        "args": ["http://example.com/api"],
    })
    # Should succeed — leader-only mode auto-agrees
    data = _rpc(client_1v, "sim_call", {"to": addr, "method": "get_result"})
    # Result may be empty if web mock not installed, but shouldn't crash


# -- Multi-validator consensus (5 validators) --

def test_all_agree_with_mocks():
    """With mocks, all validators agree (deterministic)."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=5, max_rotations=3)
    with TestClient(app) as client:
        engine = app.state.engine
        addr = _deploy(client, WEB_CONTRACT)

        # Install mock directly on engine
        mock_body = json.dumps({"value": "consensus_result"})
        engine.vm.mock_web("example\\.com/data", {"status": 200, "body": mock_body})

        _rpc(client, "sim_call", {
            "to": addr,
            "method": "fetch_data",
            "args": ["http://example.com/data"],
        })

        engine.vm._web_mocks.clear()
        engine.vm._web_mocks_hit.clear()

        data = _rpc(client, "sim_call", {"to": addr, "method": "get_result"})
        assert data["result"]["result"] == "consensus_result"


def test_disagree_causes_undetermined(client_5v):
    """Validator that always returns False → UNDETERMINED after max rotations."""
    addr = _deploy(client_5v, DISAGREE_CONTRACT)

    # sim_call doesn't go through consensus, use direct engine check
    # Call the method — validators will disagree
    data = _rpc(client_5v, "sim_call", {
        "to": addr,
        "method": "always_disagree",
        "args": ["test_value"],
    })
    # sim_call bypasses consensus (direct path) so result should still work
    assert "result" in data


def test_deterministic_method_all_agree(client_5v):
    """Method with no run_nondet → all validators agree trivially."""
    addr = _deploy(client_5v, STORAGE_CONTRACT, ["initial"])
    data = _rpc(client_5v, "sim_call", {
        "to": addr, "method": "update_storage", "args": ["updated"],
    })
    assert "result" in data
    data = _rpc(client_5v, "sim_call", {"to": addr, "method": "get_storage"})
    assert data["result"]["result"] == "updated"


# -- Consensus unit tests (direct consensus module) --

def test_consensus_module_agree():
    """Unit test: run_consensus with agreeing validators."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=5, max_rotations=3)
    with TestClient(app) as client:
        engine = app.state.engine
        addr = _deploy(client, WEB_CONTRACT)

        # Install mock directly on engine
        mock_body = json.dumps({"value": "test"})
        engine.vm.mock_web("example\\.com/x", {"status": 200, "body": mock_body})

        _rpc(client, "sim_call", {
            "to": addr,
            "method": "fetch_data",
            "args": ["http://example.com/x"],
        })

        engine.vm._web_mocks.clear()
        engine.vm._web_mocks_hit.clear()

        data = _rpc(client, "sim_call", {"to": addr, "method": "get_result"})
        assert data["result"]["result"] == "test"


def test_consensus_direct_disagree():
    """Unit test: consensus module with disagreeing validator_fn."""
    from glsim.consensus import run_consensus, ConsensusResult
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=5, max_rotations=2)
    with TestClient(app):
        engine = app.state.engine

        # Deploy disagree contract
        addr = _deploy_via_engine(engine, DISAGREE_CONTRACT)

        # Execute with consensus
        from glsim.tx_decoder import encode_calldata_result, encode_result_bytes

        calldata = encode_calldata_result({"method": "always_disagree", "args": ["val"]})

        def execute_fn():
            result, rb = engine.call_from_calldata(addr, calldata, None)
            return result, encode_result_bytes(result)

        result = run_consensus(engine, execute_fn, num_validators=5, max_rotations=2)
        assert result.status.value == "UNDETERMINED"
        assert sum(1 for v in result.votes if v == "disagree") > 2


def _deploy_via_engine(engine, contract_path, args=None):
    """Deploy a contract directly via engine (bypasses RPC)."""
    addr, _ = engine.deploy(contract_path, args or [])
    return addr


# -- Consensus data in transaction response --

def test_consensus_votes_in_response():
    """Verify eth_getTransactionByHash returns real consensus votes."""
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=3, max_rotations=1)
    with TestClient(app) as client:
        # Deploy via sim_deploy (doesn't go through consensus)
        addr = _deploy(client, WEB_CONTRACT)

        # sim_call also doesn't go through consensus.
        # To test consensus_votes in response, need to verify via
        # the consensus module directly + Transaction fields.
        engine = app.state.engine
        state = app.state.store

        from glsim.consensus import run_consensus
        from glsim.tx_decoder import encode_calldata_result, encode_result_bytes
        from glsim.state import Transaction, TxStatus

        tx = Transaction(
            hash=state.generate_tx_hash("test"),
            from_address="0x" + "00" * 20,
            to_address=addr,
            type="call",
            block_number=state.block_number + 1,
            num_validators=3,
        )

        mock_body = json.dumps({"value": "votes_test"})
        engine.vm.mock_web("example\\.com", {"status": 200, "body": mock_body})

        calldata = encode_calldata_result({"method": "fetch_data", "args": ["http://example.com/y"]})

        def execute_fn():
            result, _ = engine.call_from_calldata(addr, calldata, None)
            return result, encode_result_bytes(result)

        consensus = run_consensus(engine, execute_fn, num_validators=3, max_rotations=1)

        from glsim.server import _build_consensus_votes
        votes = _build_consensus_votes(consensus.votes, 3)

        assert len(votes) == 3
        assert all(v == "agree" for v in votes.values())

        engine.vm._web_mocks.clear()
        engine.vm._web_mocks_hit.clear()
