from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


INITIAL_STATE = "a"
UPDATED_STATE = "b"


def test_storage(setup_validators):
    setup_validators()
    factory = get_contract_factory("Storage")
    contract = factory.deploy(args=[INITIAL_STATE], wait_retries=40)

    # Get initial state
    contract_state_1 = contract.get_storage(args=[]).call()
    assert contract_state_1 == INITIAL_STATE

    # Update State
    transaction_response_call_1 = contract.update_storage(
        args=[UPDATED_STATE]
    ).transact(wait_retries=40)
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2 = contract.get_storage(args=[]).call()
    assert contract_state_2 == UPDATED_STATE
