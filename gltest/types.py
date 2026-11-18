# Re-export genlayer-py types
from genlayer_py.types import (
    CalldataAddress,
    GenLayerTransaction,
    CalldataEncodable,
    TransactionHashVariant,
)
from typing import List, TypedDict, Dict, Any

try:
    # genlayer-py layers the consumer lifecycle over the raw protocol status.
    from genlayer_py.types.transactions import ProtocolTransactionStatus
except ImportError:  # genlayer-py before the lifecycle layering
    from genlayer_py.types import TransactionStatus as ProtocolTransactionStatus

try:
    from genlayer_py.types import TransactionLifecycle
except ImportError:  # genlayer-py before the lifecycle layering
    TransactionLifecycle = Dict[str, Any]

# gltest keeps `TransactionStatus` as part of its own public API for the test
# suites that already pass it to `wait_transaction_status`. Internal code uses
# the protocol name; new code should express waits with `wait_until` instead.
TransactionStatus = ProtocolTransactionStatus


class MockedLLMResponse(TypedDict):
    """Maps prompts to responses"""

    # Prompt -> raw JSON string response
    nondet_exec_prompt: Dict[str, str]

    # Principle -> expected boolean
    eq_principle_prompt_comparative: Dict[str, bool]
    eq_principle_prompt_non_comparative: Dict[str, bool]


class MockedWebResponseData(TypedDict):
    """Mocked web response data with method for matching"""

    method: str  # GET, POST, PUT, DELETE, etc.
    status: int  # status code of the response
    body: str  # body of the response


class MockedWebResponse(TypedDict):
    """Maps urls to responses"""

    nondet_web_request: Dict[str, MockedWebResponseData]


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
