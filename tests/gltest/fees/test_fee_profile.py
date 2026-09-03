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


def studio_fee_accounting_receipt(
    *,
    execution_consumed=100,
    execution_report_total=200,
    message_consumed=10,
    genvm_message_consumed=7,
    leader_timeunits=100,
    validator_timeunits=200,
    rotations=None,
):
    if rotations is None:
        rotations = [0]
    return {
        "status": "ACCEPTED",
        "data": {
            "fee_accounting": {
                "fees_distribution": {
                    "leaderTimeunitsAllocation": str(leader_timeunits),
                    "validatorTimeunitsAllocation": str(validator_timeunits),
                    "rotations": [str(rotation) for rotation in rotations],
                },
                "execution_fee_consumed": str(execution_consumed),
                "message_fee_consumed": str(message_consumed),
                "genvm_message_fee_consumed": str(genvm_message_consumed),
                "execution_fee_report": {
                    "totalEstimatedFee": str(execution_report_total),
                },
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

    profile = collector.build_profile(
        network="localnet", headroom=1.25, chain_id=61127
    )

    assert profile["version"] == 1
    assert profile["network"] == "localnet"
    assert profile["chainId"] == 61127
    assert profile["deploy"] == {
        "leaderTimeunitsAllocation": "125",
        "validatorTimeunitsAllocation": "250",
        "executionBudgetPerRound": "127",
        "totalMessageFees": "13",
    }
    assert profile["methods"]["create_bet"] == {
        "leaderTimeunitsAllocation": "125",
        "validatorTimeunitsAllocation": "250",
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


def test_current_studio_fee_accounting_shape_is_recorded():
    collector = FeeProfileCollector()
    collector.record_method("resolve_bet", studio_fee_accounting_receipt())

    profile = collector.build_profile(network="localnet", headroom=1.25)

    assert profile["methods"]["resolve_bet"] == {
        "leaderTimeunitsAllocation": "125",
        "validatorTimeunitsAllocation": "250",
        "executionBudgetPerRound": "375",
        "totalMessageFees": "13",
        "rotationsPerRound": "0",
    }


def test_method_profile_uses_per_field_maxima_across_branches():
    collector = FeeProfileCollector()
    collector.record_method(
        "complex_action",
        studio_fee_accounting_receipt(
            execution_consumed=500,
            execution_report_total=100,
            message_consumed=0,
            genvm_message_consumed=0,
            leader_timeunits=100,
            validator_timeunits=200,
            rotations=[0],
        ),
    )
    collector.record_method(
        "complex_action",
        studio_fee_accounting_receipt(
            execution_consumed=100,
            execution_report_total=100,
            message_consumed=800,
            genvm_message_consumed=750,
            leader_timeunits=80,
            validator_timeunits=150,
            rotations=[1],
        ),
    )

    profile = collector.build_profile(network="localnet", headroom=1.0)

    assert profile["methods"]["complex_action"] == {
        "leaderTimeunitsAllocation": "100",
        "validatorTimeunitsAllocation": "200",
        "executionBudgetPerRound": "600",
        "totalMessageFees": "800",
        "rotationsPerRound": "1",
    }


def test_nested_leader_fee_accounting_shape_is_recorded():
    collector = FeeProfileCollector()
    collector.record_method(
        "resolve_bet",
        {
            "consensus_data": {
                "leader_receipt": [
                    {
                        "genvm_result": {
                            "fee_accounting": {
                                "execution_fee_consumed": "50",
                                "genvm_message_fee_consumed": "9",
                            }
                        }
                    }
                ]
            }
        },
    )

    profile = collector.build_profile(network="localnet", headroom=1.0)

    assert profile["methods"]["resolve_bet"] == {
        "executionBudgetPerRound": "50",
        "totalMessageFees": "9",
    }


def test_profile_shape_includes_time_unit_keys_when_available():
    collector = FeeProfileCollector()
    collector.record_method("create_bet", fee_receipt(10, 5))

    profile = collector.build_profile(network="localnet", headroom=1.0)

    assert set(profile) == {"version", "network", "measuredAt", "methods"}
    assert profile["methods"] == {
        "create_bet": {
            "leaderTimeunitsAllocation": "100",
            "validatorTimeunitsAllocation": "200",
            "executionBudgetPerRound": "10",
            "totalMessageFees": "5",
        }
    }


def test_write_creates_parent_dirs_and_round_trips_json(tmp_path):
    collector = FeeProfileCollector()
    collector.record_deploy(fee_receipt(10, 0))
    output_path = tmp_path / "profiles" / "fees.json"

    profile = collector.write(
        output_path, network="localnet", headroom=1.25, chain_id=61127
    )

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == profile
    assert profile["chainId"] == 61127


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
        "leaderTimeunitsAllocation": "100",
        "validatorTimeunitsAllocation": "200",
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
        "leaderTimeunitsAllocation": "100",
        "validatorTimeunitsAllocation": "200",
        "executionBudgetPerRound": "625000",
        "totalMessageFees": "0",
    }
