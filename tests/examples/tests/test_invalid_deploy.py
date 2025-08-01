import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_failed
from gltest.exceptions import DeploymentError


def test_invalid_deploy_basic_exception(setup_validators):
    """Test deployment failure with basic exception"""
    setup_validators()
    factory = get_contract_factory("InvalidDeploy")

    # Deployment should fail with exception
    with pytest.raises(DeploymentError):
        factory.deploy()


def test_invalid_deploy_receipt_only(setup_validators):
    """Test deployment failure using deploy_contract_tx() method that returns receipt only"""
    setup_validators()
    factory = get_contract_factory("InvalidDeploy")

    # Deploy and get receipt - should show failure
    receipt = factory.deploy_contract_tx()
    assert tx_execution_failed(receipt)
