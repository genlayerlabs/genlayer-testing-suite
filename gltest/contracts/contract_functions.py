from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
from gltest.types import TransactionStatus, TransactionHashVariant


@dataclass
class ContractFunction:
    method_name: str
    read_only: bool
    call_method: Optional[Callable] = None
    analyze_method: Optional[Callable] = None
    transact_method: Optional[Callable] = None

    def call(
        self,
        transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
    ):
        if not self.read_only:
            raise ValueError("call() not implemented for non-readonly method")
        return self.call_method(transaction_hash_variant=transaction_hash_variant)

    def transact(
        self,
        value: int = 0,
        consensus_max_rotations: Optional[int] = None,
        wait_transaction_status: TransactionStatus = TransactionStatus.ACCEPTED,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
        wait_triggered_transactions: bool = False,
        wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
    ):
        if self.read_only:
            raise ValueError("Cannot transact read-only method")
        return self.transact_method(
            value=value,
            consensus_max_rotations=consensus_max_rotations,
            wait_transaction_status=wait_transaction_status,
            wait_interval=wait_interval,
            wait_retries=wait_retries,
            wait_triggered_transactions=wait_triggered_transactions,
            wait_triggered_transactions_status=wait_triggered_transactions_status,
        )

    def analyze(
        self,
        provider: str,
        model: str,
        config: Optional[Dict[str, Any]] = None,
        plugin: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
        runs: int = 100,
    ):
        if self.read_only:
            raise ValueError("Cannot analyze read-only method")
        return self.analyze_method(
            provider=provider,
            model=model,
            config=config,
            plugin=plugin,
            plugin_config=plugin_config,
            runs=runs,
        )
