"""Tests for SDK-compatible RPC methods.

Tests the GenLayer protocol: eth_sendRawTransaction, eth_getTransactionReceipt,
eth_getTransactionByHash, gen_call, gen_getContractSchema.
"""

import base64
import pytest
from pathlib import Path
from eth_account import Account
from web3 import Web3
from eth_abi import encode as abi_encode
import rlp as rlp_mod

from genlayer_py.abi import calldata
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI

STORAGE_CONTRACT = str(Path(__file__).parent.parent / "examples" / "contracts" / "storage.py")
WEB_CONTRACT = str(Path(__file__).parent / "web_contract.py")


@pytest.fixture
def client():
    from glsim.server import create_app
    from starlette.testclient import TestClient
    app = create_app(num_validators=1, llm_provider=None, use_browser=False, verbose=True)
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


def _deploy_simple(client, init_value="hello"):
    """Deploy storage contract via sim_deploy (simple helper)."""
    data = _rpc(client, "sim_deploy", {
        "code_path": STORAGE_CONTRACT,
        "args": [init_value],
    })
    assert "result" in data, f"Deploy failed: {data}"
    return data["result"]["contract_address"]


def _build_add_transaction_data(sender_addr, recipient, code_or_calldata, is_deploy=False, constructor_args=None):
    """Build ABI-encoded addTransaction data like the SDK does."""
    w3 = Web3()
    contract = w3.eth.contract(abi=CONSENSUS_MAIN_ABI)
    fn = contract.get_function_by_name("addTransaction")

    if is_deploy:
        # Deploy: rlp([code_bytes, calldata_bytes, leader_only])
        code_bytes = code_or_calldata
        ctor_args = constructor_args if constructor_args is not None else []
        constructor_calldata = calldata.encode({"method": None, "args": ctor_args, "kwargs": {}})
        rlp_data = rlp_mod.encode([code_bytes, constructor_calldata, b"\x00"])
    else:
        # Call: rlp([calldata_bytes, leader_only])
        rlp_data = rlp_mod.encode([code_or_calldata, b"\x00"])

    from eth_utils.crypto import keccak
    if len(fn.argument_types) >= 6:
        params = abi_encode(
            fn.argument_types,
            [sender_addr, recipient, 1, 3, rlp_data, 0],
        )
        selector = keccak(text=fn.signature)[:4].hex()
    else:
        legacy_types = ("address", "address", "uint256", "uint256", "bytes")
        params = abi_encode(
            legacy_types,
            [sender_addr, recipient, 1, 3, rlp_data],
        )
        selector = keccak(text="addTransaction(address,address,uint256,uint256,bytes)")[:4].hex()

    return bytes.fromhex(selector + params.hex())


def _build_add_transaction_data_v5(sender_addr, recipient, code_or_calldata, is_deploy=False, constructor_args=None):
    """Build legacy 5-arg addTransaction calldata (without validUntil)."""
    if is_deploy:
        code_bytes = code_or_calldata
        ctor_args = constructor_args if constructor_args is not None else []
        constructor_calldata = calldata.encode({"method": None, "args": ctor_args, "kwargs": {}})
        rlp_data = rlp_mod.encode([code_bytes, constructor_calldata, b"\x00"])
    else:
        rlp_data = rlp_mod.encode([code_or_calldata, b"\x00"])

    from eth_utils.crypto import keccak
    selector = keccak(text="addTransaction(address,address,uint256,uint256,bytes)")[:4].hex()
    params = abi_encode(
        ("address", "address", "uint256", "uint256", "bytes"),
        [sender_addr, recipient, 1, 3, rlp_data],
    )
    return bytes.fromhex(selector + params.hex())


def _sign_and_send(client, acct, to_addr, data_bytes):
    """Sign tx and send via eth_sendRawTransaction."""
    w3 = Web3()
    tx = {
        "nonce": 0,
        "gasPrice": 0,
        "gas": 21000,
        "to": to_addr,
        "value": 0,
        "data": data_bytes,
        "chainId": 61999,
    }
    signed = acct.sign_transaction(tx)
    raw_hex = w3.to_hex(signed.raw_transaction)
    return _rpc(client, "eth_sendRawTransaction", [raw_hex])


