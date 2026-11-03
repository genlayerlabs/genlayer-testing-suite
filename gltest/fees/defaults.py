from typing import Any, Dict, List, Optional

from eth_account.signers.local import LocalAccount
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains.utils import is_studio_chain
from genlayer_py.contracts.utils import make_calldata_object
from genlayer_py.exceptions import GenLayerError
from genlayer_py.types import SimConfig
from web3.constants import ADDRESS_ZERO

from gltest.types import CalldataEncodable


def fees_are_unspecified(
    fees: Optional[Dict[str, Any]], fee_value: Optional[int]
) -> bool:
    return fees is None and fee_value is None


_POLICY_CACHE_ATTR = "_gltest_default_fees"


def _is_missing_fee_policy_rpc(error: GenLayerError) -> bool:
    cause = str(error.__cause__ or error).lower()
    return "-32601" in cause or "method not found" in cause


def _policy_default_fees(client) -> Optional[Dict[str, Any]]:
    """Return the generic estimate, or None when the backend charges no fees."""
    if hasattr(client, _POLICY_CACHE_ATTR):
        return getattr(client, _POLICY_CACHE_ATTR)
    try:
        estimate = client.estimate_transaction_fees()
    except GenLayerError as error:
        # Backends without sim_getFeeConfig predate fee admission.
        if not _is_missing_fee_policy_rpc(error):
            raise
        estimate = {"policy": {"enabled": False}}
    fees = None
    if estimate.get("policy", {}).get("enabled", True):
        fees = {
            "distribution": estimate["distribution"],
            "feeValue": estimate["feeValue"],
        }
    setattr(client, _POLICY_CACHE_ATTR, fees)
    return fees


def _fees_from_estimate(estimate: Dict[str, Any]) -> Dict[str, Any]:
    distribution = estimate.get("distribution")
    fee_value = estimate.get("feeValue", estimate.get("fee_value"))
    if not isinstance(distribution, dict) or fee_value is None:
        raise GenLayerError("fee estimator returned no recommended preset")
    fees = {"distribution": distribution, "feeValue": fee_value}
    allocations = estimate.get(
        "messageAllocations", estimate.get("message_allocations")
    )
    if allocations is not None:
        fees["messageAllocations"] = allocations
    return fees


def _is_simulation_execution_failure(error: Exception) -> bool:
    return "execution failed" in str(error).lower()


def default_deploy_fees(
    client,
    *,
    code: str,
    account: Optional[LocalAccount],
    args: Optional[List[CalldataEncodable]],
    leader_only: bool,
    sim_config: Optional[SimConfig],
) -> Optional[Dict[str, Any]]:
    """Quote a deploy the caller submitted without fees."""
    policy_fees = _policy_default_fees(client)
    if policy_fees is None:
        return None
    sender = account or client.local_account
    request: Dict[str, Any] = {
        "type": "deploy",
        "to": ADDRESS_ZERO,
        "from": sender.address,
        "data": serialize(
            [
                code,
                calldata.encode(
                    make_calldata_object(method=None, args=args, kwargs=None)
                ),
                leader_only,
            ]
        ),
    }
    if sim_config is not None:
        request["sim_config"] = sim_config
    try:
        result = client.provider.make_request(
            method="sim_estimateTransactionFees", params=[request]
        )["result"]
        return _fees_from_estimate((result or {}).get("recommendedPreset") or {})
    except Exception as error:
        # A deploy expected to fail must still be submitted so its receipt can be asserted.
        if not _is_simulation_execution_failure(error):
            raise
        return policy_fees


def default_write_fees(
    client,
    *,
    address: str,
    function_name: str,
    account: Optional[LocalAccount],
    args: Optional[List[CalldataEncodable]],
    value: int,
    leader_only: bool,
    sim_config: Optional[SimConfig],
) -> Optional[Dict[str, Any]]:
    """Quote a write the caller submitted without fees."""
    policy_fees = _policy_default_fees(client)
    if policy_fees is None:
        return None
    if not is_studio_chain(client.chain):
        return policy_fees
    try:
        estimate = client.estimate_transaction_fees_for_write(
            address=address,
            function_name=function_name,
            account=account,
            args=args,
            value=value,
            leader_only=leader_only,
            sim_config=sim_config,
        )
        return _fees_from_estimate(estimate)
    except Exception as error:
        if not _is_simulation_execution_failure(error):
            raise
        return policy_fees
