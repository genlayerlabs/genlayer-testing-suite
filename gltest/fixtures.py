"""
This module provides reusable pytest fixtures for common gltest operations.
These fixtures can be imported and used in test files.
"""

import pytest
from gltest.clients import get_gl_client, get_gl_provider
from gltest.accounts import get_accounts, get_default_account
from gltest_cli.config.general import get_general_config


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


@pytest.fixture(scope="function")
def setup_validators():
    """
    Creates test validators for localnet environment.

    Args:
        mock_response (dict, optional): Mock validator response when using --test-with-mocks flag
        n_validators (int, optional): Number of validators to create (default: 5)

    Scope: function - created fresh for each test
    """
    general_config = get_general_config()
    provider = get_gl_provider()

    def _setup(mock_response=None, n_validators=5):
        if not general_config.check_local_rpc():
            return
        if general_config.get_test_with_mocks():
            for _ in range(n_validators):
                provider.make_request(
                    method="sim_createValidator",
                    params=[
                        8,
                        "openai",
                        "gpt-4o",
                        {"temperature": 0.75, "max_tokens": 500},
                        "openai-compatible",
                        {
                            "api_key_env_var": "OPENAIKEY",
                            "api_url": "https://api.openai.com",
                            "mock_response": mock_response if mock_response else {},
                        },
                    ],
                )
        else:
            provider.make_request(
                method="sim_createRandomValidators",
                params=[n_validators, 8, 12],
            )

    yield _setup

    if not general_config.check_local_rpc():
        return

    provider.make_request(method="sim_deleteAllValidators", params=[])
