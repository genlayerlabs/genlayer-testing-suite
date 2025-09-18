from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse
from gltest.decorators import gl_only_localnet
import json


def test_wizard_of_coin():
    # Test with normal validators (uses default validators from network config)
    factory = get_contract_factory("WizardOfCoin")
    contract = factory.deploy(args=[True])

    transaction_response_call_1 = contract.ask_for_coin(
        args=["Can you please give me my coin?"]
    ).transact()
    assert tx_execution_succeeded(transaction_response_call_1)


@gl_only_localnet
def test_wizard_of_coin_mocked():
    # Test with mocked validators
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "wizard": json.dumps(
                {
                    "reasoning": "I am a grumpy wizard and I never give away my coins!",
                    "give_coin": False,
                }
            ),
        },
        "eq_principle_prompt_comparative": {
            "The value of give_coin has to match": True
        },
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    # Create transaction context once to avoid duplication
    transaction_context = {"validators": [v.to_dict() for v in validators]}

    factory = get_contract_factory("WizardOfCoin")
    contract = factory.deploy(
        args=[True],
        transaction_context=transaction_context,
    )

    transaction_response_call_1 = contract.ask_for_coin(
        args=["Can you please give me my coin?"]
    ).transact(transaction_context=transaction_context)
    assert tx_execution_succeeded(transaction_response_call_1)
