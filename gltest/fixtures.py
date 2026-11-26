"""
This module provides reusable pytest fixtures for common gltest operations.
These fixtures can be imported and used in test files.
"""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts, get_default_account
from gltest.network import get_current_chain_type, get_current_network


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


@pytest.fixture(scope="session")
def current_network():
    """
    Provides the name of the selected network (e.g. "localnet").

    Scope: session - created once per test session
    """
    return get_current_network()


@pytest.fixture(scope="session")
def current_chain_type():
    """
    Provides the chain type of the selected network (e.g. "testnet_bradbury").

    Scope: session - created once per test session
    """
    return get_current_chain_type()
