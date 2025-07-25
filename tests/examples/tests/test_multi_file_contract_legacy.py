from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus


def test_multi_file_contract_legacy(setup_validators):
    # Multi file contracts are considered if they are defined in a __init__.gpy file
    # Deploy Contract, it will deploy other.gpy as well
    setup_validators()
    factory = get_contract_factory("MultiFileContractLegacy")
    contract = factory.deploy_contract(
        args=[],
        wait_transaction_status=TransactionStatus.FINALIZED,
        wait_triggered_transactions=True,
        wait_triggered_transactions_status=TransactionStatus.ACCEPTED,
    )

    res = contract.test(args=[]).call()
    assert res == "123"
