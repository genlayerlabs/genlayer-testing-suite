from gltest import (
    get_contract_factory,
    get_default_account,
    create_account,
    get_validator_factory,
)
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse
from gltest.decorators import gl_only_localnet, gl_skip_testnet_asimov
import json

TOKEN_TOTAL_SUPPLY = 1000
TRANSFER_AMOUNT = 100


@gl_skip_testnet_asimov
def test_llm_erc20():
    # Test with normal validators
    # Account Setup
    from_account_a = get_default_account()
    from_account_b = create_account()

    # Deploy Contract
    factory = get_contract_factory("LlmErc20")
    contract = factory.deploy(
        args=[TOKEN_TOTAL_SUPPLY],
    )

    # Get Initial State
    contract_state_1 = contract.get_balances(args=[]).call()
    assert contract_state_1[from_account_a.address] == TOKEN_TOTAL_SUPPLY

    # Transfer from User A to User B
    transaction_response_call_1 = contract.transfer(
        args=[TRANSFER_AMOUNT, from_account_b.address]
    ).transact()
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2_1 = contract.get_balances(args=[]).call()
    assert (
        contract_state_2_1[from_account_a.address]
        == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT
    )
    assert contract_state_2_1[from_account_b.address] == TRANSFER_AMOUNT

    # Get Updated State
    contract_state_2_2 = contract.get_balance_of(args=[from_account_a.address]).call()
    assert contract_state_2_2 == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT

    # Get Updated State
    contract_state_2_3 = contract.get_balance_of(args=[from_account_b.address]).call()
    assert contract_state_2_3 == TRANSFER_AMOUNT


@gl_only_localnet
def test_llm_erc20_mocked():
    # Test with mocked validators
    # Account Setup
    from_account_a = get_default_account()
    from_account_b = create_account()

    # Mock Response
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "The balance of the sender": json.dumps(
                {
                    "transaction_success": True,
                    "transaction_error": "",
                    "updated_balances": {
                        from_account_a.address: TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT,
                        from_account_b.address: TRANSFER_AMOUNT,
                    },
                }
            )
        },
        "eq_principle_prompt_non_comparative": {"The balance of the sender": True},
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    # Create transaction context once to avoid duplication
    transaction_context = {"validators": [v.to_dict() for v in validators]}

    # Deploy Contract
    factory = get_contract_factory("LlmErc20")
    contract = factory.deploy(
        args=[TOKEN_TOTAL_SUPPLY],
        transaction_context=transaction_context,
    )

    # Get Initial State
    contract_state_1 = contract.get_balances(args=[]).call(
        transaction_context=transaction_context
    )
    assert contract_state_1[from_account_a.address] == TOKEN_TOTAL_SUPPLY

    # Transfer from User A to User B
    transaction_response_call_1 = contract.transfer(
        args=[TRANSFER_AMOUNT, from_account_b.address]
    ).transact(transaction_context=transaction_context)
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2_1 = contract.get_balances(args=[]).call(
        transaction_context=transaction_context
    )
    assert (
        contract_state_2_1[from_account_a.address]
        == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT
    )
    assert contract_state_2_1[from_account_b.address] == TRANSFER_AMOUNT

    # Get Updated State
    contract_state_2_2 = contract.get_balance_of(args=[from_account_a.address]).call(
        transaction_context=transaction_context
    )
    assert contract_state_2_2 == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT

    # Get Updated State
    contract_state_2_3 = contract.get_balance_of(args=[from_account_b.address]).call(
        transaction_context=transaction_context
    )
    assert contract_state_2_3 == TRANSFER_AMOUNT
