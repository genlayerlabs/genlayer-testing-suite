"""
Stats collector module for contract method analysis.

This module contains classes and functions to collect and analyze statistics
from contract method executions, simplifying the analyze_method implementation.
"""

import time
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from gltest.clients import get_gl_client
from gltest.types import CalldataEncodable
from .method_stats import StateGroup, FailedRun, MethodStatsDetailed, MethodStatsSummary
from gltest_cli.config.general import get_general_config
from gltest_cli.config.pytest_context import get_current_test_nodeid
from .utils import safe_filename


@dataclass
class SimulationConfig:
    """Configuration for simulation runs."""

    provider: str
    model: str
    config: Optional[Dict[str, Any]] = None
    plugin: Optional[str] = None
    plugin_config: Optional[Dict[str, Any]] = None


@dataclass
class SimulationResults:
    """Results from simulation runs."""

    sim_results: List[Dict[str, Any]]
    failed_runs: List[FailedRun]
    server_errors: int
    execution_time: float
    timestamp: str


class StatsCollector:
    """Collects and analyzes statistics for contract method executions."""

    def __init__(
        self,
        contract_address: str,
        method_name: str,
        account: Any,
        args: Optional[List[CalldataEncodable]] = None,
    ):
        self.contract_address = contract_address
        self.method_name = method_name
        self.account = account
        self.args = args or []
        self.client = get_gl_client()

    def run_simulations(
        self, sim_config: SimulationConfig, runs: int
    ) -> SimulationResults:
        """Execute multiple simulation runs and collect results."""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sim_results = []
        failed_runs_list = []
        server_errors = 0

        for run_idx in range(runs):
            try:
                sim_result = self._execute_single_simulation(sim_config)
                sim_results.append(sim_result)

                if sim_result.get("execution_result") != "SUCCESS":
                    failed_runs_list.append(
                        self._create_failed_run(run_idx, sim_result)
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

        return SimulationResults(
            sim_results=sim_results,
            failed_runs=failed_runs_list,
            server_errors=server_errors,
            execution_time=execution_time,
            timestamp=timestamp,
        )

    def _execute_single_simulation(
        self, sim_config: SimulationConfig
    ) -> Dict[str, Any]:
        """Execute a single simulation."""
        config_dict = {
            "provider": sim_config.provider,
            "model": sim_config.model,
        }

        if (
            sim_config.config is not None
            and sim_config.plugin is not None
            and sim_config.plugin_config is not None
        ):
            config_dict["config"] = sim_config.config
            config_dict["plugin"] = sim_config.plugin
            config_dict["plugin_config"] = sim_config.plugin_config

        return self.client.simulate_write_contract(
            address=self.contract_address,
            function_name=self.method_name,
            account=self.account,
            args=self.args,
            sim_config=config_dict,
        )

    def _create_failed_run(self, run_idx: int, sim_result: Dict[str, Any]) -> FailedRun:
        """Create a FailedRun object from a failed simulation result."""
        return FailedRun(
            run=run_idx,
            error=sim_result.get("error", "unknown error"),
            error_type="simulation",
            genvm_result={
                "stderr": sim_result.get("genvm_result", {}).get("stderr", ""),
                "stdout": sim_result.get("genvm_result", {}).get("stdout", ""),
            },
        )

    def analyze_results(
        self,
        sim_results: SimulationResults,
        runs: int,
        sim_config: SimulationConfig,
    ) -> MethodStatsSummary:
        """Analyze simulation results and generate statistics."""
        state_groups = self._analyze_states(sim_results.sim_results)

        executed_runs = runs - sim_results.server_errors
        successful_runs = sum(
            1
            for sim_receipt in sim_results.sim_results
            if sim_receipt.get("execution_result") == "SUCCESS"
        )

        most_common_count = max((group.count for group in state_groups), default=0)
        reliability_score = (
            (most_common_count / executed_runs) if executed_runs > 0 else 0.0
        )

        # Save detailed stats
        detailed_stats = self._create_detailed_stats(
            sim_results=sim_results,
            state_groups=state_groups,
            runs=runs,
            executed_runs=executed_runs,
            successful_runs=successful_runs,
            most_common_count=most_common_count,
            reliability_score=reliability_score,
            sim_config=sim_config,
        )
        self._save_detailed_stats(detailed_stats)

        # Return summary
        return MethodStatsSummary(
            method=self.method_name,
            args=self.args,
            total_runs=runs,
            server_error_runs=sim_results.server_errors,
            executed_runs=executed_runs,
            failed_runs=len(sim_results.failed_runs),
            successful_runs=successful_runs,
            unique_states=len(state_groups),
            most_common_state_count=most_common_count,
            reliability_score=reliability_score,
            execution_time=sim_results.execution_time,
            provider=sim_config.provider,
            model=sim_config.model,
        )

    def _analyze_states(self, sim_results: List[Dict[str, Any]]) -> List[StateGroup]:
        """Analyze contract states from simulation results."""
        state_counts = {}
        state_to_hash_str = {}

        for sim_receipt in sim_results:
            contract_state = sim_receipt.get("contract_state", {})
            state_json = json.dumps(contract_state, sort_keys=True)
            state_hash = hashlib.sha256(state_json.encode()).hexdigest()
            state_hash_str = f"0x{state_hash}"
            state_to_hash_str[state_hash] = state_hash_str
            state_counts[state_hash] = state_counts.get(state_hash, 0) + 1

        return [
            StateGroup(count=count, state_hash=state_to_hash_str[state_hash])
            for state_hash, count in sorted(
                state_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

    def _create_detailed_stats(
        self,
        sim_results: SimulationResults,
        state_groups: List[StateGroup],
        runs: int,
        executed_runs: int,
        successful_runs: int,
        most_common_count: int,
        reliability_score: float,
        sim_config: SimulationConfig,
    ) -> MethodStatsDetailed:
        """Create detailed statistics object."""
        configuration = {
            "runs": runs,
            "provider": sim_config.provider,
            "model": sim_config.model,
            "config": sim_config.config,
            "plugin": sim_config.plugin,
            "plugin_config": sim_config.plugin_config,
        }

        return MethodStatsDetailed(
            method=self.method_name,
            params=self.args,
            timestamp=sim_results.timestamp,
            configuration=configuration,
            execution_time=sim_results.execution_time,
            executed_runs=executed_runs,
            failed_runs=len(sim_results.failed_runs),
            successful_runs=successful_runs,
            server_error_runs=sim_results.server_errors,
            unique_states=len(state_groups),
            most_common_state_count=most_common_count,
            reliability_score=reliability_score,
            state_groups=state_groups,
            failed_runs_results=sim_results.failed_runs,
            sim_results=sim_results.sim_results,
        )

    def _save_detailed_stats(self, detailed_stats: MethodStatsDetailed) -> None:
        """Save detailed statistics to the configured directory."""
        general_config = get_general_config()
        current_nodeid = get_current_test_nodeid()
        if current_nodeid is None:
            safe_name = "no_test"
        else:
            safe_name = safe_filename(current_nodeid)
        stats_dir = general_config.get_analysis_dir() / safe_name
        detailed_stats.save_to_directory(stats_dir)
