"""
Integration tests for native contract deployment.

Tests deploying actual contracts using the pytest fixtures.
"""

import pytest
from pathlib import Path


CONTRACTS_DIR = Path(__file__).parent.parent / "examples" / "contracts"


class TestContractDeployment:
    """Tests for deploying contracts with native_deploy fixture."""

    def test_deploy_storage_contract(self, native_vm, native_deploy):
        """Can deploy and interact with Storage contract."""
        storage = native_deploy(
            str(CONTRACTS_DIR / "storage.py"),
            "initial value"
        )

        # Read initial value
        assert storage.get_storage() == "initial value"

        # Update and verify
        storage.update_storage("new value")
        assert storage.get_storage() == "new value"

    def test_deploy_user_storage_with_sender(self, native_vm, native_deploy):
        """UserStorage respects gl.message.sender_address."""
        user_storage = native_deploy(str(CONTRACTS_DIR / "user_storage.py"))

        # Re-create addresses after deploy (genlayer now loaded, returns Address objects)
        from gltest.native.loader import create_address
        alice = create_address("alice")
        bob = create_address("bob")

        # Alice stores her data
        native_vm.sender = alice
        user_storage.update_storage("alice's data")

        # Bob stores his data
        native_vm.sender = bob
        user_storage.update_storage("bob's data")

        # Verify data is separate per user
        alice_data = user_storage.get_account_storage(alice.as_hex)
        bob_data = user_storage.get_account_storage(bob.as_hex)

        assert alice_data == "alice's data"
        assert bob_data == "bob's data"

    def test_snapshot_with_contract(self, native_vm, native_deploy):
        """Snapshot/revert works with contract state."""
        storage = native_deploy(str(CONTRACTS_DIR / "storage.py"), "before")

        snap_id = native_vm.snapshot()

        storage.update_storage("after")
        assert storage.get_storage() == "after"

        native_vm.revert(snap_id)

        # After revert, the same storage instance should read the reverted state
        # NOTE: The current implementation requires re-reading from storage
        # which happens automatically on the next get_storage() call
        assert storage.get_storage() == "before"

    def test_prank_with_contract(self, native_vm, native_deploy):
        """Prank changes sender during contract calls."""
        user_storage = native_deploy(str(CONTRACTS_DIR / "user_storage.py"))

        # Re-create addresses after deploy (genlayer now loaded)
        from gltest.native.loader import create_address
        alice = create_address("alice")
        bob = create_address("bob")

        native_vm.sender = alice

        # Prank as Bob
        with native_vm.prank(bob):
            user_storage.update_storage("pranked as bob")

        # Verify it was stored under Bob's address
        bob_data = user_storage.get_account_storage(bob.as_hex)
        assert bob_data == "pranked as bob"

        # Alice's storage still empty
        with pytest.raises(Exception):
            user_storage.get_account_storage(alice.as_hex)


class TestAddressFixtures:
    """Tests for address helper fixtures."""

    def test_native_accounts(self, native_accounts):
        """native_accounts provides 10 test addresses."""
        assert len(native_accounts) == 10
        # All unique
        assert len(set(str(a) for a in native_accounts)) == 10

    def test_owner_is_default_sender(self, native_owner, native_vm):
        """native_owner matches default VM sender."""
        from gltest.native.loader import create_address
        default = create_address("default_sender")
        assert native_owner == default
