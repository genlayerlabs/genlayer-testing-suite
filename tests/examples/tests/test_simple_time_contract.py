from gltest import get_contract_factory
from datetime import datetime, timedelta, timezone
from gltest.assertions import tx_execution_succeeded, tx_execution_failed


def test_simple_time_contract():
    """Test all time-based functionality in a single comprehensive test."""

    factory = get_contract_factory("SimpleTimeContract")

    # Test 1: Deploy with past start date (10 days ago)
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).isoformat()
    contract = factory.deploy(args=[past_date])

    # Test 1: Check initial status (10 days after start)
    status = contract.get_status().call()
    assert status["is_active"] == False
    assert status["days_since_start"] == 10
    assert status["can_activate"] == True

    # Test 2: Try to activate before start date (simulate going back in time)
    before_start_date = now - timedelta(days=15)  # 5 days before start
    before_start_date_receipt = contract.activate().transact(
        transaction_context={
            "genvm_datetime": before_start_date.isoformat(),
        },
    )
    assert tx_execution_failed(before_start_date_receipt)

    # Test 3: Activate after start date
    activate_date = now - timedelta(days=5)  # 5 days after start (15 days ago + 10)
    activate_receipt = contract.activate().transact(
        transaction_context={
            "genvm_datetime": activate_date.isoformat(),
        },
    )
    assert tx_execution_succeeded(activate_receipt)

    # Test 4: Verify activation and check status
    status = contract.get_status().call(
        transaction_context={
            "genvm_datetime": activate_date.isoformat(),
        },
    )
    assert status["is_active"] == True
    assert status["days_since_start"] == 5
    assert status["can_set_data"] == True

    # Test 5: Set data within valid period (within 30 days)
    set_data_date = now - timedelta(days=2)  # 8 days after start
    test_data = "Test data within valid period"
    set_data_receipt = contract.set_data(
        args=[test_data],
    ).transact(
        transaction_context={
            "genvm_datetime": set_data_date.isoformat(),
        }
    )
    assert tx_execution_succeeded(set_data_receipt)

    # Test 6: Verify data was set
    status = contract.get_status().call(
        transaction_context={
            "genvm_datetime": set_data_date.isoformat(),
        },
    )
    assert status["data"] == test_data
    assert status["days_since_start"] == 8

    # Test 7: Try to set data after 30 days (should fail)
    expired_date = now + timedelta(days=25)  # 35 days after start
    expired_date_receipt = contract.set_data(
        args=["Should fail - expired"],
    ).transact(
        transaction_context={
            "genvm_datetime": expired_date.isoformat(),
        }
    )
    assert tx_execution_failed(expired_date_receipt)

    # Test 8: Check status shows expired
    status = contract.get_status().call(
        transaction_context={
            "genvm_datetime": expired_date.isoformat(),
        },
    )
    assert status["is_active"] == True  # Still active
    assert status["can_set_data"] == False  # But can't set data
    assert status["days_since_start"] == 35
