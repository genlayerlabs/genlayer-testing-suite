"""
This module provides reusable pytest fixtures for common gltest operations.
These fixtures can be imported and used in test files.
"""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts, get_default_account


@pytest.fixture(scope="session")
def gl_client():
    """
    Provides a GenLayer client instance.

    Scope: session - created once per test session
    """
    return get_gl_client()


@pytest.fixture(scope="session")
def default_account():
    """
    Provides the default account for testing.

    Scope: session - created once per test session
    """
    return get_default_account()


@pytest.fixture(scope="session")
def accounts():
    """
    Provides a list of test accounts.

    Scope: session - created once per test session
    """
    return get_accounts()
