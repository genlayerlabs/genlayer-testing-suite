"""
This module provides reusable pytest fixtures for common gltest operations.
These fixtures can be imported and used in test files.
"""

from urllib.parse import urlparse

import pytest
from gltest.exceptions import HelperError
from gltest_cli.config.general import get_general_config
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts, get_default_account
from gltest.network import get_current_chain_type, get_current_network
from gltest.helpers.network_time import (
    _reset_time_if_supported,
    clock_was_modified,
    raise_if_quarantined,
)


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


_LOCAL_CHAIN_TYPES = ("localnet", "studio_devnet")
_LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "::1", "0.0.0.0")


def _is_local_network() -> bool:
    """True only for a local chain type whose RPC URL is a loopback address.

    Hosted networks (testnets, ``studionet``) are never touched.
    """
    try:
        if get_current_chain_type() not in _LOCAL_CHAIN_TYPES:
            return False
        host = urlparse(get_general_config().get_rpc_url()).hostname
    except ValueError:  # unresolvable configuration: do not touch the network
        return False
    return host in _LOOPBACK_HOSTS


def _is_local_chain_type() -> bool:
    try:
        return get_current_chain_type() in _LOCAL_CHAIN_TYPES
    except ValueError:
        return False


def _helper_changed_local_clock() -> bool:
    """Non-loopback local endpoints (e.g. ``http://glsim:4000`` in Compose) are
    only cleaned up after a test when a time helper changed their clock."""
    try:
        if get_current_chain_type() not in _LOCAL_CHAIN_TYPES:
            return False
        return clock_was_modified(get_general_config().get_rpc_url())
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def _gltest_reset_network_time():
    """
    Give every test a network clock equal to wall time, on local networks
    only: the clock is reset before the test starts (so changes made by
    other means, e.g. raw RPC calls or an earlier run, are not inherited) and
    again after it ends. Backends without time manipulation support are
    detected on the first probe and left alone; a failed reset on a backend
    that does support it raises.

    Hosted networks (testnets, ``studionet``) receive no clock RPCs. Local
    endpoints that are not loopback (e.g. a Compose hostname) are probed only
    after a test in which a time helper changed the clock. To give
    a test a baseline, call ``set_time`` in the test or in a function-scoped
    fixture; it is reset when the test ends.

    Scope: function - runs around every test
    """
    local = _is_local_network()
    if local or _helper_changed_local_clock():
        _reset_time_if_supported()
        # A skipped reset (e.g. connection refused during an earlier teardown)
        # leaves the endpoint marked as modified: never admit the test then.
        url = get_general_config().get_rpc_url()
        if clock_was_modified(url):
            raise HelperError(
                f"The network clock at {url} could not be reset after an "
                "earlier change; refusing to run the test on a shifted clock."
            )
    elif _is_local_chain_type():
        raise_if_quarantined(get_general_config().get_rpc_url())
    yield
    if local or _helper_changed_local_clock():
        _reset_time_if_supported()
