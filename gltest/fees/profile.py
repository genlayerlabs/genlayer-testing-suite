import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from gltest.logging import logger
from gltest_cli.config.general import get_general_config

FEE_KEYS = (
    "leaderTimeunitsAllocation",
    "validatorTimeunitsAllocation",
    "executionBudgetPerRound",
    "totalMessageFees",
    "rotationsPerRound",
)
CONSUMED_KEY_MAPPING = {
    "executionBudgetPerRound": "executionConsumed",
    "totalMessageFees": "messageFeesConsumed",
}
ALLOCATION_KEY_MAPPING = {
    "leaderTimeunitsAllocation": "leaderTimeunitsAllocation",
    "validatorTimeunitsAllocation": "validatorTimeunitsAllocation",
}


class FeeProfileCollector:
    def __init__(self):
        self._deploy: Dict[str, int] = {}
        self._methods: Dict[str, Dict[str, int]] = {}
        self._warned_malformed = False

    def record_deploy(self, receipt: Dict[str, Any]) -> None:
        observation = self._extract_observation(receipt)
        if observation is not None:
            self._record_max(self._deploy, observation)

    def record_method(self, method_name: str, receipt: Dict[str, Any]) -> None:
        observation = self._extract_observation(receipt)
        if observation is not None:
            method_values = self._methods.setdefault(method_name, {})
            self._record_max(method_values, observation)

    def build_profile(
        self, network: str, headroom: float, chain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        profile: Dict[str, Any] = {
            "version": 1,
            "network": network,
            "measuredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if chain_id is not None:
            profile["chainId"] = chain_id
        if self._deploy:
            profile["deploy"] = self._apply_headroom(self._deploy, headroom)
        profile["methods"] = {
            method_name: self._apply_headroom(values, headroom)
            for method_name, values in sorted(self._methods.items())
        }
        return profile

    def write(
        self,
        path: Path,
        network: str,
        headroom: float,
        chain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        profile = self.build_profile(
            network=network, headroom=headroom, chain_id=chain_id
        )
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
        return profile

    def has_observations(self) -> bool:
        return bool(self._deploy or self._methods)

    def _extract_observation(
        self, receipt: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, int]]:
        try:
            if not receipt:
                return None
            legacy_observation = self._extract_legacy_fee_observation(receipt)
            if legacy_observation is not None:
                return legacy_observation

            accounting = self._extract_fee_accounting(receipt)
            if accounting is None:
                return None

            observation = self._extract_distribution_observation(accounting)
            report = self._dict_or_none(accounting.get("execution_fee_report")) or {}
            execution_fee_report_total = self._int_value(
                report.get("totalEstimatedFee")
            )
            execution_consumed = self._int_value(
                accounting.get("execution_fee_consumed")
            )
            message_consumed = self._int_value(accounting.get("message_fee_consumed"))
            genvm_message_consumed = self._int_value(
                accounting.get("genvm_message_fee_consumed")
            )

            observation.update(
                {
                    "executionBudgetPerRound": execution_consumed
                    + execution_fee_report_total,
                    "totalMessageFees": max(
                        message_consumed, genvm_message_consumed
                    ),
                }
            )
            return observation
        except Exception as e:
            if not self._warned_malformed:
                logger.warning("Failed to record fee profile observation: %s", e)
                self._warned_malformed = True
            return None

    def _extract_legacy_fee_observation(
        self, receipt: Dict[str, Any]
    ) -> Optional[Dict[str, int]]:
        fees = self._dict_or_none(receipt.get("fees"))
        if not fees:
            return None
        consumed = self._dict_or_none(fees.get("consumed"))
        if not consumed:
            return None
        observation = {
            output_key: int(consumed[consumed_key])
            for output_key, consumed_key in CONSUMED_KEY_MAPPING.items()
        }
        distribution = self._dict_or_none(fees.get("distribution"))
        if distribution:
            observation.update(self._allocation_observation(distribution))
        return observation

    def _extract_distribution_observation(
        self, accounting: Dict[str, Any]
    ) -> Dict[str, int]:
        for candidate in self._distribution_candidates(accounting):
            distribution = self._dict_or_none(candidate)
            if distribution:
                return self._allocation_observation(distribution)
        return {}

    def _distribution_candidates(self, accounting: Dict[str, Any]):
        yield accounting.get("fees_distribution")
        yield accounting.get("feesDistribution")

        preset = self._dict_or_none(accounting.get("recommended_fee_preset"))
        if preset:
            yield preset.get("distribution")

        camel_preset = self._dict_or_none(accounting.get("recommendedFeePreset"))
        if camel_preset:
            yield camel_preset.get("distribution")

    def _allocation_observation(self, distribution: Dict[str, Any]) -> Dict[str, int]:
        observation = {
            output_key: self._int_value(distribution.get(source_key))
            for output_key, source_key in ALLOCATION_KEY_MAPPING.items()
            if distribution.get(source_key) is not None
        }
        rotations = distribution.get("rotations")
        if isinstance(rotations, list) and rotations:
            observation["rotationsPerRound"] = max(
                self._int_value(rotation) for rotation in rotations
            )
        return observation

    def _extract_fee_accounting(
        self, receipt: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        for candidate in self._fee_accounting_candidates(receipt):
            accounting = self._dict_or_none(candidate)
            if accounting:
                return accounting
        return None

    def _fee_accounting_candidates(self, receipt: Dict[str, Any]):
        yield receipt.get("fee_accounting")
        yield receipt.get("feeAccounting")

        data = self._dict_or_none(receipt.get("data"))
        if data:
            yield data.get("fee_accounting")
            yield data.get("feeAccounting")

        genvm_result = self._dict_or_none(receipt.get("genvm_result"))
        if genvm_result:
            yield genvm_result.get("fee_accounting")
            yield genvm_result.get("feeAccounting")

        consensus_data = self._dict_or_none(receipt.get("consensus_data"))
        if not consensus_data:
            return

        leader_receipt = consensus_data.get("leader_receipt")
        leader_receipts = (
            leader_receipt
            if isinstance(leader_receipt, list)
            else [leader_receipt]
        )
        for item in leader_receipts:
            receipt_item = self._dict_or_none(item)
            if not receipt_item:
                continue
            yield receipt_item.get("fee_accounting")
            yield receipt_item.get("feeAccounting")
            leader_genvm_result = self._dict_or_none(receipt_item.get("genvm_result"))
            if leader_genvm_result:
                yield leader_genvm_result.get("fee_accounting")
                yield leader_genvm_result.get("feeAccounting")

    @staticmethod
    def _dict_or_none(value: Any) -> Optional[Dict[str, Any]]:
        return value if isinstance(value, dict) else None

    @staticmethod
    def _int_value(value: Any) -> int:
        return int(value or 0)

    @staticmethod
    def _record_max(current: Dict[str, int], observation: Dict[str, int]) -> None:
        for key in FEE_KEYS:
            if key not in observation:
                continue
            current[key] = max(current.get(key, 0), observation[key])

    @staticmethod
    def _apply_headroom(values: Dict[str, int], headroom: float) -> Dict[str, str]:
        multiplier = Decimal(str(headroom))
        return {
            key: str(
                value
                if key == "rotationsPerRound"
                else math.ceil(Decimal(value) * multiplier)
            )
            for key, value in values.items()
        }


_fee_profile_collector = FeeProfileCollector()


def get_fee_profile_collector() -> FeeProfileCollector:
    return _fee_profile_collector


def reset_fee_profile_collector() -> FeeProfileCollector:
    global _fee_profile_collector
    _fee_profile_collector = FeeProfileCollector()
    return _fee_profile_collector


def fee_profile_enabled() -> bool:
    return get_general_config().get_fee_profile_path() is not None


def maybe_record_fee_observation(
    kind: str, receipt: Dict[str, Any], method_name: Optional[str] = None
) -> None:
    try:
        if not fee_profile_enabled():
            return
        collector = get_fee_profile_collector()
        if kind == "deploy":
            collector.record_deploy(receipt)
        elif method_name is not None:
            collector.record_method(method_name, receipt)
    except Exception as e:
        logger.warning("Failed to record fee profile observation: %s", e)
