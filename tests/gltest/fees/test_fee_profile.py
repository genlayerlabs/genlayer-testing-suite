import json

import pytest

from gltest.contracts.contract import Contract
from gltest.contracts.contract_factory import ContractFactory
from gltest.fees import (
    FeeProfileCollector,
    get_fee_profile_collector,
    reset_fee_profile_collector,
)


def fee_receipt(execution_consumed, message_fees_consumed):
    return {
        "status": "ACCEPTED",
        "fees": {
            "consumed": {
                "executionConsumed": str(execution_consumed),
                "messageFeesConsumed": str(message_fees_consumed),
                "storageFeeUsed": "999999",
            },
            "distribution": {
                "leaderTimeunitsAllocation": "100",
                "validatorTimeunitsAllocation": "200",
                "executionBudgetPerRound": "1",
                "totalMessageFees": "1",
            },
        },
    }


class FakeGeneralConfig:
    def __init__(self, fee_profile_path=None):
        self.fee_profile_path = fee_profile_path

    def get_default_wait_interval(self):
        return 1

    def get_default_wait_retries(self):
        return 1

    def get_leader_only(self):
        return False

    def check_studio_based_rpc(self):
        return False

    def get_fee_profile_path(self):
        return self.fee_profile_path


class FakeClient:
    def __init__(self, receipt):
        self.receipt = receipt
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
        return self.receipt


@pytest.fixture(autouse=True)
def reset_collector():
    reset_fee_profile_collector()
    yield
    reset_fee_profile_collector()


def test_collector_records_max_and_applies_headroom_with_big_int():
    collector = FeeProfileCollector()
    big_value = 10**20
    collector.record_deploy(fee_receipt(100, 0))
    collector.record_deploy(fee_receipt(101, 10))
    collector.record_method("create_bet", fee_receipt(big_value, 0))

    profile = collector.build_profile(network="localnet", headroom=1.25)

    assert profile["version"] == 1
    assert profile["network"] == "localnet"
    assert profile["deploy"] == {
        "executionBudgetPerRound": "127",
        "totalMessageFees": "13",
    }
    assert profile["methods"]["create_bet"] == {
        "executionBudgetPerRound": "125000000000000000000",
        "totalMessageFees": "0",
    }


def test_receipts_without_fee_data_are_ignored():
    collector = FeeProfileCollector()
    collector.record_deploy({"status": "ACCEPTED"})
    collector.record_method("create_bet", {"fees": None})

    profile = collector.build_profile(network="localnet", headroom=1.25)

    assert "deploy" not in profile
    assert profile["methods"] == {}


def test_message_fee_zero_is_recorded():
    collector = FeeProfileCollector()
    collector.record_method("create_bet", fee_receipt(10, 0))

    profile = collector.build_profile(network="localnet", headroom=1.0)

    assert profile["methods"]["create_bet"]["totalMessageFees"] == "0"


def test_profile_shape_omits_deploy_when_unobserved_and_time_unit_keys():
    collector = FeeProfileCollector()
    collector.record_method("create_bet", fee_receipt(10, 5))

    profile = collector.build_profile(network="localnet", headroom=1.0)

    assert set(profile) == {"version", "network", "measuredAt", "methods"}
    assert profile["methods"] == {
        "create_bet": {
            "executionBudgetPerRound": "10",
            "totalMessageFees": "5",
        }
    }
    assert "leaderTimeunitsAllocation" not in profile["methods"]["create_bet"]
    assert "validatorTimeunitsAllocation" not in profile["methods"]["create_bet"]


def test_write_creates_parent_dirs_and_round_trips_json(tmp_path):
    collector = FeeProfileCollector()
    collector.record_deploy(fee_receipt(10, 0))
    output_path = tmp_path / "profiles" / "fees.json"

    profile = collector.write(output_path, network="localnet", headroom=1.25)

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == profile


def test_transact_records_fee_profile_observation(monkeypatch, tmp_path):
    client = FakeClient(fee_receipt(312500, 12500))
    monkeypatch.setattr("gltest.contracts.contract.get_gl_client", lambda: client)
    monkeypatch.setattr(
        "gltest.contracts.contract.get_general_config",
        lambda: FakeGeneralConfig(),
    )
    monkeypatch.setattr(
        "gltest.fees.profile.get_general_config",
        lambda: FakeGeneralConfig(tmp_path / "fees.json"),
    )
    contract = Contract.new(
        address="0x123",
        schema={"methods": {"create_bet": {"readonly": False}}},
    )

    contract.create_bet([1]).transact()

    profile = get_fee_profile_collector().build_profile(
        network="localnet", headroom=1.0
    )
    assert profile["methods"]["create_bet"] == {
        "executionBudgetPerRound": "312500",
        "totalMessageFees": "12500",
    }


def test_deploy_records_fee_profile_observation(monkeypatch, tmp_path):
    client = FakeClient(fee_receipt(625000, 0))
    monkeypatch.setattr(
        "gltest.contracts.contract_factory.get_gl_client", lambda: client
    )
    monkeypatch.setattr(
        "gltest.contracts.contract_factory.get_general_config",
        lambda: FakeGeneralConfig(),
    )
    monkeypatch.setattr(
        "gltest.fees.profile.get_general_config",
        lambda: FakeGeneralConfig(tmp_path / "fees.json"),
    )
    factory = ContractFactory(
        contract_name="Example", contract_code="class Example: pass"
    )

    factory.deploy_contract_tx(args=["hello"])

    profile = get_fee_profile_collector().build_profile(
        network="localnet", headroom=1.0
    )
    assert profile["deploy"] == {
        "executionBudgetPerRound": "625000",
        "totalMessageFees": "0",
    }
