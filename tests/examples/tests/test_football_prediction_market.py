from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse
import json
from gltest.decorators import gl_only_localnet


def test_football_prediction_market():
    # Test with normal validators
    factory = get_contract_factory("PredictionMarket")
    contract = factory.deploy(args=["2024-06-26", "Georgia", "Portugal"])

    # Resolve match
    transaction_response_call_1 = contract.resolve(args=[]).transact()
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2 = contract.get_resolution_data(args=[]).call()

    # Check that resolution happened (values will vary with real LLM)
    assert contract_state_2["has_resolved"]


@gl_only_localnet
def test_football_prediction_market_mocked():
    # Test with mocked validators
    team_1 = "Georgia"
    team_2 = "Portugal"
    score = "2:0"
    winner = 1

    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            f"Team 1: {team_1}\nTeam 2: {team_2}": json.dumps(
                {
                    "score": score,
                    "winner": winner,
                }
            ),
        }
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    # Create transaction context once to avoid duplication
    transaction_context = {"validators": [v.to_dict() for v in validators]}

    # Deploy Contract
    factory = get_contract_factory("PredictionMarket")
    contract = factory.deploy(
        args=["2024-06-26", "Georgia", "Portugal"],
        transaction_context=transaction_context,
    )

    # Resolve match
    transaction_response_call_1 = contract.resolve(args=[]).transact(
        transaction_context=transaction_context
    )
    assert tx_execution_succeeded(transaction_response_call_1)

    # Get Updated State
    contract_state_2 = contract.get_resolution_data(args=[]).call(
        transaction_context=transaction_context
    )

    assert contract_state_2["winner"] == 1
    assert contract_state_2["score"] == "2:0"
    assert contract_state_2["has_resolved"]
