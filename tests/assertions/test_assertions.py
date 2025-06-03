from gltest.assertions import tx_execution_succeeded, tx_execution_failed

GENLYER_SUCCESS_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}
}

GENLAYER_FAILED_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "ERROR"}]}
}


def test_tx_execution_succeeded_with_successful_transaction():
    assert tx_execution_succeeded(GENLYER_SUCCESS_TRANSACTION) is True


def test_tx_execution_succeeded_with_failed_transaction():
    assert tx_execution_succeeded(GENLAYER_FAILED_TRANSACTION) is False


def test_tx_execution_succeeded_with_invalid_transaction():
    assert tx_execution_succeeded({}) is False


def test_tx_execution_succeeded_with_empty_transaction():
    assert tx_execution_succeeded({}) is False


def test_tx_execution_failed_with_successful_transaction():
    assert tx_execution_failed(GENLYER_SUCCESS_TRANSACTION) is False


def test_tx_execution_failed_with_failed_transaction():
    assert tx_execution_failed(GENLAYER_FAILED_TRANSACTION) is True


def test_tx_execution_failed_with_invalid_transaction():
    assert tx_execution_failed({}) is True


def test_tx_execution_failed_with_empty_transaction():
    assert tx_execution_failed({}) is True
