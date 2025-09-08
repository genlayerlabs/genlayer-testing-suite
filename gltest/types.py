# Re-export genlayer-py types
from genlayer_py.types import (
    CalldataAddress,
    GenLayerTransaction,
    TransactionStatus,
    CalldataEncodable,
    TransactionHashVariant,
)
from typing import List, TypedDict, Dict, Any


class ValidatorConfig(TypedDict):
    """Validator information."""

    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]


class TransactionContext(TypedDict, total=False):
    """Context for consensus operations."""

    validators: List[ValidatorConfig]  # List to create virtual validators
    genvm_datetime: str  # ISO format datetime string
