"""
This module provides reusable pytest fixtures for common gltest operations.
These fixtures can be imported and used in test files.
"""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts, get_default_account
from gltest.network import get_current_chain_type, get_current_network
from gltest.helpers.network_time import _reset_time_if_modified


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
    Provides the chain type of the selected network (e.g. "testnet_asimov").

    Scope: session - created once per test session
    """
    return get_current_chain_type()


@pytest.fixture(autouse=True)
def _gltest_reset_network_time():
    """
    Undo network clock changes made with ``gltest.helpers`` time helpers
    (``increase_time`` / ``set_time``) once each test finishes, so a shifted
    clock never leaks into the next test.

    No RPC is sent unless the clock was changed, so this is a no-op on
    networks without time manipulation support. To give a test a time
    baseline, call ``set_time`` in the test or in a function-scoped fixture;
    it is reset when the test ends.

    Scope: function - runs around every test
    """
    yield
    _reset_time_if_modified()