# ---------------------------------------------------------------------------
# eth_sendRawTransaction + receipt + transaction
# ---------------------------------------------------------------------------

def test_eth_send_raw_transaction_deploy(client):
    """Deploy a contract via eth_sendRawTransaction (full SDK flow)."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()

    data = _build_add_transaction_data(
        acct.address,
        "0x" + "00" * 20,  # zero address = deploy
        code,
        is_deploy=True,
        constructor_args=["test_value"],
    )

    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    assert "result" in resp, f"SendRawTx failed: {resp}"
    eth_tx_hash = resp["result"]
    assert eth_tx_hash.startswith("0x")


def test_eth_send_raw_transaction_deploy_legacy_v5(client):
    """Deploy via eth_sendRawTransaction using legacy 5-arg addTransaction ABI."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()

    data = _build_add_transaction_data_v5(
        acct.address,
        "0x" + "00" * 20,  # zero address = deploy
        code,
        is_deploy=True,
        constructor_args=["test_value"],
    )

    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    assert "result" in resp, f"SendRawTx failed: {resp}"
    eth_tx_hash = resp["result"]
    assert eth_tx_hash.startswith("0x")


def test_eth_get_transaction_by_hash_includes_triggered_transactions_graph(client):
    """Synthetic triggered transaction graph is exposed for Studio-compatible polling."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()

    # Deploy a parent contract first so we can send a call transaction.
    deploy_data = _build_add_transaction_data(
        acct.address,
        "0x" + "00" * 20,
        code,
        is_deploy=True,
        constructor_args=["initial"],
    )
    deploy_resp = _sign_and_send(
        client,
        acct,
        "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",
        deploy_data,
    )
    deploy_eth_hash = deploy_resp["result"]
    deploy_receipt = _rpc(client, "eth_getTransactionReceipt", [deploy_eth_hash])["result"]
    deploy_gl_id = deploy_receipt["logs"][0]["topics"][1]
    deployed_tx = _rpc(client, "eth_getTransactionByHash", [deploy_gl_id])["result"]
    contract_addr = deployed_tx["to_address"]

    # Force a deterministic cross-contract deploy capture for this call tx.
    engine = client.app.state.engine
    original_call_from_calldata = engine.call_from_calldata
    synthetic_deploy_addrs = [
        "0x" + "aa" * 20,
        "0x" + "bb" * 20,
        "0x" + "cc" * 20,
    ]

    def patched_call_from_calldata(contract_address, calldata_bytes, sender=None):
        result = original_call_from_calldata(contract_address, calldata_bytes, sender)
        engine._captured_triggered_ops = [
            {"type": "deploy", "address": addr} for addr in synthetic_deploy_addrs
        ]
        return result

    engine.call_from_calldata = patched_call_from_calldata
    try:
        call_calldata = calldata.encode({
            "method": "update_storage",
            "args": ["updated"],
            "kwargs": {},
        })
        call_data = _build_add_transaction_data(
            acct.address,
            contract_addr,
            call_calldata,
            is_deploy=False,
        )
        call_resp = _sign_and_send(
            client,
            acct,
            "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",
            call_data,
        )
    finally:
        engine.call_from_calldata = original_call_from_calldata

    call_eth_hash = call_resp["result"]
    call_receipt = _rpc(client, "eth_getTransactionReceipt", [call_eth_hash])["result"]
    call_gl_id = call_receipt["logs"][0]["topics"][1]
    parent_tx = _rpc(client, "eth_getTransactionByHash", [call_gl_id])["result"]

    # Factory-style parent should reference exactly one primary triggered deployment tx.
    assert "triggered_transactions" in parent_tx
    assert len(parent_tx["triggered_transactions"]) == 1
    campaign_like_tx_hash = parent_tx["triggered_transactions"][0]

    campaign_like_tx = _rpc(client, "eth_getTransactionByHash", [campaign_like_tx_hash])["result"]
    assert campaign_like_tx is not None
    assert campaign_like_tx["status"] == "FINALIZED"
    assert campaign_like_tx["to_address"] == synthetic_deploy_addrs[0]

    # Remaining deploys are exposed as second-level triggered transactions.
    assert len(campaign_like_tx["triggered_transactions"]) == 2
    lr = campaign_like_tx["consensus_data"]["leader_receipt"][0]
    assert lr["pending_transactions"] == campaign_like_tx["triggered_transactions"]

    for triggered_hash, expected_addr in zip(
        campaign_like_tx["triggered_transactions"],
        synthetic_deploy_addrs[1:],
        strict=False,
    ):
        triggered_tx = _rpc(client, "eth_getTransactionByHash", [triggered_hash])["result"]
        assert triggered_tx is not None
        assert triggered_tx["status"] == "FINALIZED"
        assert triggered_tx["to_address"] == expected_addr


def test_eth_get_block_by_number_latest(client):
    """eth_getBlockByNumber returns latest block in Ethereum-compatible shape."""
    block = _rpc(client, "eth_getBlockByNumber", ["latest", False])["result"]
    assert block is not None
    assert block["number"] == "0x0"
    assert block["transactions"] == []
    # Legacy fee mode for compatibility with nodes that don't expose EIP-1559 fields.
    assert block["baseFeePerGas"] is None


def test_eth_get_block_by_number_contains_tx_hash(client):
    """eth_getBlockByNumber should include tx hashes for committed blocks."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()
    data = _build_add_transaction_data(
        acct.address,
        "0x" + "00" * 20,
        code,
        is_deploy=True,
        constructor_args=["test_value"],
    )

    send_resp = _sign_and_send(
        client,
        acct,
        "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",
        data,
    )
    eth_tx_hash = send_resp["result"]

    latest_block = _rpc(client, "eth_getBlockByNumber", ["latest", False])["result"]
    assert latest_block is not None
    assert eth_tx_hash in latest_block["transactions"]

    block_by_number = _rpc(client, "eth_getBlockByNumber", [latest_block["number"], False])["result"]
    assert block_by_number is not None
    assert eth_tx_hash in block_by_number["transactions"]


