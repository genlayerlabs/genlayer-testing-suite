"""
Type definitions for native test runner.

Reuses MockedLLMResponse and MockedWebResponse from gltest.types.
"""

# Re-export from parent package for convenience
from ..types import (
    MockedLLMResponse,
    MockedWebResponse,
    MockedWebResponseData,
)

__all__ = [
    "MockedLLMResponse",
    "MockedWebResponse",
    "MockedWebResponseData",
]
