from gltest import get_contract_factory


def test_multi_file_contract():
    # Multi file contracts are considered if they are defined in a __init__.py file
    # Deploy Contract, it will deploy other.py as well
    factory = get_contract_factory("MultiFileContract")
    contract = factory.deploy(
        args=[],
        wait_triggered_transactions=True,
    )

    res = contract.test(args=[]).call()
    assert res == "123"
