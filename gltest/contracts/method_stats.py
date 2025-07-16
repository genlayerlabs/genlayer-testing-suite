from dataclasses import dataclass
from typing import List, Any, Optional, Dict
import json
from pathlib import Path
from .utils import safe_filename


@dataclass
class MethodStatsSummary:
    """Statistical analysis results for a contract method execution."""

    method: str
    args: List[Any]
    total_runs: int
    executed_runs: int
    server_error_runs: int
    failed_runs: int
    successful_runs: int
    unique_states: int
    most_common_state_count: int
    reliability_score: float
    execution_time: float
    provider: str
    model: str

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100

    def __str__(self) -> str:
        """Format the statistical analysis results."""
        return f"""Method analysis summary
---------------------------
Method: {self.method}
Args: {self.args}
Provider: {self.provider}
Model: {self.model}
Total runs: {self.total_runs}
Server error runs: {self.server_error_runs}
Method executed runs: {self.executed_runs}
Method successful runs: {self.successful_runs}
Method failed runs: {self.failed_runs}
Unique states: {self.unique_states}
Reliability score: {self.reliability_score:.2f}% ({self.most_common_state_count}/{self.executed_runs} consistent)
Execution time: {self.execution_time:.1f}s"""


@dataclass
class StateGroup:
    """Represents a group of runs with the same contract state."""

    count: int
    state_hash: str


@dataclass
class FailedRun:
    """Represents a failed run with error details."""

    run: int
    error: str
    error_type: str  # "server" or "simulation"
    genvm_result: Optional[Dict[str, str]]


@dataclass
class MethodStatsDetailed:
    """Detailed statistical analysis results for a contract method execution."""

    method: str
    params: List[Any]
    timestamp: str
    configuration: Dict[str, Any]
    execution_time: float
    executed_runs: int
    failed_runs: int
    successful_runs: int
    server_error_runs: int
    most_common_state_count: int
    reliability_score: float
    sim_results: List[Any]
    unique_states: int
    state_groups: List[StateGroup]
    failed_runs_results: List[FailedRun]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "method": self.method,
            "params": self.params,
            "timestamp": self.timestamp,
            "configuration": self.configuration,
            "execution_time": self.execution_time,
            "method_executed_runs": self.executed_runs,
            "method_failed_runs": self.failed_runs,
            "method_successful_runs": self.successful_runs,
            "server_error_runs": self.server_error_runs,
            "most_common_state_count": self.most_common_state_count,
            "reliability_score": self.reliability_score,
            "unique_states": self.unique_states,
            "state_groups": [
                {"count": sg.count, "state_hash": sg.state_hash}
                for sg in self.state_groups
            ],
            "failed_runs": [
                {
                    "run": fr.run,
                    "error": fr.error,
                    "error_type": fr.error_type,
                    "genvm_result": fr.genvm_result,
                }
                for fr in self.failed_runs_results
            ],
            "simulation_results": self.filter_sim_results(),
        }

    def filter_sim_results(self) -> List[Any]:
        """Filter the simulation results to only include specific fields."""
        filtered_results = []
        allowed_fields = [
            "calldata",
            "contract_state",
            "eq_outputs",
            "execution_result",
            "genvm_result",
            "node_config",
            "pending_transactions",
            "result",
        ]

        for result in self.sim_results:
            filtered_result = {
                key: result.get(key) for key in allowed_fields if key in result
            }
            filtered_results.append(filtered_result)

        return filtered_results

    def save_to_directory(self, directory: str, filename: Optional[str] = None) -> str:
        """
        Save the detailed stats to a JSON file in the specified directory.

        Raises:
            OSError: If directory creation or file writing fails.
        """
        directory_path = Path(directory)
        directory_path.mkdir(parents=True, exist_ok=True)
        if filename is None:
            safe_method = safe_filename(self.method)
            safe_timestamp = safe_filename(self.timestamp)
            filename = f"{safe_method}_{safe_timestamp}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        filepath = directory_path / filename
        try:
            with open(filepath, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except (OSError, TypeError) as e:
            raise OSError(f"Failed to save stats to {filepath}: {e}") from e
        return str(filepath)
