from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def test_multi_file_contract(setup_validators):
    # Multi file contracts are considered if they are defined in a __init__.py file
    # Deploy Contract, it will deploy other.py as well
    setup_validators()
    factory = get_contract_factory("MultiFileContract")
    contract = factory.deploy(args=[])

    wait_response = contract.wait(args=[]).transact()
    assert tx_execution_succeeded(wait_response)

    res = contract.test(args=[]).call()
    assert res == "123"
