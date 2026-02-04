"""
Pytest plugin for native GenLayer contract testing.

Provides fixtures:
- native_vm: VMContext for Foundry-style cheatcodes
- native_deploy: Factory for deploying contracts

Usage:
    def test_transfer(native_vm, native_deploy):
        token = native_deploy("contracts/Token.py")
        native_vm.sender = alice
        token.transfer(bob, 100)
        assert token.balances[bob] == 100
"""

from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any, Optional, Callable

from .vm import VMContext
from .loader import deploy_contract, create_address, create_test_addresses


@pytest.fixture
def native_vm() -> VMContext:
    """
    Provides a fresh VMContext for each test.
    The VM is automatically activated for the test scope.
    """
    ctx = VMContext()
    ctx.sender = create_address("default_sender")

    with ctx.activate():
        yield ctx


@pytest.fixture
def native_deploy(native_vm: VMContext) -> Callable[..., Any]:
    """
    Factory fixture for deploying contracts natively.

    Usage:
        def test_example(native_deploy):
            token = native_deploy("path/to/Token.py", initial_supply=1000)
    """
    def _deploy(
        contract_path: str,
        *args: Any,
        sdk_version: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        path = Path(contract_path)

        if not path.is_absolute():
            if path.exists():
                path = path.resolve()
            else:
                for base in [
                    Path.cwd(),
                    Path.cwd() / "contracts",
                    Path.cwd() / "intelligent-contracts",
                ]:
                    candidate = base / contract_path
                    if candidate.exists():
                        path = candidate.resolve()
                        break

        return deploy_contract(path, native_vm, *args, sdk_version=sdk_version, **kwargs)

    return _deploy


@pytest.fixture
def native_alice() -> Any:
    """Test address: Alice."""
    return create_address("alice")


@pytest.fixture
def native_bob() -> Any:
    """Test address: Bob."""
    return create_address("bob")


@pytest.fixture
def native_charlie() -> Any:
    """Test address: Charlie."""
    return create_address("charlie")


@pytest.fixture
def native_owner() -> Any:
    """Test address: Owner (default sender)."""
    return create_address("default_sender")


@pytest.fixture
def native_accounts() -> list:
    """List of 10 test addresses."""
    return create_test_addresses(10)


def pytest_configure(config):
    """Register markers for native tests."""
    config.addinivalue_line(
        "markers",
        "native: mark test as using native contract execution (no simulator)",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests using native fixtures."""
    for item in items:
        if 'native_vm' in item.fixturenames or 'native_deploy' in item.fixturenames:
            item.add_marker(pytest.mark.native)
