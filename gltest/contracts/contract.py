import types
from eth_account.signers.local import LocalAccount
from dataclasses import dataclass
from gltest.clients import get_gl_client
from gltest.types import (
    CalldataEncodable,
    GenLayerTransaction,
    TransactionStatus,
    TransactionHashVariant,
)
from typing import List, Any, Optional, Dict, Callable
from gltest_cli.config.general import get_general_config
from .contract_functions import ContractFunction
from .stats_collector import StatsCollector, SimulationConfig


def read_contract_wrapper(
    self,
    method_name: str,
    args: Optional[List[CalldataEncodable]] = None,
) -> Any:
    """
    Wrapper to the contract read method.
    """

    def call_method(
        transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
    ):
        client = get_gl_client()
        return client.read_contract(
            address=self.address,
            function_name=method_name,
            account=self.account,
            args=args,
            transaction_hash_variant=transaction_hash_variant,
        )

    return ContractFunction(
        method_name=method_name,
        read_only=True,
        call_method=call_method,
    )


def write_contract_wrapper(
    self,
    method_name: str,
    args: Optional[List[CalldataEncodable]] = None,
) -> GenLayerTransaction:
    """
    Wrapper to the contract write method.
    """

    def transact_method(
        value: int = 0,
        consensus_max_rotations: Optional[int] = None,
        wait_transaction_status: TransactionStatus = TransactionStatus.ACCEPTED,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
        wait_triggered_transactions: bool = False,
        wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
    ):
        """
        Transact the contract method.
        """
        general_config = get_general_config()
        actual_wait_interval = (
            wait_interval
            if wait_interval is not None
            else general_config.get_default_wait_interval()
        )
        actual_wait_retries = (
            wait_retries
            if wait_retries is not None
            else general_config.get_default_wait_retries()
        )
        leader_only = (
            general_config.get_leader_only()
            if general_config.check_studio_based_rpc()
            else False
        )
        client = get_gl_client()
        tx_hash = client.write_contract(
            address=self.address,
            function_name=method_name,
            account=self.account,
            value=value,
            consensus_max_rotations=consensus_max_rotations,
            leader_only=leader_only,
            args=args,
        )
        receipt = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash,
            status=wait_transaction_status,
            interval=actual_wait_interval,
            retries=actual_wait_retries,
        )
        if wait_triggered_transactions:
            triggered_transactions = receipt["triggered_transactions"]
            for triggered_transaction in triggered_transactions:
                client.wait_for_transaction_receipt(
                    transaction_hash=triggered_transaction,
                    status=wait_triggered_transactions_status,
                    interval=actual_wait_interval,
                    retries=actual_wait_retries,
                )
        return receipt

    def analyze_method(
        provider: str,
        model: str,
        config: Optional[Dict[str, Any]] = None,
        plugin: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
        runs: int = 100,
    ):
        """
        Analyze the contract method using StatsCollector.
        """
        collector = StatsCollector(
            contract_address=self.address,
            method_name=method_name,
            account=self.account,
            args=args,
        )
        sim_config = SimulationConfig(
            provider=provider,
            model=model,
            config=config,
            plugin=plugin,
            plugin_config=plugin_config,
        )
        sim_results = collector.run_simulations(sim_config, runs)
        return collector.analyze_results(sim_results, runs, sim_config)

    return ContractFunction(
        method_name=method_name,
        read_only=False,
        transact_method=transact_method,
        analyze_method=analyze_method,
    )


def contract_function_factory(method_name: str, read_only: bool) -> Callable:
    """
    Create a function that interacts with a specific contract method.
    """
    if read_only:
        return lambda self, args=None: read_contract_wrapper(self, method_name, args)
    return lambda self, args=None: write_contract_wrapper(self, method_name, args)


@dataclass
class Contract:
    """
    Class to interact with a contract, its methods
    are implemented dynamically at build time.
    """

    address: str
    account: Optional[LocalAccount] = None
    _schema: Optional[Dict[str, Any]] = None

    @classmethod
    def new(
        cls,
        address: str,
        schema: Dict[str, Any],
        account: Optional[LocalAccount] = None,
    ) -> "Contract":
        """
        Build the methods from the schema.
        """
        if not isinstance(schema, dict) or "methods" not in schema:
            raise ValueError("Invalid schema: must contain 'methods' field")
        instance = cls(address=address, _schema=schema, account=account)
        instance._build_methods_from_schema()
        return instance

    def _build_methods_from_schema(self):
        """
        Build the methods from the schema.
        """
        if self._schema is None:
            raise ValueError("No schema provided")
        for method_name, method_info in self._schema["methods"].items():
            if not isinstance(method_info, dict) or "readonly" not in method_info:
                raise ValueError(
                    f"Invalid method info for '{method_name}': must contain 'readonly' field"
                )
            method_func = contract_function_factory(
                method_name, method_info["readonly"]
            )
            bound_method = types.MethodType(method_func, self)
            setattr(self, method_name, bound_method)

    def connect(self, account: LocalAccount) -> "Contract":
        """
        Create a new instance of the contract with the same methods and a different account.
        """
        new_contract = self.__class__(
            address=self.address, account=account, _schema=self._schema
        )
        new_contract._build_methods_from_schema()
        return new_contract
