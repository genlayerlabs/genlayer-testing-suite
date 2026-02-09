"""FastAPI JSON-RPC 2.0 server for glsim."""

from __future__ import annotations

import base64
import re
import traceback
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .state import StateStore, Transaction, TxStatus
from .engine import SimEngine
from .consensus import run_consensus
from .tx_decoder import (
    decode_raw_transaction,
    decode_genlayer_payload,
    decode_gen_call_data,
    decode_calldata_bytes,
    encode_calldata_result,
    encode_result_bytes,
    encode_error_bytes,
    pad_address,
    NEW_TRANSACTION_TOPIC,
    CONSENSUS_CONTRACT_ADDR,
    ADDRESS_ZERO,
)


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

def _ok(result: Any, req_id: Any) -> dict:
    return {"jsonrpc": "2.0", "result": result, "id": req_id}


def _error(code: int, message: str, req_id: Any = None) -> dict:
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": req_id}


# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
CONTRACT_ERROR = -32000  # application-level


# ---------------------------------------------------------------------------
# RPC method implementations
# ---------------------------------------------------------------------------

def _rpc_ping(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return "pong"


def _rpc_sim_deploy(state: StateStore, engine: SimEngine, params: dict) -> Any:
    code_path = params.get("code_path") or params.get(0)
    if not code_path:
        raise ValueError("code_path is required")

    args = params.get("args", [])
    kwargs = params.get("kwargs", {})
    sender = params.get("sender")

    deployer = sender or "0x0000000000000000000000000000000000000001"
    tx_hash = state.generate_tx_hash(f"deploy:{code_path}")
    tx = Transaction(
        hash=tx_hash,
        from_address=deployer,
        to_address=None,
        type="deploy",
        args=args,
        kwargs=kwargs,
        block_number=state.block_number + 1,
    )
    state.add_transaction(tx)

    try:
        contract_addr, _instance = engine.deploy(code_path, args, kwargs, sender)
        tx.status = TxStatus.FINALIZED
        tx.to_address = contract_addr
        tx.result = contract_addr
        state.next_block()
        return {"contract_address": contract_addr, "tx_hash": tx_hash}
    except Exception as exc:
        tx.status = TxStatus.FAILED
        tx.error = str(exc)
        state.next_block()
        raise


def _rpc_sim_call(state: StateStore, engine: SimEngine, params: dict) -> Any:
    to = params.get("to")
    method = params.get("method")
    if not to or not method:
        raise ValueError("'to' and 'method' are required")

    args = params.get("args", [])
    kwargs = params.get("kwargs", {})
    sender = params.get("sender")

    caller = sender or "0x0000000000000000000000000000000000000001"
    tx_hash = state.generate_tx_hash(f"call:{to}:{method}")
    tx = Transaction(
        hash=tx_hash,
        from_address=caller,
        to_address=to,
        type="call",
        method=method,
        args=args,
        kwargs=kwargs,
        block_number=state.block_number + 1,
    )
    state.add_transaction(tx)

    try:
        result = engine.call_method(to, method, args, kwargs, sender)
        tx.status = TxStatus.FINALIZED
        tx.result = result
        state.next_block()
        return {"result": result, "tx_hash": tx_hash}
    except Exception as exc:
        tx.status = TxStatus.FAILED
        tx.error = str(exc)
        state.next_block()
        raise


def _rpc_sim_read(state: StateStore, engine: SimEngine, params: dict) -> Any:
    to = params.get("to")
    method = params.get("method")
    if not to or not method:
        raise ValueError("'to' and 'method' are required")

    args = params.get("args", [])
    kwargs = params.get("kwargs", {})
    result = engine.call_method(to, method, args, kwargs)
    return {"result": result}


def _rpc_sim_fund_account(state: StateStore, engine: SimEngine, params: dict) -> Any:
    # SDK sends positional: [address, amount]
    address = params.get("account_address") or _positional(params, 0)
    amount = params.get("amount")
    if amount is None:
        amount = _positional(params, 1)
    if not address or amount is None:
        raise ValueError("'account_address' and 'amount' are required")
    state.fund_account(address, int(amount))
    return {"balance": state.get_balance(address)}


def _rpc_sim_get_balance(state: StateStore, engine: SimEngine, params: dict) -> Any:
    address = params.get("account_address")
    if not address:
        raise ValueError("'account_address' is required")
    return state.get_balance(address)


def _rpc_sim_get_tx_by_hash(state: StateStore, engine: SimEngine, params: dict) -> Any:
    tx_hash = params.get("transaction_hash")
    if not tx_hash:
        raise ValueError("'transaction_hash' is required")
    tx = state.get_transaction(tx_hash)
    if tx is None:
        return None
    return _tx_to_dict(tx)


def _rpc_sim_get_tx_receipt(state: StateStore, engine: SimEngine, params: dict) -> Any:
    tx_hash = params.get("transaction_hash")
    if not tx_hash:
        raise ValueError("'transaction_hash' is required")
    tx = state.get_transaction(tx_hash)
    if tx is None:
        return None
    status_hex = "0x1" if tx.status == TxStatus.FINALIZED else "0x0"
    receipt = {
        "transactionHash": tx.hash,
        "blockNumber": hex(tx.block_number),
        "status": status_hex,
        "from": tx.from_address,
        "to": tx.to_address,
        "contractAddress": tx.to_address if tx.type == "deploy" else None,
        "logs": [],
        "gasUsed": "0x5208",
        "cumulativeGasUsed": "0x5208",
    }
    if tx.consensus_data:
        receipt["consensus_data"] = tx.consensus_data
    if tx.error:
        receipt["error"] = tx.error
    return receipt


def _rpc_sim_get_contract_schema(state: StateStore, engine: SimEngine, params: dict) -> Any:
    address = params.get("contract_address")
    if not address:
        raise ValueError("'contract_address' is required")
    schema = engine.get_schema(address)
    if schema is None:
        raise ValueError(f"No contract at {address}")
    return schema


def _rpc_eth_chain_id(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return hex(state.chain_id)


def _rpc_net_version(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return str(state.chain_id)


def _rpc_eth_block_number(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return hex(state.block_number)


def _rpc_eth_get_balance(state: StateStore, engine: SimEngine, params: dict) -> Any:
    address = params.get("account_address") or _positional(params, 0)
    if not address:
        raise ValueError("address is required")
    bal = state.get_balance(address)
    return hex(bal)


def _rpc_eth_get_tx_count(state: StateStore, engine: SimEngine, params: dict) -> Any:
    address = params.get("address") or _positional(params, 0)
    if not address:
        raise ValueError("address is required")
    return hex(state.get_nonce(address))


def _rpc_eth_gas_price(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return "0x0"


def _rpc_eth_estimate_gas(state: StateStore, engine: SimEngine, params: dict) -> Any:
    return "0x5208"


# ---------------------------------------------------------------------------
# SDK-compatible RPC methods
# ---------------------------------------------------------------------------

def _rpc_eth_send_raw_transaction(state: StateStore, engine: SimEngine, params: dict) -> Any:
    raw_hex = _positional(params, 0)
    if not raw_hex:
        raise ValueError("raw transaction hex is required")

    # Extract optional sim_config (validators with mock_web_response)
    sim_config = _positional(params, 1)

    # Decode the raw Ethereum transaction
    eth_tx = decode_raw_transaction(raw_hex)
    eth_tx_hash = eth_tx["hash"]

    # Decode GenLayer payload from the tx input data
    gl_payload = decode_genlayer_payload(eth_tx["data"])
    decoded = gl_payload["decoded_tx_data"]
    tx_type = gl_payload["tx_type"]
    sender = gl_payload["sender"]
    recipient = gl_payload["recipient"]

    # Allocate GenLayer tx ID
    gl_tx_id = state.allocate_gl_tx_id()
    internal_hash = state.generate_tx_hash(f"gl:{gl_tx_id}")

    tx = Transaction(
        hash=internal_hash,
        from_address=sender,
        to_address=recipient if recipient != ADDRESS_ZERO else None,
        type=tx_type,
        block_number=state.block_number + 1,
        gl_tx_id=gl_tx_id,
        eth_tx_hash=eth_tx_hash,
        raw_sender=eth_tx["from"],
        num_validators=gl_payload["n_validators"],
    )
    state.add_transaction(tx)
    state.register_tx_mappings(tx)

    # Install web mocks from sim_config before executing
    _install_sim_config_mocks(engine, sim_config)

    if tx_type == "deploy":
        code_hex = decoded.get("code", "")
        code_bytes = bytes.fromhex(code_hex[2:]) if code_hex.startswith("0x") else code_hex.encode()
        constructor_args = decoded.get("constructor_args")
        calldata_bytes = b""
        if constructor_args:
            calldata_bytes = encode_calldata_result(constructor_args)
        tx.calldata_bytes = calldata_bytes

        def execute_fn():
            addr, _ = engine.deploy_from_code(code_bytes, calldata_bytes, sender)
            return addr, b""

        consensus = run_consensus(engine, execute_fn, engine.num_validators, engine.max_rotations)
        tx.status = consensus.status
        if consensus.error:
            tx.error = consensus.error
            tx.result_bytes = encode_error_bytes(consensus.error)
        else:
            tx.to_address = consensus.result
            tx.result = consensus.result
    else:
        # Call
        call_data = decoded.get("call_data")
        if call_data is None:
            _clear_sim_config_mocks(engine)
            state.next_block()
            raise ValueError("No calldata in transaction")
        calldata_bytes = encode_calldata_result(call_data)
        tx.calldata_bytes = calldata_bytes

        def execute_fn():
            result, _ = engine.call_from_calldata(recipient, calldata_bytes, sender)
            return result, encode_result_bytes(result)

        consensus = run_consensus(engine, execute_fn, engine.num_validators, engine.max_rotations)
        tx.status = consensus.status
        if consensus.error:
            tx.error = consensus.error
            tx.result_bytes = encode_error_bytes(consensus.error)
        else:
            tx.result = consensus.result
            tx.result_bytes = consensus.result_bytes

    tx.consensus_votes = _build_consensus_votes(consensus.votes, tx.num_validators)
    tx.consensus_rotation = consensus.rotation

    _clear_sim_config_mocks(engine)
    state.next_block()
    return eth_tx_hash


def _rpc_eth_get_transaction_receipt(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Ethereum-format receipt with NewTransaction event log.

    web3.py calls this internally from wait_for_transaction_receipt().
    The SDK extracts the gl_tx_id from the NewTransaction event topics.
    """
    tx_hash = _positional(params, 0) or params.get("transaction_hash")
    if not tx_hash:
        raise ValueError("transaction hash is required")

    # Look up by eth_tx_hash first, then by internal hash
    tx = state.get_tx_by_eth_hash(tx_hash)
    if tx is None:
        tx = state.get_transaction(tx_hash)
    if tx is None:
        return None

    status_hex = "0x1" if tx.status == TxStatus.FINALIZED else "0x0"
    block_hex = hex(tx.block_number)
    block_hash = "0x" + "00" * 32

    # Build NewTransaction event log
    gl_tx_id_topic = "0x" + tx.gl_tx_id.to_bytes(32, "big").hex()
    recipient_topic = "0x" + pad_address(tx.to_address or ADDRESS_ZERO)
    sender_topic = "0x" + pad_address(tx.raw_sender or tx.from_address)

    logs = [{
        "address": CONSENSUS_CONTRACT_ADDR,
        "blockNumber": block_hex,
        "blockHash": block_hash,
        "transactionHash": tx.eth_tx_hash or tx_hash,
        "transactionIndex": "0x0",
        "logIndex": "0x0",
        "removed": False,
        "topics": [
            NEW_TRANSACTION_TOPIC,
            gl_tx_id_topic,
            recipient_topic,
            sender_topic,
        ],
        "data": "0x",
    }] if tx.gl_tx_id else []

    return {
        "transactionHash": tx.eth_tx_hash or tx_hash,
        "transactionIndex": "0x0",
        "blockNumber": block_hex,
        "blockHash": block_hash,
        "cumulativeGasUsed": "0x5208",
        "gasUsed": "0x5208",
        "status": status_hex,
        "from": tx.raw_sender or tx.from_address,
        "to": CONSENSUS_CONTRACT_ADDR,
        "contractAddress": None,
        "logs": logs,
        "logsBloom": "0x" + "00" * 256,
    }


def _rpc_eth_get_transaction_by_hash(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """GenLayer Studio localnet format for transaction data.

    SDK's get_transaction() calls this with gl_tx_id hex.
    Returns status as string name (e.g. "FINALIZED"), consensus_data with
    leader_receipt, data.calldata as base64.
    """
    tx_hash = _positional(params, 0) or params.get("transaction_hash")
    if not tx_hash:
        raise ValueError("transaction hash is required")

    # Try to parse as gl_tx_id (hex number)
    tx = None
    try:
        gl_id = int(tx_hash, 16) if isinstance(tx_hash, str) else tx_hash
        tx = state.get_tx_by_gl_id(gl_id)
    except (ValueError, TypeError):
        pass

    # Fall back to eth_tx_hash or internal hash
    if tx is None:
        tx = state.get_tx_by_eth_hash(tx_hash)
    if tx is None:
        tx = state.get_transaction(tx_hash)
    if tx is None:
        return None

    # Encode calldata as base64 for the response
    calldata_b64 = base64.b64encode(tx.calldata_bytes).decode() if tx.calldata_bytes else ""
    result_b64 = base64.b64encode(tx.result_bytes).decode() if tx.result_bytes else ""

    # Build consensus_data
    node_config = {
        "address": "0x" + "00" * 20,
        "provider": "glsim",
        "model": "direct",
        "config": {},
        "plugin": "glsim",
        "plugin_config": {},
        "stake": 1,
    }

    execution_result = "ERROR" if tx.error else "SUCCESS"
    leader_receipt = {
        "execution_result": execution_result,
        "mode": "leader",
        "calldata": calldata_b64,
        "result": result_b64,
        "eq_outputs": {},
        "genvm_result": {"stdout": "", "stderr": tx.error or ""},
        "contract_state": {},
        "pending_transactions": [],
        "gas_used": 0,
        "vote": None,
        "node_config": node_config,
    }

    validators = []
    votes = {}
    if tx.consensus_votes:
        # Real consensus data from consensus simulation
        for v_addr, vote in tx.consensus_votes.items():
            validators.append({
                **leader_receipt,
                "mode": "validator",
                "vote": vote,
                "node_config": {**node_config, "address": v_addr},
            })
        votes = dict(tx.consensus_votes)
    else:
        # Synthetic fallback for sim_deploy/sim_call paths
        for i in range(tx.num_validators):
            v_addr = f"0x{i:040x}"
            validators.append({
                **leader_receipt,
                "mode": "validator",
                "vote": "agree" if tx.status == TxStatus.FINALIZED else None,
                "node_config": {**node_config, "address": v_addr},
            })
            if tx.status == TxStatus.FINALIZED:
                votes[v_addr] = "agree"

    consensus_data = {
        "leader_receipt": [leader_receipt],
        "validators": validators,
        "votes": votes,
    }

    status_name = tx.status.value  # "FINALIZED", "PENDING", "FAILED"
    tx_type = 0 if tx.type == "deploy" else 2

    now = datetime.now(timezone.utc).isoformat()

    return {
        "hash": tx_hash,
        "status": status_name,
        "from_address": tx.from_address,
        "to_address": tx.to_address or ADDRESS_ZERO,
        "type": tx_type,
        "nonce": 0,
        "value": 0,
        "gaslimit": 0,
        "r": 0,
        "s": 0,
        "v": 0,
        "created_at": now,
        "data": {
            "calldata": calldata_b64,
            **({"contract_address": tx.to_address} if tx.type == "deploy" else {}),
        },
        "consensus_data": consensus_data,
    }


def _rpc_gen_call(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Read-only contract call (SDK's read_contract).

    SDK sends: params=[{"type": "read", "to": addr, "from": sender, "data": hex_rlp}]
    Returns: hex-encoded calldata result WITHOUT 0x prefix.
    """
    req = _positional(params, 0)
    if not req or not isinstance(req, dict):
        raise ValueError("params must be [{type, to, from, data}]")

    to = req.get("to")
    data_hex = req.get("data")
    sender = req.get("from")
    sim_config = req.get("sim_config")

    if not to or not data_hex:
        raise ValueError("'to' and 'data' are required")

    # Decode RLP: [calldata_bytes, leader_only_flag]
    calldata_bytes, _leader_only = decode_gen_call_data(data_hex)

    # Decode calldata and call
    cd = decode_calldata_bytes(calldata_bytes)
    method = cd.get("method")
    args = cd.get("args", [])
    kwargs = cd.get("kwargs", {})

    if not method:
        raise ValueError("No method in calldata")

    _install_sim_config_mocks(engine, sim_config)
    try:
        result = engine.call_method(to, method, args, kwargs, sender)
    finally:
        _clear_sim_config_mocks(engine)

    # Encode result as calldata and return hex WITHOUT 0x prefix
    result_bytes = encode_calldata_result(result)
    return result_bytes.hex()


def _rpc_gen_get_contract_schema(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Get contract schema in SDK ContractSchema format."""
    address = _positional(params, 0) or params.get("contract_address")
    if not address:
        raise ValueError("contract address is required")

    schema = engine.get_sdk_schema(address)
    if schema is None:
        raise ValueError(f"No contract at {address}")
    return schema


def _rpc_gen_get_contract_schema_for_code(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Get contract schema from hex-encoded source code."""
    code_hex = _positional(params, 0)
    if not code_hex:
        raise ValueError("hex-encoded contract code is required")

    if code_hex.startswith("0x"):
        code_bytes = bytes.fromhex(code_hex[2:])
    else:
        code_bytes = bytes.fromhex(code_hex)

    return engine.get_sdk_schema_for_code(code_bytes)


def _rpc_sim_call_sdk(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """SDK-format sim_call (simulate_write_contract).

    SDK sends: params=[{"type": "write", "to": addr, "from": sender, "data": hex_rlp}]
    """
    req = _positional(params, 0)
    if isinstance(req, dict) and "to" in req and "data" in req:
        to = req.get("to")
        data_hex = req.get("data")
        sender = req.get("from")
        sim_config = req.get("sim_config")

        calldata_bytes, _leader_only = decode_gen_call_data(data_hex)
        cd = decode_calldata_bytes(calldata_bytes)
        method = cd.get("method")
        args = cd.get("args", [])
        kwargs = cd.get("kwargs", {})

        if not method:
            raise ValueError("No method in calldata")

        _install_sim_config_mocks(engine, sim_config)
        try:
            result = engine.call_method(to, method, args, kwargs, sender)
        finally:
            _clear_sim_config_mocks(engine)
        result_bytes = encode_calldata_result(result)

        # Return a simplified transaction receipt
        calldata_b64 = base64.b64encode(calldata_bytes).decode()
        result_b64 = base64.b64encode(result_bytes).decode()
        return {
            "status": "FINALIZED",
            "result": result,
            "consensus_data": {
                "leader_receipt": [{
                    "execution_result": "SUCCESS",
                    "calldata": calldata_b64,
                    "result": result_b64,
                }],
            },
        }

    # Fall through to existing sim_call format
    return _rpc_sim_call(state, engine, params)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

def _rpc_sim_create_snapshot(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Create a state snapshot, return snapshot ID."""
    return engine.create_snapshot()


def _rpc_sim_restore_snapshot(state: StateStore, engine: SimEngine, params: dict) -> Any:
    """Restore state to a snapshot. Returns True on success."""
    snapshot_id = _positional(params, 0)
    if snapshot_id is None:
        raise ValueError("snapshot_id is required")
    return engine.restore_snapshot(snapshot_id)


RPC_METHODS = {
    "ping": _rpc_ping,
    # Simple sim_* methods (test helpers / direct access)
    "sim_deploy": _rpc_sim_deploy,
    "sim_call": _rpc_sim_call_sdk,  # SDK-compatible sim_call with fallback
    "sim_read": _rpc_sim_read,
    "sim_fundAccount": _rpc_sim_fund_account,
    "sim_getBalance": _rpc_sim_get_balance,
    "sim_getTransactionByHash": _rpc_sim_get_tx_by_hash,
    "sim_getTransactionReceipt": _rpc_sim_get_tx_receipt,
    "sim_getContractSchema": _rpc_sim_get_contract_schema,
    "sim_createSnapshot": _rpc_sim_create_snapshot,
    "sim_restoreSnapshot": _rpc_sim_restore_snapshot,
    # Ethereum-compatible RPCs
    "eth_chainId": _rpc_eth_chain_id,
    "net_version": _rpc_net_version,
    "eth_blockNumber": _rpc_eth_block_number,
    "eth_getBalance": _rpc_eth_get_balance,
    "eth_getTransactionCount": _rpc_eth_get_tx_count,
    "eth_gasPrice": _rpc_eth_gas_price,
    "eth_estimateGas": _rpc_eth_estimate_gas,
    "eth_sendRawTransaction": _rpc_eth_send_raw_transaction,
    "eth_getTransactionReceipt": _rpc_eth_get_transaction_receipt,
    "eth_getTransactionByHash": _rpc_eth_get_transaction_by_hash,
    # GenLayer-specific RPCs
    "gen_call": _rpc_gen_call,
    "gen_getContractSchema": _rpc_gen_get_contract_schema,
    "gen_getContractSchemaForCode": _rpc_gen_get_contract_schema_for_code,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _positional(params: dict, idx: int) -> Any:
    """Get positional param from a dict that may have integer keys."""
    return params.get(idx)


def _install_sim_config_mocks(engine: SimEngine, sim_config: dict | None) -> None:
    """Extract mock_web_response and mock_llm_response from sim_config validators."""
    if not sim_config or not isinstance(sim_config, dict):
        return
    validators = sim_config.get("validators")
    if not validators or not isinstance(validators, list):
        return
    # Use first validator's mocks (all validators share same mocks)
    pc = validators[0].get("plugin_config", {})
    # Web mocks
    web_mocks = pc.get("mock_web_response", {}).get("nondet_web_request", {})
    for url, resp_data in web_mocks.items():
        engine.vm.mock_web(re.escape(url), resp_data)
    # LLM mocks
    llm_mocks = pc.get("mock_response", {}).get("response", {})
    for prompt_key, response_text in llm_mocks.items():
        engine.vm.mock_llm(prompt_key, response_text)


def _build_consensus_votes(votes: list, num_validators: int) -> dict:
    """Convert vote list to {address: vote} dict."""
    result = {}
    for i, vote in enumerate(votes):
        v_addr = f"0x{i:040x}"
        result[v_addr] = vote
    return result


def _clear_sim_config_mocks(engine: SimEngine) -> None:
    """Clear any mocks installed from sim_config."""
    engine.vm._web_mocks.clear()
    engine.vm._web_mocks_hit.clear()
    engine.vm._llm_mocks.clear()
    engine.vm._llm_mocks_hit.clear()


def _tx_to_dict(tx: Transaction) -> dict:
    d = asdict(tx)
    d["status"] = tx.status.value
    return d


def _normalize_params(params) -> dict:
    """Convert list params to dict with integer keys, pass dicts through."""
    if params is None:
        return {}
    if isinstance(params, list):
        return {i: v for i, v in enumerate(params)}
    return params


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(
    num_validators: int = 1,
    max_rotations: int = 3,
    llm_provider: str | None = None,
    use_browser: bool = False,
    verbose: bool = False,
) -> FastAPI:
    """Create and configure the glsim FastAPI app."""

    web_handler = None
    llm_handler = None
    try:
        from .live_io import create_web_handler, create_llm_handler
        web_handler = create_web_handler(use_browser=use_browser)
        llm_handler = create_llm_handler(provider_config=llm_provider)
    except ImportError:
        pass

    state = StateStore()
    engine = SimEngine(state, web_handler=web_handler, llm_handler=llm_handler)
    engine.num_validators = num_validators
    engine.max_rotations = max_rotations

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine.activate()
        yield
        engine.deactivate()

    app = FastAPI(title="glsim", version="0.1.0", lifespan=lifespan)
    app.state.store = state
    app.state.engine = engine
    app.state.verbose = verbose

    # -- Health endpoint --
    @app.get("/health")
    async def health():
        return {"status": "ok", "block_number": state.block_number}

    # -- JSON-RPC endpoint --
    @app.post("/api")
    async def json_rpc(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(_error(PARSE_ERROR, "Parse error"))

        # Batch support
        if isinstance(body, list):
            results = [_handle_single(body_item, state, engine, verbose) for body_item in body]
            return JSONResponse(results)

        return JSONResponse(_handle_single(body, state, engine, verbose))

    return app


def _handle_single(body: dict, state: StateStore, engine: SimEngine, verbose: bool) -> dict:
    req_id = body.get("id")

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or "method" not in body:
        return _error(INVALID_REQUEST, "Invalid JSON-RPC 2.0 request", req_id)

    method_name = body["method"]
    handler = RPC_METHODS.get(method_name)
    if handler is None:
        return _error(METHOD_NOT_FOUND, f"Method not found: {method_name}", req_id)

    params = _normalize_params(body.get("params"))

    try:
        result = handler(state, engine, params)
        return _ok(result, req_id)
    except (ValueError, AttributeError, FileNotFoundError) as exc:
        return _error(CONTRACT_ERROR, str(exc), req_id)
    except Exception as exc:
        if verbose:
            traceback.print_exc()
        return _error(INTERNAL_ERROR, str(exc), req_id)


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------

def run_server(app: FastAPI, host: str = "127.0.0.1", port: int = 4000) -> None:
    """Run the glsim server with uvicorn."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
