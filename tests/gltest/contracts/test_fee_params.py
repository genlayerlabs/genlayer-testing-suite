from gltest.contracts.contract import Contract
from gltest.contracts.contract_factory import ContractFactory


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
    def __init__(self):
        self.write_contract_calls = []
        self.deploy_contract_calls = []
        self.wait_for_transaction_receipt_calls = []

    def write_contract(self, **kwargs):
        self.write_contract_calls.append(kwargs)
        return "0xwrite"

    def deploy_contract(self, **kwargs):
        self.deploy_contract_calls.append(kwargs)
        return "0xdeploy"

    def wait_for_transaction_receipt(self, **kwargs):
        self.wait_for_transaction_receipt_calls.append(kwargs)
        return {
            "status": "ACCEPTED",
            "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]},
        }


def test_transact_threads_fee_params_to_sdk(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    monkeypatch.setattr(
        "gltest.contracts.contract.get_general_config", lambda: FakeGeneralConfig()
    )
    contract = Contract.new(
        address="0x123",
        schema={"methods": {"set_value": {"readonly": False}}},
    )
    fees = {
        "distribution": {"leaderTimeunitsAllocation": 1},
        "messageAllocations": [],
    }

    receipt = contract.set_value([1]).transact(
        fees=fees,
        fee_value=123,
        wait_until="finalized",
    )

    assert receipt["status"] == "ACCEPTED"
    assert client.write_contract_calls[0]["fees"] == {
        **fees,
        "feeValue": 123,
    }
    assert client.wait_for_transaction_receipt_calls[0] == {
        "transaction_hash": "0xwrite",
        "wait_until": "finalized",
        "interval": 1,
        "retries": 1,
    }


def test_deploy_threads_fee_params_to_sdk(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr("gltest.contracts.contract_factory.get_gl_client", lambda: client)
    monkeypatch.setattr(
        "gltest.contracts.contract_factory.get_general_config",
        lambda: FakeGeneralConfig(),
    )
    factory = ContractFactory(contract_name="Example", contract_code="class Example: pass")
    fees = {
        "distribution": {"leaderTimeunitsAllocation": 1},
        "messageAllocations": [],
        "feeValue": 100,
    }

    receipt = factory.deploy_contract_tx(
        args=["hello"],
        fees=fees,
        fee_value=250,
    )

    assert receipt["status"] == "ACCEPTED"
    assert client.deploy_contract_calls[0]["fees"] == {
        **fees,
        "feeValue": 250,
    }
    assert client.wait_for_transaction_receipt_calls[0] == {
        "transaction_hash": "0xdeploy",
        "wait_until": "decided",
        "interval": 1,
        "retries": 1,
    }
