from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse
import json


def test_multi_analysis_all_pass():
    """Test when all analyses pass with good scores"""
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            # Alignment analysis
            "Analyze if this content aligns": json.dumps(
                {"score": 2, "reason": "Content perfectly aligns with the goal"}
            ),
            # Quality analysis
            "Analyze the quality of this content": json.dumps(
                {"score": 3, "reason": "Excellent quality content"}
            ),
            # Engagement analysis
            "Analyze the engagement potential": json.dumps(
                {"score": 5, "reason": "Very high engagement potential"}
            ),
        },
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    factory = get_contract_factory("MultiAnalysis")
    contract = factory.deploy(
        args=["Test Campaign", "Promote our product"],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    # Test successful analysis
    transaction_response = contract.analyze_content(
        args=["This is great content about our amazing product!"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})

    assert tx_execution_succeeded(transaction_response)

    # Read the analysis results
    result = contract.get_last_analysis().call()
    assert result["alignment"] == 2
    assert result["quality"] == 3
    assert result["engagement"] == 5
    assert result["total"] == 10


def test_multi_analysis_alignment_fails():
    """Test when alignment analysis fails (score 0), blocking subsequent analyses"""
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            # Alignment fails
            "Analyze if this content aligns": json.dumps(
                {"score": 0, "reason": "Content does not align with goal at all"}
            ),
            # These won't be called due to early exit, but include for completeness
            "Analyze the quality of this content": json.dumps(
                {"score": 3, "reason": "Should not be called"}
            ),
            "Analyze the engagement potential": json.dumps(
                {"score": 5, "reason": "Should not be called"}
            ),
        },
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    factory = get_contract_factory("MultiAnalysis")
    contract = factory.deploy(
        args=["Test Campaign", "Promote our product"],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    transaction_response = contract.analyze_content(
        args=["This content is completely off-topic"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})

    assert tx_execution_succeeded(transaction_response)

    # Read the analysis results
    result = contract.get_last_analysis().call()
    assert result["alignment"] == 0
    assert result["quality"] == 0  # Skipped due to alignment failure
    assert result["engagement"] == 0  # Skipped due to alignment failure
    assert result["total"] == 0


def test_multi_analysis_quality_fails():
    """Test when alignment passes but quality fails"""
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            # Alignment passes
            "Analyze if this content aligns": json.dumps(
                {"score": 1, "reason": "Content aligns acceptably"}
            ),
            # Quality fails
            "Analyze the quality of this content": json.dumps(
                {"score": 0, "reason": "Very poor quality"}
            ),
            # Won't be called due to quality failure
            "Analyze the engagement potential": json.dumps(
                {"score": 5, "reason": "Should not be called"}
            ),
        },
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    factory = get_contract_factory("MultiAnalysis")
    contract = factory.deploy(
        args=["Test Campaign", "Promote our product"],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    transaction_response = contract.analyze_content(
        args=["Product good but bad grammar and spelling"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})

    assert tx_execution_succeeded(transaction_response)

    # Read the analysis results
    result = contract.get_last_analysis().call()
    assert result["alignment"] == 1
    assert result["quality"] == 0
    assert result["engagement"] == 0  # Skipped due to quality failure
    assert result["total"] == 1


def test_multi_analysis_partial_scores():
    """Test with moderate scores across all analyses"""
    mock_llm_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "Analyze if this content aligns": json.dumps(
                {"score": 1, "reason": "Content aligns acceptably"}
            ),
            "Analyze the quality of this content": json.dumps(
                {"score": 2, "reason": "Good quality"}
            ),
            "Analyze the engagement potential": json.dumps(
                {"score": 3, "reason": "Moderate engagement potential"}
            ),
        },
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_llm_response,
    )

    factory = get_contract_factory("MultiAnalysis")
    contract = factory.deploy(
        args=["Test Campaign", "Promote our product"],
        transaction_context={"validators": [v.to_dict() for v in validators]},
    )

    transaction_response = contract.analyze_content(
        args=["Our product is decent and worth checking out"]
    ).transact(transaction_context={"validators": [v.to_dict() for v in validators]})

    assert tx_execution_succeeded(transaction_response)

    # Read the analysis results
    result = contract.get_last_analysis().call()
    assert result["alignment"] == 1
    assert result["quality"] == 2
    assert result["engagement"] == 3
    assert result["total"] == 6
