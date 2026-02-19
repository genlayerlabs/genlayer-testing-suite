"""In-memory state store for glsim.

Tracks accounts, deployed contracts, and transactions.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TxStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FINALIZED = "FINALIZED"
    UNDETERMINED = "UNDETERMINED"
    FAILED = "FAILED"


@dataclass
class Account:
    address: str
    balance: int = 0
    nonce: int = 0


@dataclass
class DeployedContract:
    address: str
    code_path: str
    instance: Any = None  # live contract object
    schema: Optional[Dict] = None


@dataclass
class Transaction:
    hash: str
    from_address: str
    to_address: Optional[str]
    status: TxStatus = TxStatus.PENDING
    type: str = "call"  # "deploy" | "call"
    method: Optional[str] = None
    args: List = field(default_factory=list)
    kwargs: Dict = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    block_number: int = 0
    consensus_data: Optional[Dict] = None
    # RPC compat fields
    gl_tx_id: int = 0
    eth_tx_hash: str = ""
    raw_sender: str = ""
    calldata_bytes: bytes = field(default=b"", repr=False)
    result_bytes: bytes = field(default=b"", repr=False)
    num_validators: int = 1
    consensus_votes: Dict[str, str] = field(default_factory=dict)
    consensus_rotation: int = 0
    triggered_transactions: List[str] = field(default_factory=list)


class StateStore:
    """In-memory state for the simulated network."""

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.contracts: Dict[str, DeployedContract] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.block_number: int = 0
        self.chain_id: int = 61999  # matches Studio default
        self._next_gl_tx_id: int = 1
        self._gl_to_hash: Dict[int, str] = {}
        self._eth_hash_to_hash: Dict[str, str] = {}

    def get_or_create_account(self, address: str) -> Account:
        addr = address.lower()
        if addr not in self.accounts:
            self.accounts[addr] = Account(address=addr)
        return self.accounts[addr]

    def fund_account(self, address: str, amount: int) -> None:
        acct = self.get_or_create_account(address)
        acct.balance += amount

    def get_balance(self, address: str) -> int:
        addr = address.lower()
        acct = self.accounts.get(addr)
        return acct.balance if acct else 0

    def register_contract(
        self, address: str, code_path: str, instance: Any, schema: Optional[Dict] = None
    ) -> DeployedContract:
        contract = DeployedContract(
            address=address.lower(),
            code_path=code_path,
            instance=instance,
            schema=schema,
        )
        self.contracts[address.lower()] = contract
        return contract

    def get_contract(self, address: str) -> Optional[DeployedContract]:
        return self.contracts.get(address.lower())

    def add_transaction(self, tx: Transaction) -> None:
        self.transactions[tx.hash] = tx

    def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return self.transactions.get(tx_hash)

    def next_block(self) -> int:
        self.block_number += 1
        return self.block_number

    def generate_tx_hash(self, data: str) -> str:
        h = hashlib.sha256(f"{data}:{time.time_ns()}".encode()).hexdigest()
        return f"0x{h}"

    def generate_contract_address(self, deployer: str, nonce: int) -> str:
        h = hashlib.sha256(f"{deployer}:{nonce}".encode()).hexdigest()[:40]
        return f"0x{h}"

    def get_nonce(self, address: str) -> int:
        acct = self.accounts.get(address.lower())
        return acct.nonce if acct else 0

    def increment_nonce(self, address: str) -> int:
        acct = self.get_or_create_account(address)
        acct.nonce += 1
        return acct.nonce

    def allocate_gl_tx_id(self) -> int:
        tx_id = self._next_gl_tx_id
        self._next_gl_tx_id += 1
        return tx_id

    def register_tx_mappings(self, tx: Transaction) -> None:
        """Register gl_tx_id and eth_tx_hash mappings for a transaction."""
        if tx.gl_tx_id:
            self._gl_to_hash[tx.gl_tx_id] = tx.hash
        if tx.eth_tx_hash:
            self._eth_hash_to_hash[tx.eth_tx_hash.lower()] = tx.hash

    def get_tx_by_gl_id(self, gl_tx_id: int) -> Optional[Transaction]:
        tx_hash = self._gl_to_hash.get(gl_tx_id)
        return self.transactions.get(tx_hash) if tx_hash else None

    def get_tx_by_eth_hash(self, eth_hash: str) -> Optional[Transaction]:
        tx_hash = self._eth_hash_to_hash.get(eth_hash.lower())
        return self.transactions.get(tx_hash) if tx_hash else None
