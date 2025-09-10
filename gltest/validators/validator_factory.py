from gltest.types import MockedLLMResponse
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from copy import deepcopy


@dataclass
class Validator:
    stake: int
    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]

    # Mock configuration
    mock_enabled: bool
    mock_llm_response: Optional[MockedLLMResponse]

    def to_dict(self) -> Dict[str, Any]:
        normal_config = {
            "stake": self.stake,
            "provider": self.provider,
            "model": self.model,
            "config": deepcopy(self.config),
            "plugin": self.plugin,
            "plugin_config": deepcopy(self.plugin_config),
        }
        if not self.mock_enabled:
            return normal_config

        mock = self.mock_llm_response or {}
        mock_config = {
            "response": mock.get("nondet_exec_prompt", {}),
            "eq_principle_prompt_comparative": mock.get(
                "eq_principle_prompt_comparative", {}
            ),
            "eq_principle_prompt_non_comparative": mock.get(
                "eq_principle_prompt_non_comparative", {}
            ),
        }
        return {
            **normal_config,
            "plugin_config": {
                **self.plugin_config,
                "mock_response": mock_config,
            },
        }

    def batch_clone(self, count: int) -> List["Validator"]:
        return [self.clone() for _ in range(count)]

    def clone(self) -> "Validator":
        return Validator(
            stake=self.stake,
            provider=self.provider,
            model=self.model,
            config=deepcopy(self.config),
            plugin=self.plugin,
            plugin_config=deepcopy(self.plugin_config),
            mock_enabled=self.mock_enabled,
            mock_llm_response=deepcopy(self.mock_llm_response),
        )


class ValidatorFactory:
    def __init__(self):
        pass

    def create_validator(
        self,
        stake: int,
        provider: str,
        model: str,
        config: Dict[str, Any],
        plugin: str,
        plugin_config: Dict[str, Any],
    ) -> Validator:
        return Validator(
            stake=stake,
            provider=provider,
            model=model,
            config=deepcopy(config),
            plugin=plugin,
            plugin_config=deepcopy(plugin_config),
            mock_enabled=False,
            mock_llm_response=None,
        )

    def batch_create_validators(
        self,
        count: int,
        stake: int,
        provider: str,
        model: str,
        config: Dict[str, Any],
        plugin: str,
        plugin_config: Dict[str, Any],
    ) -> List[Validator]:
        return [
            self.create_validator(
                stake=stake,
                provider=provider,
                model=model,
                config=config,
                plugin=plugin,
                plugin_config=plugin_config,
            )
            for _ in range(count)
        ]

    def create_mock_validator(self, mock_llm_response: MockedLLMResponse) -> Validator:
        return Validator(
            stake=8,
            provider="openai",
            model="gpt-4o",
            config={"temperature": 0.75, "max_tokens": 500},
            plugin="openai-compatible",
            plugin_config={
                "api_key_env_var": "OPENAIKEY",
                "api_url": "https://api.openai.com",
            },
            mock_enabled=True,
            mock_llm_response=deepcopy(mock_llm_response),
        )

    def batch_create_mock_validators(
        self,
        count: int,
        mock_llm_response: MockedLLMResponse,
    ) -> List[Validator]:
        return [self.create_mock_validator(mock_llm_response) for _ in range(count)]


def get_validator_factory() -> ValidatorFactory:
    return ValidatorFactory()
