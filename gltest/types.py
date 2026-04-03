# Re-export genlayer-py types
from __future__ import annotations
from genlayer_py.types import (
    CalldataAddress,
    GenLayerTransaction,
    TransactionStatus,
    CalldataEncodable,
    TransactionHashVariant,
)
from typing import List, TypedDict, Dict, Any, Optional, Literal
from dataclasses import dataclass, field


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
    """A tree structure representing a transaction and its triggered children."""

    receipt: GenLayerTransaction
    children: List[TransactionTree] = field(default_factory=list)

    def flatten(self) -> List[GenLayerTransaction]:
        """Flatten the tree into a list of receipts (breadth-first order)."""
        result = [self.receipt]
        for child in self.children:
            result.extend(child.flatten())
        return result

    def get_children_receipts(
        self, triggered_on: Optional[Literal["accepted", "finalized"]] = None
    ) -> List[GenLayerTransaction]:
        """Get receipts of direct children, optionally filtered by triggered_on status.

        Args:
            triggered_on: Optional status to filter by ("accepted" or "finalized").
                          If None, returns all children receipts.

        Returns:
            A list of receipts from direct children.
        """
        if triggered_on is None:
            return [child.receipt for child in self.children]
        return [
            child.receipt
            for child in self.children
            if child.receipt.get("triggered_on") == triggered_on
        ]
