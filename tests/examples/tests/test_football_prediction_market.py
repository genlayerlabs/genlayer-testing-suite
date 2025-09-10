from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def test_football_prediction_market():
    factory = get_contract_factory("PredictionMarket")
    contract = factory.deploy(args=["2024-06-26", "Georgia", "Portugal"])

    tx_receipt = contract.resolve(args=[]).transact()
    assert tx_execution_succeeded(tx_receipt)

    state = contract.get_resolution_data(args=[]).call()
    assert state["has_resolved"] is True
