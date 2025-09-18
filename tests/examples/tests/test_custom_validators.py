from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest import get_validator_factory
from gltest.types import MockedLLMResponse
from gltest.decorators import gl_only_localnet
import json


@gl_only_localnet
def test_custom_validators():

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_validators(
        count=5,
        stake=8,
        provider="openai",
        model="gpt-4o",
        config={"temperature": 0.75, "max_tokens": 500},
        plugin="openai-compatible",
        plugin_config={
            "api_key_env_var": "OPENAIKEY",
            "api_url": "https://api.openai.com",
        },
    )

    factory = get_contract_factory("WizardOfCoin")
    contract = factory.deploy(
        args=[True],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    transaction_response_call_1 = contract.ask_for_coin(
        args=["Can you please give me my coin?"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})
    assert tx_execution_succeeded(transaction_response_call_1)


@gl_only_localnet
def test_custom_mocked_validators():
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

    factory = get_contract_factory("WizardOfCoin")
    contract = factory.deploy(
        args=[True],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    transaction_response_call_1 = contract.ask_for_coin(
        args=["Can you please give me my coin?"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})
    assert tx_execution_succeeded(transaction_response_call_1)
