# Re-export genlayer-py types
from genlayer_py.types import (
    CalldataAddress,
    GenLayerTransaction,
    TransactionStatus,
    CalldataEncodable,
    TransactionHashVariant,
)
from typing import List, TypedDict, Dict, Any


class MockedLLMResponse(TypedDict):
    """Maps prompts to responses"""

    # Prompt -> raw JSON string response
    nondet_exec_prompt: Dict[str, str]

    # Principle -> expected boolean
    eq_principle_prompt_comparative: Dict[str, bool]
    eq_principle_prompt_non_comparative: Dict[str, bool]


class ValidatorConfig(TypedDict):
    """Validator information."""

    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]


class TransactionContext(TypedDict, total=False):
    """Context for transaction operations."""

    validators: List[ValidatorConfig]  # List to create virtual validators
    genvm_datetime: str  # ISO format datetime string
