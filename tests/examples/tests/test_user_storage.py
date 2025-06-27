from gltest import (
    get_contract_factory,
    get_default_account,
    create_account,
    get_accounts,
)
from gltest.assertions import tx_execution_succeeded
from gltest_cli.config.general import get_general_config
from genlayer_py.chains import testnet_asimov


INITIAL_STATE_USER_A = "user_a_initial_state"
UPDATED_STATE_USER_A = "user_a_updated_state"
INITIAL_STATE_USER_B = "user_b_initial_state"
UPDATED_STATE_USER_B = "user_b_updated_state"


def test_user_storage(setup_validators):
    setup_validators()
    general_config = get_general_config()
    chain = general_config.get_chain()

    # Account Setup
    if chain.id == testnet_asimov.id:
        accounts = get_accounts()
        if len(accounts) < 2:
            raise ValueError(
                f"Test requires at least 2 accounts, but only {len(accounts)} available"
            )
        from_account_a = accounts[0]
        from_account_b = accounts[1]
    else:
        from_account_a = get_default_account()
        from_account_b = create_account()

    factory = get_contract_factory("UserStorage")
    contract = factory.deploy()

    # GET Initial State
    contract_state_1 = contract.get_complete_storage(args=[]).call()
    assert contract_state_1 == {}

    # ADD User A State
    transaction_response_call_1 = contract.update_storage(
        args=[INITIAL_STATE_USER_A]
    ).transact()
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2_1 = contract.get_complete_storage(args=[]).call()
    assert contract_state_2_1[from_account_a.address] == INITIAL_STATE_USER_A

    # Get Updated State
    contract_state_2_2 = contract.get_account_storage(
        args=[from_account_a.address]
    ).call()
    assert contract_state_2_2 == INITIAL_STATE_USER_A

    # ADD User B State
    transaction_response_call_2 = (
        contract.connect(from_account_b)
        .update_storage(args=[INITIAL_STATE_USER_B])
        .transact()
    )
    assert tx_execution_succeeded(transaction_response_call_2)

    # Get Updated State
    contract_state_3 = contract.get_complete_storage(args=[]).call()
    assert contract_state_3[from_account_a.address] == INITIAL_STATE_USER_A
    assert contract_state_3[from_account_b.address] == INITIAL_STATE_USER_B

    # UPDATE User A State
    transaction_response_call_3 = contract.update_storage(
        args=[UPDATED_STATE_USER_A]
    ).transact()
    assert tx_execution_succeeded(transaction_response_call_3)

    # Get Updated State
    contract_state_4_1 = contract.get_complete_storage(args=[]).call()
    assert contract_state_4_1[from_account_a.address] == UPDATED_STATE_USER_A
    assert contract_state_4_1[from_account_b.address] == INITIAL_STATE_USER_B

    # Get Updated State
    contract_state_4_2 = contract.get_account_storage(
        args=[from_account_b.address]
    ).call()
    assert contract_state_4_2 == INITIAL_STATE_USER_B
