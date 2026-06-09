import re
from typing import Any, Optional
from genlayer_py.types import GenLayerTransaction

try:
    from genlayer_py.transactions import is_successful
except ImportError:
    is_successful = None


ACCEPTED_STATUSES = {"ACCEPTED", "FINALIZED", "5", "7"}
SUCCESS_RESULTS = {"FINISHED_WITH_RETURN", "1"}


def _string_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    enum_value = getattr(value, "value", value)
    return str(enum_value)


def _has_accepted_status(result: GenLayerTransaction) -> bool:
    status = _string_value(result.get("status_name", result.get("status")))
    return status in ACCEPTED_STATUSES


def _leader_receipt(result: GenLayerTransaction) -> Optional[dict]:
    consensus_data = result.get("consensus_data")
    if not isinstance(consensus_data, dict):
        return None
    leader_receipt = consensus_data.get("leader_receipt")
    if isinstance(leader_receipt, dict):
        return leader_receipt
    if not isinstance(leader_receipt, list) or len(leader_receipt) == 0:
        return None
    if not isinstance(leader_receipt[0], dict):
        return None
    return leader_receipt[0]


def _has_successful_execution(result: GenLayerTransaction) -> bool:
    if not _has_accepted_status(result):
        return False
    if is_successful is not None:
        try:
            if is_successful(result):
                return True
        except Exception:
            pass
    execution_result = _string_value(
        result.get("tx_execution_result_name", result.get("tx_execution_result"))
    )
    if execution_result in SUCCESS_RESULTS:
        return True
    leader_receipt = _leader_receipt(result)
    return (
        leader_receipt is not None
        and leader_receipt.get("execution_result") == "SUCCESS"
    )


def tx_execution_succeeded(
    result: GenLayerTransaction,
    match_std_out: Optional[str] = None,
    match_std_err: Optional[str] = None,
) -> bool:
    if not _has_successful_execution(result):
        return False

    if match_std_out is not None or match_std_err is not None:
        leader_receipt = _leader_receipt(result)
        if leader_receipt is None or "genvm_result" not in leader_receipt:
            return False

        genvm_result = leader_receipt["genvm_result"]

        if match_std_out is not None:
            if "stdout" not in genvm_result:
                return False
            try:
                if not re.search(match_std_out, genvm_result["stdout"]):
                    return False
            except re.error:
                return False

        if match_std_err is not None:
            if "stderr" not in genvm_result:
                return False
            try:
                if not re.search(match_std_err, genvm_result["stderr"]):
                    return False
            except re.error:
                return False
    return True


def tx_execution_failed(
    result: GenLayerTransaction,
    match_std_out: Optional[str] = None,
    match_std_err: Optional[str] = None,
) -> bool:
    return not tx_execution_succeeded(result, match_std_out, match_std_err)