def test_eth_get_transaction_receipt_has_new_transaction_event(client):
    """Receipt must have NewTransaction log with gl_tx_id in topics."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True, constructor_args=["test_value"])
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    assert receipt is not None
    assert receipt["status"] == "0x1"
    assert receipt["transactionHash"] == eth_tx_hash
    assert len(receipt["logs"]) == 1

    log = receipt["logs"][0]
    assert log["address"] == "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575"
    assert len(log["topics"]) == 4
    # topics[0] = NewTransaction event sig
    assert log["topics"][0].startswith("0x")
    # topics[1] = gl_tx_id (bytes32)
    gl_tx_id_hex = log["topics"][1]
    gl_tx_id = int(gl_tx_id_hex, 16)
    assert gl_tx_id > 0


def test_eth_get_transaction_by_hash_localnet_format(client):
    """eth_getTransactionByHash must return Studio localnet format."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True, constructor_args=["test_value"])
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    # Get gl_tx_id from receipt
    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]

    # Query transaction by gl_tx_id
    tx = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    assert tx is not None
    assert tx["status"] == "FINALIZED"
    assert tx["from_address"].lower() == acct.address.lower()
    assert tx["type"] == 0  # deploy

    # Must have consensus_data
    cd = tx["consensus_data"]
    assert "leader_receipt" in cd
    assert len(cd["leader_receipt"]) == 1
    assert cd["leader_receipt"][0]["execution_result"] == "SUCCESS"
    assert cd["leader_receipt"][0]["mode"] == "leader"

    # Must have data.calldata (base64)
    assert "data" in tx
    assert "calldata" in tx["data"]


