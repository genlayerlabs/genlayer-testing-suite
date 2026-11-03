"""Direct-mode cases for a GenVM v0.2 contract, run in their own process."""

from pathlib import Path

from gltest.direct.loader import create_address

CONTRACT = str(Path(__file__).parent / "legacy_storage.py")


def test_deploy_with_constructor_arg(direct_deploy):
    contract = direct_deploy(CONTRACT, "seed")
    assert contract.get_label() == "seed"


def test_storage_follows_sender(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, "seed")
    alice = create_address("alice")
    bob = create_address("bob")

    direct_vm.sender = alice
    contract.set_note("from alice")
    with direct_vm.prank(bob):
        contract.set_note("from bob")

    assert contract.get_note(alice.as_hex) == "from alice"
    assert contract.get_note(bob.as_hex) == "from bob"


def test_strict_eq_nondet(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, "seed")
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "rendered"})

    contract.fetch_label("https://example.com/")

    assert contract.get_label() == "rendered"


def test_run_nondet_validator(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, "seed")
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "rendered"})

    contract.fetch_checked("https://example.com/")

    assert contract.get_label() == "rendered"
    assert direct_vm.run_validator() is True
    assert direct_vm.run_validator(leader_result="other") is False
    assert direct_vm.run_validator(leader_error=ValueError("boom")) is False


def test_user_error_reverts(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, "seed")
    with direct_vm.expect_revert("nope"):
        contract.fail("nope")
