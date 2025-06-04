from gltest.assertions import tx_execution_succeeded, tx_execution_failed

GENLAYER_SUCCESS_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}
}

GENLAYER_FAILED_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "ERROR"}]}
}

GENLAYER_EMPTY_LEADER_RECEIPT = {"consensus_data": {"leader_receipt": []}}


def test_with_successful_transaction():
    assert tx_execution_succeeded(GENLAYER_SUCCESS_TRANSACTION) is True
    assert tx_execution_failed(GENLAYER_SUCCESS_TRANSACTION) is False


def test_with_failed_transaction():
    assert tx_execution_succeeded(GENLAYER_FAILED_TRANSACTION) is False
    assert tx_execution_failed(GENLAYER_FAILED_TRANSACTION) is True


def test_with_empty_leader_receipt():
    assert tx_execution_succeeded(GENLAYER_EMPTY_LEADER_RECEIPT) is False
    assert tx_execution_failed(GENLAYER_EMPTY_LEADER_RECEIPT) is True


def test_with_invalid_transaction():
    assert tx_execution_succeeded({}) is False
    assert tx_execution_failed({}) is True
