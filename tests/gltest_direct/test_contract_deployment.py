"""
Integration tests for direct contract deployment.

Tests deploying actual contracts using the pytest fixtures.
"""

import pytest
from pathlib import Path


CONTRACTS_DIR = Path(__file__).parent.parent / "examples" / "contracts"


class TestContractDeployment:
    """Tests for deploying contracts with direct_deploy fixture."""

    def test_deploy_storage_contract(self, direct_vm, direct_deploy):
        """Can deploy and interact with Storage contract."""
        storage = direct_deploy(
            str(CONTRACTS_DIR / "storage.py"),
            "initial value"
        )

        # Read initial value
        assert storage.get_storage() == "initial value"

        # Update and verify
        storage.update_storage("new value")
        assert storage.get_storage() == "new value"

    def test_direct_mode_ignores_fee_kwargs(self, direct_vm, direct_deploy):
        """Fee-aware dev-env tests do not crash in gasless direct mode."""
        fees = {
            "distribution": {"leaderTimeunitsAllocation": 1},
            "messageAllocations": [],
            "feeValue": 10,
        }
        storage = direct_deploy(
            str(CONTRACTS_DIR / "storage.py"),
            "initial value",
            fees=fees,
            fee_value=10,
            wait_until="decided",
        )

        storage.update_storage("new value", fees=fees, fee_value=10)

        assert storage.get_storage() == "new value"

    def test_deploy_user_storage_with_sender(self, direct_vm, direct_deploy):
        """UserStorage respects gl.message.sender_address."""
        user_storage = direct_deploy(str(CONTRACTS_DIR / "user_storage.py"))

        # Re-create addresses after deploy (genlayer now loaded, returns Address objects)
        from gltest.direct.loader import create_address
        alice = create_address("alice")
        bob = create_address("bob")

        # Alice stores her data
        direct_vm.sender = alice
        user_storage.update_storage("alice's data")

        # Bob stores his data
        direct_vm.sender = bob
        user_storage.update_storage("bob's data")

        # Verify data is separate per user
        alice_data = user_storage.get_account_storage(alice.as_hex)
        bob_data = user_storage.get_account_storage(bob.as_hex)

        assert alice_data == "alice's data"
        assert bob_data == "bob's data"

    def test_snapshot_with_contract(self, direct_vm, direct_deploy):
        """Snapshot/revert works with contract state."""
        storage = direct_deploy(str(CONTRACTS_DIR / "storage.py"), "before")

        snap_id = direct_vm.snapshot()

        storage.update_storage("after")
        assert storage.get_storage() == "after"

        direct_vm.revert(snap_id)

        # After revert, the same storage instance should read the reverted state
        # NOTE: The current implementation requires re-reading from storage
        # which happens automatically on the next get_storage() call
        assert storage.get_storage() == "before"

    def test_prank_with_contract(self, direct_vm, direct_deploy):
        """Prank changes sender during contract calls."""
        user_storage = direct_deploy(str(CONTRACTS_DIR / "user_storage.py"))

        # Re-create addresses after deploy (genlayer now loaded)
        from gltest.direct.loader import create_address
        alice = create_address("alice")
        bob = create_address("bob")

        direct_vm.sender = alice

        # Prank as Bob
        with direct_vm.prank(bob):
            user_storage.update_storage("pranked as bob")

        # Verify it was stored under Bob's address
        bob_data = user_storage.get_account_storage(bob.as_hex)
        assert bob_data == "pranked as bob"

        # Alice's storage still empty
        with pytest.raises(Exception):
            user_storage.get_account_storage(alice.as_hex)


class TestAddressFixtures:
    """Tests for address helper fixtures."""

    def test_direct_accounts(self, direct_accounts):
        """direct_accounts provides 10 test addresses."""
        assert len(direct_accounts) == 10
        # All unique
        assert len(set(str(a) for a in direct_accounts)) == 10

    def test_owner_is_default_sender(self, direct_owner, direct_vm):
        """direct_owner matches default VM sender."""
        from gltest.direct.loader import create_address
        default = create_address("default_sender")
        assert direct_owner == default


class TestWarp:
    """vm.warp() is visible through the message context after deploy."""

    def test_warp_updates_message_datetime(self, direct_vm, direct_deploy):
        """warp() after SDK import updates gl.message datetime."""
        contract = direct_deploy(str(CONTRACTS_DIR / "message_time.py"))

        direct_vm.warp("2030-01-02T03:04:05Z")

        assert contract.get_message_datetime() == "2030-01-02T03:04:05Z"
        assert contract.get_raw_datetime() == "2030-01-02T03:04:05Z"

    def test_revert_restores_message_datetime(self, direct_vm, direct_deploy):
        """revert() restores the snapshot's message datetime."""
        contract = direct_deploy(str(CONTRACTS_DIR / "message_time.py"))
        direct_vm.warp("2030-01-01T00:00:00Z")
        snap_id = direct_vm.snapshot()

        direct_vm.warp("2031-01-01T00:00:00Z")
        direct_vm.revert(snap_id)

        assert contract.get_message_datetime() == "2030-01-01T00:00:00Z"
        assert contract.get_raw_datetime() == "2030-01-01T00:00:00Z"
