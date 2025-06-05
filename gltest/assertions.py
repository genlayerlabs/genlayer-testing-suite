import re
from typing import Optional
from genlayer_py.types import GenLayerTransaction


def tx_execution_succeeded(
    result: GenLayerTransaction,
    match_std_out: Optional[str] = None,
    match_std_err: Optional[str] = None,
) -> bool:
    if "consensus_data" not in result:
        return False
    if "leader_receipt" not in result["consensus_data"]:
        return False
    if len(result["consensus_data"]["leader_receipt"]) == 0:
        return False

    leader_receipt = result["consensus_data"]["leader_receipt"][0]

    if "execution_result" not in leader_receipt:
        return False

    execution_result = leader_receipt["execution_result"]

    if execution_result != "SUCCESS":
        return False

    if match_std_out is not None or match_std_err is not None:
        if "genvm_result" not in leader_receipt:
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
