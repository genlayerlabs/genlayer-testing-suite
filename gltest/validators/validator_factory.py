from gltest.types import MockedLLMResponse, MockedWebResponse
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
    mock_web_response: Optional[MockedWebResponse]

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

        # Mock llm response
        mock_llm = self.mock_llm_response or {}
        mock_llm_config = {
            "response": mock_llm.get("nondet_exec_prompt", {}),
            "eq_principle_prompt_comparative": mock_llm.get(
                "eq_principle_prompt_comparative", {}
            ),
            "eq_principle_prompt_non_comparative": mock_llm.get(
                "eq_principle_prompt_non_comparative", {}
            ),
        }
        mock_web = self.mock_web_response or {}
        mock_web_config = {
            "nondet_web_request": mock_web.get("nondet_web_request", {}),
        }
        return {
            **normal_config,
            "plugin_config": {
                **self.plugin_config,
                "mock_response": mock_llm_config,
                "mock_web_response": mock_web_config,
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
            mock_web_response=deepcopy(self.mock_web_response),
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
            mock_web_response=None,
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

    def create_mock_validator(
        self,
        mock_llm_response: Optional[MockedLLMResponse] = None,
        mock_web_response: Optional[MockedWebResponse] = None,
    ) -> Validator:
        if mock_llm_response is None and mock_web_response is None:
            raise ValueError(
                "mock_llm_response and mock_web_response cannot both be None"
            )
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
            mock_llm_response=(
                deepcopy(mock_llm_response) if mock_llm_response is not None else None
            ),
            mock_web_response=(
                deepcopy(mock_web_response) if mock_web_response is not None else None
            ),
        )

    def batch_create_mock_validators(
        self,
        count: int,
        mock_llm_response: Optional[MockedLLMResponse] = None,
        mock_web_response: Optional[MockedWebResponse] = None,
    ) -> List[Validator]:
        return [
            self.create_mock_validator(mock_llm_response, mock_web_response)
            for _ in range(count)
        ]


def get_validator_factory() -> ValidatorFactory:
    return ValidatorFactory()