def test_full_deploy_and_call_flow(client):
    """Full SDK flow: deploy via raw tx, call via raw tx, read via gen_call."""
    acct = Account.create()

    # 1. Deploy
    code = Path(STORAGE_CONTRACT).read_bytes()
    deploy_data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True, constructor_args=["test_value"])
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", deploy_data)
    eth_tx_hash = resp["result"]

    # Get contract address from the transaction
    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]
    tx_data = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    contract_addr = tx_data["to_address"]
    assert contract_addr != "0x" + "00" * 20

    # 2. Read via gen_call
    read_calldata = calldata.encode({"method": "get_storage", "args": [], "kwargs": {}})
    rlp_data = "0x" + rlp_mod.encode([read_calldata, b"\x00"]).hex()

    gen_call_resp = _rpc(client, "gen_call", [{
        "type": "read",
        "to": contract_addr,
        "from": acct.address,
        "data": rlp_data,
    }])
    assert "result" in gen_call_resp
    result_hex = gen_call_resp["result"]
    # Decode the result
    decoded = calldata.decode(bytes.fromhex(result_hex))
    assert decoded == "test_value"


# ---------------------------------------------------------------------------
# gen_call
# ---------------------------------------------------------------------------

def test_gen_call_read(client):
    """gen_call reads a value from a deployed contract."""
    addr = _deploy_simple(client, "gen_call_test")

    read_calldata = calldata.encode({"method": "get_storage", "args": [], "kwargs": {}})
    rlp_data = "0x" + rlp_mod.encode([read_calldata, b"\x00"]).hex()

    resp = _rpc(client, "gen_call", [{
        "type": "read",
        "to": addr,
        "from": "0x" + "11" * 20,
        "data": rlp_data,
    }])
    assert "result" in resp
    decoded = calldata.decode(bytes.fromhex(resp["result"]))
    assert decoded == "gen_call_test"


# ---------------------------------------------------------------------------
# gen_getContractSchema
# ---------------------------------------------------------------------------

def test_gen_get_contract_schema(client):
    """gen_getContractSchema returns SDK ContractSchema format."""
    addr = _deploy_simple(client)

    resp = _rpc(client, "gen_getContractSchema", [addr])
    assert "result" in resp
    schema = resp["result"]

    # SDK ContractSchema format
    assert "ctor" in schema
    assert "methods" in schema
    assert "params" in schema["ctor"]
    assert "kwparams" in schema["ctor"]

    # Should have get_storage and update_storage
    assert "get_storage" in schema["methods"]
    assert "update_storage" in schema["methods"]

    get_method = schema["methods"]["get_storage"]
    assert "ret" in get_method
    assert "readonly" in get_method


def test_gen_get_contract_schema_for_code(client):
    """gen_getContractSchemaForCode extracts schema from hex-encoded source."""
    code = Path(STORAGE_CONTRACT).read_bytes()
    code_hex = "0x" + code.hex()

    resp = _rpc(client, "gen_getContractSchemaForCode", [code_hex])
    assert "result" in resp
    schema = resp["result"]
    assert "methods" in schema
    assert "get_storage" in schema["methods"]


# ---------------------------------------------------------------------------
# sim_fundAccount with positional params (SDK format)
# ---------------------------------------------------------------------------

def test_sim_fund_account_positional(client):
    """SDK sends sim_fundAccount with positional params [address, amount]."""
    addr = "0x" + "cc" * 20
    resp = _rpc(client, "sim_fundAccount", [addr, 9999])
    assert "result" in resp
    assert resp["result"]["balance"] == 9999


# ---------------------------------------------------------------------------
# eth_getTransactionReceipt for sim_deploy (backward compat)
# ---------------------------------------------------------------------------

def test_eth_receipt_for_sim_deploy(client):
    """eth_getTransactionReceipt should also work for sim_deploy transactions."""
    data = _rpc(client, "sim_deploy", {
        "code_path": STORAGE_CONTRACT,
        "args": ["hello"],
    })
    tx_hash = data["result"]["tx_hash"]

    # sim_getTransactionReceipt still works
    receipt = _rpc(client, "sim_getTransactionReceipt", {"transaction_hash": tx_hash})
    assert receipt["result"]["status"] == "0x1"

    # eth_getTransactionReceipt should also find it
    receipt2 = _rpc(client, "eth_getTransactionReceipt", [tx_hash])
    assert receipt2["result"] is not None
    assert receipt2["result"]["status"] == "0x1"


