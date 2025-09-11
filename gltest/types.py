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


class WebResponse(TypedDict):
    """Web response"""

    method: str  # GET, POST, PUT, DELETE, etc.
    status: int  # status code of the response
    body: str  # body of the response


class MockedWebRequest(TypedDict):
    """Maps urls to responses"""

    nondet_web_request: Dict[str, WebResponse]


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
