from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest import get_validator_factory
from gltest.types import MockedWebResponse
import json
import urllib.parse


def get_username_url(username: str) -> str:
    params = {"user.fields": "public_metrics,verified"}
    return f"https://domain.com/api/twitter/users/by/username/{username}?{urllib.parse.urlencode(params)}"


def test_x_username_storage():
    mock_web_response: MockedWebResponse = {
        "nondet_web_request": {
            get_username_url("user_a"): {
                "method": "GET",
                "status": 200,
                "body": json.dumps({"username": "user_a"}),
            },
            get_username_url("user_b"): {
                "method": "GET",
                "status": 200,
                "body": json.dumps({"username": "user_b"}),
            },
        },
    }
    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_web_response=mock_web_response,
    )
    transaction_context = {"validators": [v.to_dict() for v in validators]}

    factory = get_contract_factory("XUsernameStorage")
    contract = factory.deploy(transaction_context=transaction_context)

    assert contract.get_username().call(transaction_context=transaction_context) == ""

    tx_receipt = contract.update_username(args=["user_a"]).transact(
        transaction_context=transaction_context
    )
    assert tx_execution_succeeded(tx_receipt)

    data = contract.get_username().call(transaction_context=transaction_context)
    assert data == "user_a"

    tx_receipt = contract.update_username(args=["user_b"]).transact(
        transaction_context=transaction_context
    )
    assert tx_execution_succeeded(tx_receipt)

    data = contract.get_username().call(transaction_context=transaction_context)
    assert data == "user_b"
