"""
Native Python test runner for GenLayer intelligent contracts.

Runs contracts directly in Python without WASM/simulator, providing
Foundry-style cheatcodes and fast test execution.

Usage:
    from gltest.native import VMContext, deploy_contract

    def test_transfer():
        vm = VMContext()
        with vm.activate():
            token = deploy_contract("path/to/Token.py", vm, owner)
            vm.sender = alice
            token.transfer(bob, 100)
            assert token.balances[bob] == 100
"""

from .vm import VMContext
from .loader import deploy_contract, load_contract_class, create_address, create_test_addresses
from .wasi_mock import ContractRollback, MockNotFoundError

__all__ = [
    "VMContext",
    "deploy_contract",
    "load_contract_class",
    "create_address",
    "create_test_addresses",
    "ContractRollback",
    "MockNotFoundError",
]
