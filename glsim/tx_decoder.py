"""Transaction decoder for glsim.

Decodes raw signed Ethereum transactions and extracts GenLayer payloads
using the genlayer_py SDK decoders.
"""

from __future__ import annotations

import rlp
from eth_account import Account as EthAccount
from eth_utils.crypto import keccak
from genlayer_py.consensus.consensus_main.decoder import (  # type: ignore[import-untyped]
    decode_add_transaction_data,
)
from genlayer_py.abi import calldata  # type: ignore[import-untyped]


# addTransaction(address,address,uint256,uint256,bytes) selector
ADD_TX_SELECTOR = keccak(
    text="addTransaction(address,address,uint256,uint256,bytes)"
)[:4].hex()

# NewTransaction(bytes32,address,address) event topic
NEW_TRANSACTION_TOPIC = "0x" + keccak(
    text="NewTransaction(bytes32,address,address)"
).hex()

# Consensus main contract address (matches localnet chain config)
CONSENSUS_CONTRACT_ADDR = "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575"

# Zero address = deploy target
ADDRESS_ZERO = "0x" + "00" * 20


def decode_raw_transaction(raw_hex: str) -> dict:
    """Decode a raw signed Ethereum transaction.

    Returns dict with: from, to, data (bytes), nonce, value, gas, hash.
    """
    if raw_hex.startswith("0x"):
        raw_bytes = bytes.fromhex(raw_hex[2:])
    else:
        raw_bytes = bytes.fromhex(raw_hex)

    sender = EthAccount.recover_transaction(raw_hex)

    # Decode RLP fields (legacy tx: nonce, gasPrice, gas, to, value, data, v, r, s)
    decoded = rlp.decode(raw_bytes)
    nonce = int.from_bytes(decoded[0], "big") if decoded[0] else 0
    to_addr = "0x" + decoded[3].hex() if decoded[3] else None
    value = int.from_bytes(decoded[4], "big") if decoded[4] else 0
    data = decoded[5]

    tx_hash = "0x" + keccak(raw_bytes).hex()

    return {
        "from": sender,
        "to": to_addr,
        "data": data,
        "nonce": nonce,
        "value": value,
        "hash": tx_hash,
    }


def decode_genlayer_payload(input_data: bytes) -> dict:
    """Decode addTransaction ABI call data into GenLayer tx fields.

    The input_data is the 'data' field from the raw Ethereum transaction,
    which is ABI-encoded: addTransaction(sender, recipient, nValidators, maxRotations, txData).

    Uses genlayer_py decoders to further decode the inner RLP payload.

    Returns dict with:
        sender, recipient, n_validators, max_rotations,
        tx_type ("deploy"|"call"), decoded_tx_data,
        and for deploy: code (bytes), constructor_args
        and for call: call_data (decoded calldata dict)
    """
    hex_data = "0x" + input_data.hex()
    result = decode_add_transaction_data(hex_data)

    decoded_tx = result["tx_data"]["decoded"]
    tx_type = decoded_tx.get("type", "call") if decoded_tx else "call"

    return {
        "sender": result["sender_address"],
        "recipient": result["recipient_address"],
        "n_validators": result["num_of_initial_validators"],
        "max_rotations": result["max_rotations"],
        "tx_type": tx_type,
        "decoded_tx_data": decoded_tx,
        "raw_tx_data": bytes.fromhex(result["tx_data"]["encoded"][2:]),
    }


def decode_gen_call_data(hex_data: str) -> tuple:
    """Decode gen_call RLP data → (calldata_bytes, leader_only).

    The SDK sends: hex(rlp([calldata_bytes, leader_only_flag]))
    """
    if hex_data.startswith("0x"):
        raw = bytes.fromhex(hex_data[2:])
    else:
        raw = bytes.fromhex(hex_data)

    decoded = rlp.decode(raw)
    calldata_bytes = decoded[0]
    leader_only = decoded[1] == b"\x01" if len(decoded) > 1 else False
    return calldata_bytes, leader_only


def decode_calldata_bytes(raw: bytes) -> dict:
    """Decode ULEB128 calldata bytes → dict with method, args, kwargs.

    Uses genlayer_py.abi.calldata.decode().
    """
    decoded = calldata.decode(raw)
    if decoded is None:
        return {"method": None, "args": [], "kwargs": {}}

    # calldata.decode returns a dict like {"method": "name", "args": [...], "kwargs": {...}}
    # or for constructor: {"method": None, "args": [...], "kwargs": {...}}
    if isinstance(decoded, dict):
        return decoded
    return {"method": None, "args": [decoded], "kwargs": {}}


def encode_calldata_result(value) -> bytes:
    """Encode a Python value as calldata bytes."""
    return calldata.encode(value)


def encode_result_bytes(value) -> bytes:
    """Encode success result with status prefix: 0x00 + calldata.encode(value).

    This matches GenVM's result format expected by result_to_user_friendly_json().
    """
    return bytes([0]) + calldata.encode(value)


def encode_error_bytes(error_msg: str) -> bytes:
    """Encode error result with status prefix: 0x01 + error_msg as UTF-8.

    This matches GenVM's rollback/error format.
    """
    return bytes([1]) + error_msg.encode("utf-8")


def pad_address(addr: str) -> str:
    """Pad an address to 32 bytes (64 hex chars) for event topics."""
    if addr.startswith("0x"):
        addr = addr[2:]
    return addr.lower().zfill(64)
