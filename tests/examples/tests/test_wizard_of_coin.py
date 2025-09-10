from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def test_wizard_of_coin():
    validator_config = {
        "provider": "openai",
        "model": "gpt-4o",
        "config": {"temperature": 0.75},
        "plugin": "openai-compatible",
        "plugin_config": {"api_key_env_var": "OPENAIKEY"},
    }
    factory = get_contract_factory("WizardOfCoin")
    contract = factory.deploy(
        args=[True],
        transaction_context={"validators": [validator_config]},
    )

    transaction_response_call_1 = contract.ask_for_coin(
        args=["Can you please give me my coin?"]
    ).transact(transaction_context={"validators": [validator_config]})
    assert tx_execution_succeeded(transaction_response_call_1)
