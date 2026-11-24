import pytest

from gltest.contracts.contract_factory import ContractFactory
from gltest.exceptions import DeploymentError, SchemaDiscoveryError

CONTRACT_ADDRESS = "0x" + "ab" * 20
SUCCESS_RECEIPT = {
    "hash": "0xdeploy",
    "status": "ACCEPTED",
    "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]},
    "data": {"contract_address": CONTRACT_ADDRESS},
}
FAILED_RECEIPT = {
    "hash": "0xdeploy",
    "status": "ACCEPTED",
    "consensus_data": {"leader_receipt": [{"execution_result": "ERROR"}]},
    "data": {"contract_address": CONTRACT_ADDRESS},
}


class FakeGeneralConfig:
    def get_default_wait_interval(self):
        return 1

    def get_default_wait_retries(self):
        return 1

    def get_leader_only(self):
        return False

    def check_studio_based_rpc(self):
        return False


class FakeClient:
    """Serves deploys and (optionally) schema lookups."""

    def __init__(self, receipt, schema=None):
        self.receipt = receipt
        self.schema = schema
        self.deploy_contract_calls = []

    def deploy_contract(self, **kwargs):
        self.deploy_contract_calls.append(kwargs)
        return "0xdeploy"

    def wait_for_transaction_receipt(self, **kwargs):
        return self.receipt

    def get_contract_schema_for_code(self, contract_code):
        if self.schema is None:
            raise RuntimeError("schema lookup unavailable")
        return self.schema


def _patch(monkeypatch, client):
    module = "gltest.contracts.contract_factory"
    monkeypatch.setattr(f"{module}.get_gl_client", lambda: client)
    monkeypatch.setattr(f"{module}.get_gl_hosted_studio_client", lambda: client)
    monkeypatch.setattr(f"{module}.get_local_client", lambda: client)
    monkeypatch.setattr(f"{module}.get_general_config", lambda: FakeGeneralConfig())


def _factory():
    return ContractFactory(contract_name="Example", contract_code="class Example: pass")


def test_deploy_reports_address_and_receipt_when_schema_lookup_fails(monkeypatch):
    client = FakeClient(SUCCESS_RECEIPT)
    _patch(monkeypatch, client)

    with pytest.raises(SchemaDiscoveryError) as exc_info:
        _factory().deploy()

    error = exc_info.value
    assert error.contract_address == CONTRACT_ADDRESS
    assert error.receipt == SUCCESS_RECEIPT
    assert error.receipt["hash"] == "0xdeploy"
    message = str(error)
    assert "deployed" in message and CONTRACT_ADDRESS in message
    assert "schema" in message
    assert "do not redeploy" in message.lower()
    # one deploy was submitted: callers must not retry
    assert len(client.deploy_contract_calls) == 1


def test_schema_discovery_error_stays_a_value_error(monkeypatch):
    client = FakeClient(SUCCESS_RECEIPT)
    _patch(monkeypatch, client)

    with pytest.raises(ValueError):
        _factory().deploy()


def test_build_contract_still_fails_without_receipt(monkeypatch):
    client = FakeClient(SUCCESS_RECEIPT)
    _patch(monkeypatch, client)

    with pytest.raises(SchemaDiscoveryError) as exc_info:
        _factory().build_contract(CONTRACT_ADDRESS)

    assert exc_info.value.contract_address == CONTRACT_ADDRESS
    assert exc_info.value.receipt is None
    assert "Failed to get schema from all clients" in str(exc_info.value)


def test_deploy_still_returns_contract_when_schema_is_available(monkeypatch):
    client = FakeClient(SUCCESS_RECEIPT, schema={"methods": {}})
    _patch(monkeypatch, client)

    contract = _factory().deploy()

    assert contract.address == CONTRACT_ADDRESS
    assert len(client.deploy_contract_calls) == 1


def test_failed_deploy_transaction_is_still_a_deployment_error(monkeypatch):
    client = FakeClient(FAILED_RECEIPT)
    _patch(monkeypatch, client)

    with pytest.raises(DeploymentError):
        _factory().deploy()