# ---------------------------------------------------------------------------
# contract_address in deploy response data (Gap 3)
# ---------------------------------------------------------------------------

def test_deploy_response_has_contract_address_in_data(client):
    """eth_getTransactionByHash for deploy must include data.contract_address."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True, constructor_args=["test_value"])
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]

    tx = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    # extract_contract_address() looks for data.contract_address
    assert "contract_address" in tx["data"]
    assert tx["data"]["contract_address"] == tx["to_address"]
    assert tx["data"]["contract_address"] != "0x" + "00" * 20


# ---------------------------------------------------------------------------
# Error handling (Gap 4) — contract error → FINALIZED + execution_result=ERROR
# ---------------------------------------------------------------------------

def test_call_error_returns_finalized_with_error(client):
    """Contract exception → tx is FINALIZED but execution_result=ERROR."""
    acct = Account.create()

    # Deploy the web contract (has fail_always method)
    code = Path(WEB_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    # Get contract address
    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]
    tx_data = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    contract_addr = tx_data["to_address"]

    # Call fail_always — should NOT return an RPC error
    call_calldata = calldata.encode({"method": "fail_always", "args": [], "kwargs": {}})
    call_data = _build_add_transaction_data(acct.address, contract_addr, call_calldata)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", call_data)
    # Must get eth_tx_hash back (not an error)
    assert "result" in resp, f"Expected eth_tx_hash, got error: {resp}"
    call_eth_hash = resp["result"]

    # Get receipt — status should still be 0x1 (tx was processed)
    call_receipt = _rpc(client, "eth_getTransactionReceipt", [call_eth_hash])["result"]
    assert call_receipt["status"] == "0x1"

    # Get transaction — should be FINALIZED but execution_result=ERROR
    call_gl_id = call_receipt["logs"][0]["topics"][1]
    call_tx = _rpc(client, "eth_getTransactionByHash", [call_gl_id])["result"]
    assert call_tx["status"] == "FINALIZED"
    lr = call_tx["consensus_data"]["leader_receipt"][0]
    assert lr["execution_result"] == "ERROR"
    assert "intentional failure" in lr["genvm_result"]["stderr"]


# ---------------------------------------------------------------------------
# Result bytes prefix format (Gap 2)
# ---------------------------------------------------------------------------

def test_result_bytes_have_status_prefix(client):
    """leader_receipt.result must have 0x00 prefix for success (calldata format)."""
    acct = Account.create()
    code = Path(STORAGE_CONTRACT).read_bytes()

    # Deploy
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True, constructor_args=["test_value"])
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]
    tx_data = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    contract_addr = tx_data["to_address"]

    # Call update_storage (write)
    call_calldata = calldata.encode({"method": "update_storage", "args": ["new_val"], "kwargs": {}})
    call_data = _build_add_transaction_data(acct.address, contract_addr, call_calldata)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", call_data)
    call_eth_hash = resp["result"]

    call_receipt = _rpc(client, "eth_getTransactionReceipt", [call_eth_hash])["result"]
    call_gl_id = call_receipt["logs"][0]["topics"][1]
    call_tx = _rpc(client, "eth_getTransactionByHash", [call_gl_id])["result"]

    lr = call_tx["consensus_data"]["leader_receipt"][0]
    result_b64 = lr["result"]
    if result_b64:
        result_bytes = base64.b64decode(result_b64)
        # First byte must be status code 0 (success)
        assert result_bytes[0] == 0, f"Expected status byte 0x00, got {result_bytes[0]:#x}"


def test_error_result_bytes_have_rollback_prefix(client):
    """leader_receipt.result for errors must have 0x01 prefix (rollback format)."""
    acct = Account.create()

    # Deploy web contract
    code = Path(WEB_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]
    tx_data = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    contract_addr = tx_data["to_address"]

    # Call fail_always
    call_calldata = calldata.encode({"method": "fail_always", "args": [], "kwargs": {}})
    call_data = _build_add_transaction_data(acct.address, contract_addr, call_calldata)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", call_data)
    call_eth_hash = resp["result"]

    call_receipt = _rpc(client, "eth_getTransactionReceipt", [call_eth_hash])["result"]
    call_gl_id = call_receipt["logs"][0]["topics"][1]
    call_tx = _rpc(client, "eth_getTransactionByHash", [call_gl_id])["result"]

    lr = call_tx["consensus_data"]["leader_receipt"][0]
    result_b64 = lr["result"]
    result_bytes = base64.b64decode(result_b64)
    # First byte must be 1 (rollback/error)
    assert result_bytes[0] == 1, f"Expected status byte 0x01, got {result_bytes[0]:#x}"
    # Remaining bytes are UTF-8 error message
    error_msg = result_bytes[1:].decode("utf-8")
    assert "intentional failure" in error_msg


# ---------------------------------------------------------------------------
# sim_config with mock_web_response (Gap 1)
# ---------------------------------------------------------------------------

def test_sim_config_mock_web_response(client):
    """eth_sendRawTransaction with sim_config installs web mocks."""
    acct = Account.create()

    # Deploy web contract
    code = Path(WEB_CONTRACT).read_bytes()
    data = _build_add_transaction_data(acct.address, "0x" + "00" * 20, code, is_deploy=True)
    resp = _sign_and_send(client, acct, "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575", data)
    eth_tx_hash = resp["result"]

    receipt = _rpc(client, "eth_getTransactionReceipt", [eth_tx_hash])["result"]
    gl_tx_id_hex = receipt["logs"][0]["topics"][1]
    tx_data = _rpc(client, "eth_getTransactionByHash", [gl_tx_id_hex])["result"]
    contract_addr = tx_data["to_address"]

    # Call fetch_data with sim_config that mocks the URL
    mock_url = "https://api.example.com/data"
    call_calldata = calldata.encode({"method": "fetch_data", "args": [mock_url], "kwargs": {}})
    call_rlp = _build_add_transaction_data(acct.address, contract_addr, call_calldata)

    # Build sim_config with mock_web_response
    sim_config = {
        "validators": [{
            "stake": 1,
            "provider": "test",
            "model": "test",
            "config": {},
            "plugin": "test",
            "plugin_config": {
                "mock_web_response": {
                    "nondet_web_request": {
                        mock_url: {
                            "method": "GET",
                            "status": 200,
                            "body": '{"value": "mocked_data"}',
                        }
                    }
                }
            },
        }],
    }

    # Sign and send with sim_config as second param
    w3 = Web3()
    tx = {
        "nonce": 0,
        "gasPrice": 0,
        "gas": 21000,
        "to": "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",
        "value": 0,
        "data": call_rlp,
        "chainId": 61999,
    }
    signed = acct.sign_transaction(tx)
    raw_hex = w3.to_hex(signed.raw_transaction)

    resp = _rpc(client, "eth_sendRawTransaction", [raw_hex, sim_config])
    assert "result" in resp, f"Expected eth_tx_hash, got: {resp}"

    # Verify the call succeeded (mock was used)
    call_eth_hash = resp["result"]
    call_receipt = _rpc(client, "eth_getTransactionReceipt", [call_eth_hash])["result"]
    call_gl_id = call_receipt["logs"][0]["topics"][1]
    call_tx = _rpc(client, "eth_getTransactionByHash", [call_gl_id])["result"]

    lr = call_tx["consensus_data"]["leader_receipt"][0]
    assert lr["execution_result"] == "SUCCESS", f"Expected SUCCESS, stderr: {lr['genvm_result']['stderr']}"

    # Read the result back
    read_calldata = calldata.encode({"method": "get_result", "args": [], "kwargs": {}})
    rlp_data = "0x" + rlp_mod.encode([read_calldata, b"\x00"]).hex()
    gen_resp = _rpc(client, "gen_call", [{
        "type": "read",
        "to": contract_addr,
        "from": acct.address,
        "data": rlp_data,
    }])
    decoded = calldata.decode(bytes.fromhex(gen_resp["result"]))
    assert decoded == "mocked_data"
