from gltest.assertions import tx_execution_succeeded, tx_execution_failed

GENLAYER_SUCCESS_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}
}

GENLAYER_FAILED_TRANSACTION = {
    "consensus_data": {"leader_receipt": [{"execution_result": "ERROR"}]}
}

GENLAYER_EMPTY_LEADER_RECEIPT = {"consensus_data": {"leader_receipt": []}}

GENLAYER_GENVM_TRANSACTION = {
    "consensus_data": {
        "leader_receipt": [
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stdout": "Process completed successfully with code 123 items",
                    "stderr": "Warning: deprecated function used",
                },
            }
        ]
    }
}

GENLAYER_GENVM_EMPTY_STDERR = {
    "consensus_data": {
        "leader_receipt": [
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stdout": "Task finished without errors",
                    "stderr": "",
                },
            }
        ]
    }
}

GENLAYER_GENVM_NO_STDOUT = {
    "consensus_data": {
        "leader_receipt": [
            {
                "execution_result": "SUCCESS",
                "genvm_result": {"stderr": "Error occurred"},
            }
        ]
    }
}

GENLAYER_GENVM_FAILED = {
    "consensus_data": {
        "leader_receipt": [
            {
                "execution_result": "ERROR",
                "genvm_result": {
                    "stdout": "Process failed",
                    "stderr": "Critical error occurred",
                },
            }
        ]
    }
}


def test_with_successful_transaction():
    """Test assertion functions with a basic successful transaction.

    Validates that:
    - tx_execution_succeeded returns True for successful transactions
    - tx_execution_failed returns False for successful transactions
    """
    assert tx_execution_succeeded(GENLAYER_SUCCESS_TRANSACTION) is True
    assert tx_execution_failed(GENLAYER_SUCCESS_TRANSACTION) is False


def test_with_failed_transaction():
    """Test assertion functions with a basic failed transaction.

    Validates that:
    - tx_execution_succeeded returns False for failed transactions
    - tx_execution_failed returns True for failed transactions
    """
    assert tx_execution_succeeded(GENLAYER_FAILED_TRANSACTION) is False
    assert tx_execution_failed(GENLAYER_FAILED_TRANSACTION) is True


def test_with_empty_leader_receipt():
    """Test assertion functions with empty leader_receipt array.

    Validates that:
    - Both functions handle empty leader_receipt gracefully
    - Empty leader_receipt is treated as a failed transaction
    """
    assert tx_execution_succeeded(GENLAYER_EMPTY_LEADER_RECEIPT) is False
    assert tx_execution_failed(GENLAYER_EMPTY_LEADER_RECEIPT) is True


def test_with_invalid_transaction():
    """Test assertion functions with completely invalid transaction structure.

    Validates that:
    - Both functions handle malformed transactions gracefully
    - Invalid transactions are treated as failed
    """
    assert tx_execution_succeeded({}) is False
    assert tx_execution_failed({}) is True


def test_genvm_result_without_match():
    """Test assertion functions with genvm_result but no match parameters.

    Validates that:
    - Transactions with genvm_result succeed when execution_result is SUCCESS
    - No match parameters means only basic execution status is checked
    """
    assert tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION) is True
    assert tx_execution_failed(GENLAYER_GENVM_TRANSACTION) is False


def test_match_std_out_simple_string():
    """Test stdout matching with simple string patterns.

    Validates that:
    - Simple string matching works correctly in stdout
    - Non-matching strings cause the assertion to fail
    - tx_execution_failed behaves oppositely to tx_execution_succeeded
    """
    assert (
        tx_execution_succeeded(
            GENLAYER_GENVM_TRANSACTION, match_std_out="Process completed"
        )
        is True
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_out="nonexistent")
        is False
    )
    assert (
        tx_execution_failed(GENLAYER_GENVM_TRANSACTION, match_std_out="nonexistent")
        is True
    )


def test_match_std_err_simple_string():
    """Test stderr matching with simple string patterns.

    Validates that:
    - Simple string matching works correctly in stderr
    - Non-matching strings cause the assertion to fail
    - tx_execution_failed behaves oppositely to tx_execution_succeeded
    """
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_err="Warning")
        is True
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_err="nonexistent")
        is False
    )
    assert (
        tx_execution_failed(GENLAYER_GENVM_TRANSACTION, match_std_err="nonexistent")
        is True
    )


