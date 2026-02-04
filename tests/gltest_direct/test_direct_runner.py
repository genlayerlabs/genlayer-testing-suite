"""
Integration tests for the direct Python test runner.

Tests the full flow of:
- VMContext activation
- Contract loading with SDK versioning
- Storage operations
- Prank/snapshot/revert
- Mock web/LLM
"""

import pytest
from pathlib import Path

from gltest.direct import VMContext, deploy_contract, create_address
from gltest.direct.wasi_mock import ContractRollback, MockNotFoundError


# Path to example contracts
CONTRACTS_DIR = Path(__file__).parent.parent / "examples" / "contracts"


class TestVMContext:
    """Tests for VMContext basics."""

    def test_vm_context_creation(self):
        """VMContext can be created with default values."""
        vm = VMContext()
        assert vm._value == 0
        assert vm._chain_id == 1

    def test_sender_property(self):
        """Sender can be set and read."""
        vm = VMContext()
        alice = create_address("alice")
        vm.sender = alice
        assert vm.sender == alice

    def test_prank_context_manager(self):
        """Prank temporarily changes sender."""
        vm = VMContext()
        alice = create_address("alice")
        bob = create_address("bob")

        vm.sender = alice
        assert vm.sender == alice

        with vm.prank(bob):
            assert vm.sender == bob

        assert vm.sender == alice

    def test_prank_start_stop(self):
        """startPrank/stopPrank work correctly."""
        vm = VMContext()
        alice = create_address("alice")
        bob = create_address("bob")

        vm.sender = alice
        vm.startPrank(bob)
        assert vm.sender == bob

        vm.stopPrank()
        assert vm.sender == alice

    def test_stop_prank_without_active_raises(self):
        """stopPrank raises when no active prank."""
        vm = VMContext()
        with pytest.raises(RuntimeError, match="No active prank"):
            vm.stopPrank()


class TestStorage:
    """Tests for in-memory storage."""

    def test_storage_read_write(self):
        """Storage read/write works."""
        vm = VMContext()
        slot_id = b"\x00" * 32

        slot = vm._storage.get_store_slot(slot_id)
        slot.write(0, b"hello")
        assert slot.read(0, 5) == b"hello"

    def test_storage_indirect_slot(self):
        """Indirect slots work for nested storage."""
        vm = VMContext()
        slot_id = b"\x00" * 32

        slot = vm._storage.get_store_slot(slot_id)
        indirect = slot.indirect(0)

        indirect.write(0, b"nested")
        assert indirect.read(0, 6) == b"nested"

        # Original slot unaffected
        assert slot.read(0, 6) == b"\x00" * 6


class TestSnapshots:
    """Tests for snapshot/revert functionality."""

    def test_snapshot_revert(self):
        """Snapshot and revert restore storage state."""
        vm = VMContext()
        slot_id = b"\x00" * 32

        slot = vm._storage.get_store_slot(slot_id)
        slot.write(0, b"before")

        snap_id = vm.snapshot()

        slot.write(0, b"after!")
        assert slot.read(0, 6) == b"after!"

        vm.revert(snap_id)

        # Need to get slot again after revert
        slot = vm._storage.get_store_slot(slot_id)
        assert slot.read(0, 6) == b"before"

    def test_snapshot_preserves_balances(self):
        """Snapshots include balances."""
        vm = VMContext()
        alice = create_address("alice")

        vm.deal(alice, 1000)
        snap_id = vm.snapshot()

        vm.deal(alice, 500)
        assert vm._balances[vm._to_bytes(alice)] == 500

        vm.revert(snap_id)
        assert vm._balances[vm._to_bytes(alice)] == 1000

    def test_revert_invalid_snapshot_raises(self):
        """Revert with invalid ID raises."""
        vm = VMContext()
        with pytest.raises(ValueError, match="Snapshot 999 not found"):
            vm.revert(999)


class TestMocking:
    """Tests for web/LLM mocking."""

    def test_web_mock_registration(self):
        """Web mocks can be registered and matched."""
        vm = VMContext()
        vm.mock_web(
            r"api\.example\.com/price",
            {"status": 200, "body": '{"price": 42000}'}
        )

        result = vm._match_web_mock("https://api.example.com/price/btc")
        assert result is not None
        assert result["status"] == 200

    def test_web_mock_no_match_returns_none(self):
        """Unmatched web requests return None."""
        vm = VMContext()
        result = vm._match_web_mock("https://unknown.com/api")
        assert result is None

    def test_llm_mock_registration(self):
        """LLM mocks can be registered and matched."""
        vm = VMContext()
        vm.mock_llm(r"classify.*tweet", "positive")

        result = vm._match_llm_mock("Please classify this tweet: Hello world")
        assert result == "positive"

    def test_clear_mocks(self):
        """clear_mocks removes all registered mocks."""
        vm = VMContext()
        vm.mock_web(r".*", {"status": 200})
        vm.mock_llm(r".*", "response")

        vm.clear_mocks()

        assert vm._match_web_mock("any") is None
        assert vm._match_llm_mock("any") is None


class TestExpectRevert:
    """Tests for expect_revert functionality."""

    def test_expect_revert_catches_rollback(self):
        """expect_revert catches ContractRollback."""
        vm = VMContext()

        with vm.expect_revert():
            raise ContractRollback("Test error")

    def test_expect_revert_with_message(self):
        """expect_revert can match message."""
        vm = VMContext()

        with vm.expect_revert("Test error"):
            raise ContractRollback("Test error occurred")

    def test_expect_revert_fails_if_no_revert(self):
        """expect_revert fails if call succeeds."""
        vm = VMContext()

        with pytest.raises(AssertionError, match="Expected revert"):
            with vm.expect_revert():
                pass  # No revert

    def test_expect_revert_wrong_message(self):
        """expect_revert fails if message doesn't match."""
        vm = VMContext()

        with pytest.raises(AssertionError, match="Expected revert with message"):
            with vm.expect_revert("expected message"):
                raise ContractRollback("different message")


class TestActivation:
    """Tests for VM activation context."""

    def test_activate_context(self):
        """VM activation injects WASI mock."""
        import sys
        vm = VMContext()

        with vm.activate():
            assert "_genlayer_wasi" in sys.modules

        # Cleaned up after
        assert "_genlayer_wasi" not in sys.modules


class TestAddressCreation:
    """Tests for address creation helpers."""

    def test_create_address_deterministic(self):
        """Same seed creates same address."""
        addr1 = create_address("alice")
        addr2 = create_address("alice")
        assert addr1 == addr2

    def test_create_address_different_seeds(self):
        """Different seeds create different addresses."""
        alice = create_address("alice")
        bob = create_address("bob")
        assert alice != bob
