from pathlib import Path
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
INITIAL_STATE = "hello"
UPDATED_STATE = "world"


def test_upgradable_storage():
    # Deploy v1
    factory = get_contract_factory(
        contract_file_path=CONTRACTS_DIR / "upgradable_storage.py"
    )
    contract = factory.deploy(args=[INITIAL_STATE])

    # Verify initial state
    assert contract.get_storage(args=[]).call() == INITIAL_STATE

    # Update state using v1 method
    tx = contract.update_storage(args=[UPDATED_STATE]).transact()
    assert tx_execution_succeeded(tx)
    assert contract.get_storage(args=[]).call() == UPDATED_STATE

    # Read v2 code and upgrade the contract
    v2_code = (CONTRACTS_DIR / "upgradable_storage_v2.py").read_bytes()
    tx = contract.upgrade(args=[v2_code]).transact()
    assert tx_execution_succeeded(tx)

    # After upgrade, rebuild the contract proxy from the v2 schema
    # so we can access newly added methods
    v2_factory = get_contract_factory(
        contract_file_path=CONTRACTS_DIR / "upgradable_storage_v2.py"
    )
    contract_v2 = v2_factory.build_contract(contract_address=contract.address)

    # Storage persists across upgrades
    assert contract_v2.get_storage(args=[]).call() == UPDATED_STATE

    # New v2 method works
    assert contract_v2.get_storage_length(args=[]).call() == len(UPDATED_STATE)

    # Existing methods still work
    tx = contract_v2.update_storage(args=["upgraded"]).transact()
    assert tx_execution_succeeded(tx)
    assert contract_v2.get_storage(args=[]).call() == "upgraded"
    assert contract_v2.get_storage_length(args=[]).call() == len("upgraded")
