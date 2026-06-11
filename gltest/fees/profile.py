import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from gltest.logging import logger
from gltest_cli.config.general import get_general_config

FEE_KEYS = ("executionBudgetPerRound", "totalMessageFees")
CONSUMED_KEY_MAPPING = {
    "executionBudgetPerRound": "executionConsumed",
    "totalMessageFees": "messageFeesConsumed",
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

    def build_profile(self, network: str, headroom: float) -> Dict[str, Any]:
        profile: Dict[str, Any] = {
            "version": 1,
            "network": network,
            "measuredAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if self._deploy:
            profile["deploy"] = self._apply_headroom(self._deploy, headroom)
        profile["methods"] = {
            method_name: self._apply_headroom(values, headroom)
            for method_name, values in sorted(self._methods.items())
        }
        return profile

    def write(self, path: Path, network: str, headroom: float) -> Dict[str, Any]:
        profile = self.build_profile(network=network, headroom=headroom)
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
            fees = receipt.get("fees")
            if not fees:
                return None
            consumed = fees.get("consumed")
            if not consumed:
                return None
            return {
                output_key: int(consumed[consumed_key])
                for output_key, consumed_key in CONSUMED_KEY_MAPPING.items()
            }
        except Exception as e:
            if not self._warned_malformed:
                logger.warning("Failed to record fee profile observation: %s", e)
                self._warned_malformed = True
            return None

    @staticmethod
    def _record_max(current: Dict[str, int], observation: Dict[str, int]) -> None:
        for key in FEE_KEYS:
            current[key] = max(current.get(key, 0), observation[key])

    @staticmethod
    def _apply_headroom(values: Dict[str, int], headroom: float) -> Dict[str, str]:
        multiplier = Decimal(str(headroom))
        # The backend only reports consumed fee amounts, not consumed time-unit
        # allocations, so leader/validator allocation suggestions are omitted.
        return {
            key: str(math.ceil(Decimal(value) * multiplier))
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