def test_match_std_out_regex():
    """Test stdout matching with regex patterns.

    Validates that:
    - Complex regex patterns work correctly in stdout
    - Different regex patterns match appropriately
    - Non-matching regex patterns cause assertions to fail
    - Tests various regex features like \\d+, .*, word boundaries
    """
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_out=r".*code \d+")
        is True
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_out=r".* 123 .*")
        is True
    )
    assert (
        tx_execution_succeeded(
            GENLAYER_GENVM_TRANSACTION, match_std_out=r"Process.*successfully"
        )
        is True
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_out=r"code \d{4}")
        is False
    )


def test_match_std_err_regex():
    """Test stderr matching with regex patterns.

    Validates that:
    - Complex regex patterns work correctly in stderr
    - Different regex patterns match appropriately
    - Non-matching regex patterns cause assertions to fail
    - Tests various regex features like .*, word boundaries
    """
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_err=r"Warning:.*")
        is True
    )
    assert (
        tx_execution_succeeded(
            GENLAYER_GENVM_TRANSACTION, match_std_err=r".*deprecated.*"
        )
        is True
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_TRANSACTION, match_std_err=r"Error:.*")
        is False
    )


def test_match_both_stdout_and_stderr():
    """Test matching both stdout and stderr simultaneously.

    Validates that:
    - Both stdout and stderr patterns must match for success
    - If either pattern fails to match, the assertion fails
    - Combined matching works with both simple strings and regex
    """
    assert (
        tx_execution_succeeded(
            GENLAYER_GENVM_TRANSACTION,
            match_std_out="Process completed",
            match_std_err="Warning",
        )
        is True
    )

    assert (
        tx_execution_succeeded(
            GENLAYER_GENVM_TRANSACTION,
            match_std_out="Process completed",
            match_std_err="nonexistent",
        )
        is False
    )


def test_match_empty_stderr():
    """Test matching empty stderr with different approaches.

    Validates that:
    - Empty stderr can be matched with regex pattern ^$
    - Empty stderr can be matched with empty string
    - Non-empty patterns fail when stderr is empty
    """
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_EMPTY_STDERR, match_std_err=r"^$") is True
    )
    assert tx_execution_succeeded(GENLAYER_GENVM_EMPTY_STDERR, match_std_err="") is True
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_EMPTY_STDERR, match_std_err="Warning")
        is False
    )


def test_missing_stdout_field():
    """Test behavior when stdout field is missing from genvm_result.

    Validates that:
    - Missing stdout field causes match_std_out to fail
    - The assertion handles missing fields gracefully
    - tx_execution_failed returns True when stdout matching is requested but field is missing
    """
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_NO_STDOUT, match_std_out="anything")
        is False
    )
    assert (
        tx_execution_failed(GENLAYER_GENVM_NO_STDOUT, match_std_out="anything") is True
    )


def test_missing_stderr_field():
    """Test behavior when stderr field is missing from genvm_result.

    Validates that:
    - Missing stderr field causes match_std_err to fail
    - The assertion handles missing fields gracefully
    - tx_execution_failed returns True when stderr matching is requested but field is missing
    """
    genvm_no_stderr = {
        "consensus_data": {
            "leader_receipt": [
                {"execution_result": "SUCCESS", "genvm_result": {"stdout": "Success"}}
            ]
        }
    }
    assert tx_execution_succeeded(genvm_no_stderr, match_std_err="anything") is False
    assert tx_execution_failed(genvm_no_stderr, match_std_err="anything") is True


def test_failed_execution_with_genvm_result():
    """Test assertion behavior with failed execution but present genvm_result.

    Validates that:
    - execution_result takes precedence over output matching
    - Even with matching stdout/stderr, failed executions return False
    - The basic execution status is checked before output matching
    """
    assert tx_execution_succeeded(GENLAYER_GENVM_FAILED) is False
    assert tx_execution_failed(GENLAYER_GENVM_FAILED) is True

    # Even with matching stdout/stderr, should still fail if execution_result is not SUCCESS
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_FAILED, match_std_out="Process failed")
        is False
    )
    assert (
        tx_execution_succeeded(GENLAYER_GENVM_FAILED, match_std_err="Critical error")
        is False
    )


def test_missing_genvm_result_with_match():
    """Test behavior when genvm_result is missing but match parameters are provided.

    Validates that:
    - Missing genvm_result causes output matching to fail
    - Both stdout and stderr matching fail when genvm_result is absent
    - tx_execution_failed returns True when match parameters are used without genvm_result
    """
    assert (
        tx_execution_succeeded(GENLAYER_SUCCESS_TRANSACTION, match_std_out="anything")
        is False
    )
    assert (
        tx_execution_succeeded(GENLAYER_SUCCESS_TRANSACTION, match_std_err="anything")
        is False
    )
    assert (
        tx_execution_failed(GENLAYER_SUCCESS_TRANSACTION, match_std_out="anything")
        is True
    )
