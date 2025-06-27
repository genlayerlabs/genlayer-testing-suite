import types
import time
import json
import hashlib
from datetime import datetime, timezone
from eth_account.signers.local import LocalAccount
from dataclasses import dataclass
from gltest.clients import get_gl_client
from gltest.types import CalldataEncodable, GenLayerTransaction, TransactionStatus
from typing import List, Any, Optional, Dict, Callable
from gltest_cli.config.general import get_general_config
from gltest_cli.config.pytest_context import get_current_test_nodeid
from .contract_functions import ContractFunction
from .method_stats import (
    MethodStatsSummary,
    MethodStatsDetailed,
    StateGroup,
    FailedRun,
)
from .utils import safe_filename


def read_contract_wrapper(
    self,
    method_name: str,
    args: Optional[List[CalldataEncodable]] = None,
) -> Any:
    """
    Wrapper to the contract read method.
    """

    def call_method():
        client = get_gl_client()
        return client.read_contract(
            address=self.address,
            function_name=method_name,
            account=self.account,
            args=args,
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
    value: int = 0,
    consensus_max_rotations: Optional[int] = None,
    leader_only: bool = False,
    wait_transaction_status: TransactionStatus = TransactionStatus.FINALIZED,
    wait_interval: Optional[int] = None,
    wait_retries: Optional[int] = None,
    wait_triggered_transactions: bool = True,
    wait_triggered_transactions_status: TransactionStatus = TransactionStatus.FINALIZED,
) -> GenLayerTransaction:
    """
    Wrapper to the contract write method.
    """

    def transact_method():
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

    def stats_method(
        provider: str,
        model: str,
        config: Optional[Dict[str, Any]] = None,
        plugin: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
        runs: int = 100,
    ):
        """
        Analyze the contract method.
        """
        client = get_gl_client()

        start_time = time.time()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sim_results = []
        failed_runs_list = []
        server_errors = 0

        for run_idx in range(runs):
            try:
                sim_config = {
                    "provider": provider,
                    "model": model,
                }
                if (
                    config is not None
                    and plugin is not None
                    and plugin_config is not None
                ):
                    sim_config["config"] = config
                    sim_config["plugin"] = plugin
                    sim_config["plugin_config"] = plugin_config
                sim_receipt = client.simulate_write_contract(
                    address=self.address,
                    function_name=method_name,
                    account=self.account,
                    args=args,
                    sim_config=sim_config,
                )
                sim_results.append(sim_receipt)

                if sim_receipt.get("execution_result") != "SUCCESS":
                    failed_runs_list.append(
                        FailedRun(
                            run=run_idx,
                            error=sim_receipt.get("error", "unknown error"),
                            error_type="simulation",
                            genvm_result={
                                "stderr": sim_receipt.get("genvm_result", {}).get(
                                    "stderr", ""
                                ),
                                "stdout": sim_receipt.get("genvm_result", {}).get(
                                    "stdout", ""
                                ),
                            },
                        )
                    )
            except Exception as e:
                server_errors += 1
                failed_runs_list.append(
                    FailedRun(
                        run=run_idx,
                        error=str(e),
                        error_type="server",
                        genvm_result=None,
                    )
                )

        execution_time = time.time() - start_time

        state_counts = {}
        state_to_hash_str = {}

        for sim_receipt in sim_results:
            contract_state = sim_receipt.get("contract_state", {})
            state_json = json.dumps(contract_state, sort_keys=True)
            state_hash = hashlib.sha256(state_json.encode()).hexdigest()
            state_hash_str = f"0x{state_hash}"
            state_to_hash_str[state_hash] = state_hash_str
            state_counts[state_hash] = state_counts.get(state_hash, 0) + 1

        state_groups = [
            StateGroup(count=count, state_hash=state_to_hash_str[state_hash])
            for state_hash, count in sorted(
                state_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        executed_runs = runs - server_errors
        most_common_count = max(state_counts.values()) if state_counts else 0
        reliability_score = (
            (most_common_count / executed_runs) if executed_runs > 0 else 0.0
        )

        configuration = {
            "runs": runs,
            "provider": provider,
            "model": model,
            "config": config,
            "plugin": plugin,
            "plugin_config": plugin_config,
        }

        successful_runs = sum(
            1
            for sim_receipt in sim_results
            if sim_receipt.get("execution_result") == "SUCCESS"
        )

        detailed_stats = MethodStatsDetailed(
            method=method_name,
            params=args or [],
            timestamp=timestamp,
            configuration=configuration,
            execution_time=execution_time,
            executed_runs=executed_runs,
            failed_runs=len(failed_runs_list),
            successful_runs=successful_runs,
            server_error_runs=server_errors,
            unique_states=len(state_groups),
            most_common_state_count=most_common_count,
            reliability_score=reliability_score,
            state_groups=state_groups,
            failed_runs_results=failed_runs_list,
            sim_results=sim_results,
        )

        general_config = get_general_config()
        stats_dir = general_config.get_stats_dir() / safe_filename(
            get_current_test_nodeid()
        )
        detailed_stats.save_to_directory(stats_dir)

        return MethodStatsSummary(
            method=method_name,
            args=args or [],
            total_runs=runs,
            server_error_runs=server_errors,
            executed_runs=executed_runs,
            failed_runs=len(failed_runs_list),
            successful_runs=successful_runs,
            unique_states=len(state_groups),
            most_common_state_count=most_common_count,
            reliability_score=reliability_score,
            execution_time=execution_time,
            provider=provider,
            model=model,
        )

    return ContractFunction(
        method_name=method_name,
        read_only=False,
        transact_method=transact_method,
        stats_method=stats_method,
    )


def contract_function_factory(method_name: str, read_only: bool) -> Callable:
    """
    Create a function that interacts with a specific contract method.
    """
    if read_only:
        return lambda self, args=None: read_contract_wrapper(self, method_name, args)
    else:
        return lambda self, **kwargs: write_contract_wrapper(
            self, method_name, **kwargs
        )


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
