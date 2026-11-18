# Re-export genlayer-py types
from genlayer_py.types import (
    CalldataAddress,
    GenLayerTransaction,
    CalldataEncodable,
    TransactionHashVariant,
)
from dataclasses import dataclass
from dataclasses import field
from typing import List, TypedDict, Dict, Any, Optional

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


@dataclass
class TransactionTree:
    """A transaction receipt together with the receipts of the transactions it triggered."""

    receipt: GenLayerTransaction
    children: List["TransactionTree"] = field(default_factory=list)

    @property
    def hash(self) -> Optional[str]:
        return self.receipt.get("hash") or self.receipt.get("tx_id")

    def flatten(self) -> List[GenLayerTransaction]:
        """Return this receipt and all descendant receipts (depth-first, pre-order).

        A transaction reachable through several paths is listed once.
        """
        result: List[GenLayerTransaction] = []
        seen: set = set()

        def _visit(node: "TransactionTree") -> None:
            key = node.hash or id(node.receipt)
            if key not in seen:
                seen.add(key)
                result.append(node.receipt)
            for child in node.children:
                _visit(child)

        _visit(self)
        return result

    def triggered_receipts(self) -> List[GenLayerTransaction]:
        """Return all descendant receipts, excluding this transaction's own receipt."""
        return self.flatten()[1:]
