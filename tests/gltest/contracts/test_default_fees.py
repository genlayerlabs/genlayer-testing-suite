from types import SimpleNamespace

import pytest
from eth_account import Account
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.contracts.utils import make_calldata_object
from genlayer_py.exceptions import GenLayerError
from web3.constants import ADDRESS_ZERO

from gltest.contracts.contract import Contract
from gltest.contracts.contract_factory import ContractFactory

STUDIO_DEVNET_CHAIN_ID = 61997
CUSTOM_CHAIN_ID = 424242
SELECTOR_CONTEXT = {"genvm_executor_selector": "re:^v0\\.2\\."}

GENERIC_DISTRIBUTION = {"leaderTimeunitsAllocation": 1, "executionBudgetPerRound": 2}
DEPLOY_PRESET = {
    "distribution": {"leaderTimeunitsAllocation": "10", "rotations": ["0"]},
    "messageAllocations": [{"messageType": 1, "budget": "5"}],
    "feeValue": "1000",
}
WRITE_ESTIMATE = {
    "distribution": {"leaderTimeunitsAllocation": 20},
    "feeValue": 2000,
    "fee_value": 2000,
    "messageAllocations": [{"messageType": 0, "budget": 7}],
    "policy": {"enabled": True},
}


class FakeGeneralConfig:
    def __init__(self, studio_based=True):
        self.studio_based = studio_based

    def get_default_wait_interval(self):
        return 1

    def get_default_wait_retries(self):
        return 1

    def get_leader_only(self):
        return False

    def check_studio_based_rpc(self):
        return self.studio_based


class FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def make_request(self, method, params):
        self.requests.append({"method": method, "params": params})
        if self.error is not None:
            raise self.error
        return {"result": self.response}


class FakeStudioClient:
    def __init__(
        self,
        *,
        policy_enabled=True,
        policy_error=None,
        provider=None,
        write_estimate=WRITE_ESTIMATE,
        write_error=None,
        chain_id=STUDIO_DEVNET_CHAIN_ID,
    ):
        self.local_account = Account.create()
        self.chain = SimpleNamespace(id=chain_id)
        self.provider = provider or FakeProvider({"recommendedPreset": DEPLOY_PRESET})
        self.policy_enabled = policy_enabled
        self.policy_error = policy_error
        self.write_estimate = write_estimate
        self.write_error = write_error
        self.generic_estimate_calls = 0
        self.write_estimate_calls = []
        self.deploy_contract_calls = []
        self.write_contract_calls = []

    def estimate_transaction_fees(self):
        self.generic_estimate_calls += 1
        if self.policy_error is not None:
            raise self.policy_error
        return {
            "distribution": GENERIC_DISTRIBUTION,
            "feeValue": 99,
            "fee_value": 99,
            "policy": {"enabled": self.policy_enabled},
        }

    def estimate_transaction_fees_for_write(self, **kwargs):
        self.write_estimate_calls.append(kwargs)
        if self.write_error is not None:
            raise self.write_error
        return self.write_estimate

    def deploy_contract(self, **kwargs):
        self.deploy_contract_calls.append(kwargs)
        return "0xdeploy"

    def write_contract(self, **kwargs):
        self.write_contract_calls.append(kwargs)
        return "0xwrite"

    def wait_for_transaction_receipt(self, **kwargs):
        return {
            "status": "ACCEPTED",
            "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]},
        }


def _policy_error(message, code):
    """Mirror how genlayer-py wraps a failed sim_getFeeConfig request."""
    try:
        try:
            raise GenLayerError(f"sim_getFeeConfig failed (code={code}): {message}")
        except GenLayerError as cause:
            raise GenLayerError("Fee policy estimation is not supported") from cause
    except GenLayerError as error:
        return error


def _use(monkeypatch, client, studio_based=True):
    config = FakeGeneralConfig(studio_based=studio_based)
    for module in ("contract", "contract_factory"):
        monkeypatch.setattr(f"gltest.contracts.{module}.get_gl_client", lambda: client)
        monkeypatch.setattr(
            f"gltest.contracts.{module}.get_general_config", lambda: config
        )


def _factory():
    return ContractFactory(contract_name="Example", contract_code="class Example: pass")


def _contract():
    return Contract.new(
        address="0x0000000000000000000000000000000000000123",
        schema={"methods": {"set_value": {"readonly": False}}},
    )


def test_deploy_without_fees_submits_deploy_specific_estimate(monkeypatch):
    client = FakeStudioClient()
    _use(monkeypatch, client)

    _factory().deploy_contract_tx(args=["hello"], transaction_context=SELECTOR_CONTEXT)

    assert client.provider.requests == [
        {
            "method": "sim_estimateTransactionFees",
            "params": [
                {
                    "type": "deploy",
                    "to": ADDRESS_ZERO,
                    "from": client.local_account.address,
                    "data": serialize(
                        [
                            "class Example: pass",
                            calldata.encode(
                                make_calldata_object(
                                    method=None, args=["hello"], kwargs=None
                                )
                            ),
                            False,
                        ]
                    ),
                    "sim_config": SELECTOR_CONTEXT,
                }
            ],
        }
    ]
    assert client.deploy_contract_calls[0]["fees"] == DEPLOY_PRESET
    assert client.deploy_contract_calls[0]["sim_config"] == SELECTOR_CONTEXT


def test_deploy_estimate_uses_explicit_account(monkeypatch):
    client = FakeStudioClient()
    _use(monkeypatch, client)
    account = Account.create()

    _factory().deploy_contract_tx(account=account)

    request = client.provider.requests[0]["params"][0]
    assert request["from"] == account.address
    assert "sim_config" not in request


def test_write_without_fees_submits_write_specific_estimate(monkeypatch):
    client = FakeStudioClient()
    _use(monkeypatch, client)
    contract = _contract()

    contract.set_value([1]).transact(value=5, transaction_context=SELECTOR_CONTEXT)

    assert client.write_estimate_calls == [
        {
            "address": contract.address,
            "function_name": "set_value",
            "account": None,
            "args": [1],
            "value": 5,
            "leader_only": False,
            "sim_config": SELECTOR_CONTEXT,
        }
    ]
    assert client.write_contract_calls[0]["fees"] == {
        "distribution": WRITE_ESTIMATE["distribution"],
        "feeValue": 2000,
        "messageAllocations": WRITE_ESTIMATE["messageAllocations"],
    }


def test_write_on_custom_studio_chain_uses_generic_estimate(monkeypatch):
    client = FakeStudioClient(chain_id=CUSTOM_CHAIN_ID)
    _use(monkeypatch, client)

    _contract().set_value([1]).transact()

    assert client.write_estimate_calls == []
    assert client.write_contract_calls[0]["fees"] == {
        "distribution": GENERIC_DISTRIBUTION,
        "feeValue": 99,
    }


def test_simulation_execution_failure_falls_back_to_generic_estimate(monkeypatch):
    error = GenLayerError("sim_estimateTransactionFees: execution failed")
    client = FakeStudioClient(provider=FakeProvider(error=error), write_error=error)
    _use(monkeypatch, client)
    generic = {"distribution": GENERIC_DISTRIBUTION, "feeValue": 99}

    _factory().deploy_contract_tx()
    _contract().set_value([1]).transact()

    assert client.deploy_contract_calls[0]["fees"] == generic
    assert client.write_contract_calls[0]["fees"] == generic


def test_other_estimate_errors_are_raised(monkeypatch):
    client = FakeStudioClient(write_error=GenLayerError("rate limited"))
    _use(monkeypatch, client)

    with pytest.raises(GenLayerError, match="rate limited"):
        _contract().set_value([1]).transact()
    assert client.write_contract_calls == []


@pytest.mark.parametrize(
    "client_kwargs",
    [
        {"policy_enabled": False},
        {"policy_error": _policy_error("Method not found: sim_getFeeConfig", -32601)},
    ],
    ids=["policy-disabled", "no-fee-policy-rpc"],
)
def test_gasless_backends_keep_legacy_call(monkeypatch, client_kwargs):
    client = FakeStudioClient(**client_kwargs)
    _use(monkeypatch, client)

    _factory().deploy_contract_tx()
    _contract().set_value([1]).transact()

    assert client.provider.requests == []
    assert client.write_estimate_calls == []
    assert client.deploy_contract_calls[0]["fees"] is None
    assert client.write_contract_calls[0]["fees"] is None


def test_fee_policy_lookup_failures_are_raised_and_retried(monkeypatch):
    client = FakeStudioClient(
        policy_error=_policy_error(
            "Rate limit exceeded: 30 requests per minute", -32029
        )
    )
    _use(monkeypatch, client)

    with pytest.raises(GenLayerError, match="not supported"):
        _contract().set_value([1]).transact()
    client.policy_error = None
    _contract().set_value([1]).transact()

    assert client.generic_estimate_calls == 2
    assert client.write_contract_calls[0]["fees"]["feeValue"] == 2000


def test_fee_policy_is_looked_up_once_per_client(monkeypatch):
    client = FakeStudioClient()
    _use(monkeypatch, client)

    _factory().deploy_contract_tx()
    _contract().set_value([1]).transact()
    _contract().set_value([2]).transact()

    assert client.generic_estimate_calls == 1
    assert len(client.provider.requests) == 1
    assert len(client.write_estimate_calls) == 2


def test_non_studio_backends_are_not_quoted(monkeypatch):
    client = FakeStudioClient()
    _use(monkeypatch, client, studio_based=False)

    _factory().deploy_contract_tx()
    _contract().set_value([1]).transact()

    assert client.generic_estimate_calls == 0
    assert client.deploy_contract_calls[0]["fees"] is None
    assert client.write_contract_calls[0]["fees"] is None


@pytest.mark.parametrize(
    "fee_kwargs, expected",
    [
        (
            {"fees": {"distribution": {"leaderTimeunitsAllocation": 3}}},
            {"distribution": {"leaderTimeunitsAllocation": 3}},
        ),
        ({"fee_value": 0}, {"feeValue": 0}),
    ],
    ids=["explicit-fees", "explicit-fee-value"],
)
def test_explicit_fee_arguments_are_not_replaced(monkeypatch, fee_kwargs, expected):
    client = FakeStudioClient()
    _use(monkeypatch, client)

    _factory().deploy_contract_tx(**fee_kwargs)
    _contract().set_value([1]).transact(**fee_kwargs)

    assert client.generic_estimate_calls == 0
    assert client.deploy_contract_calls[0]["fees"] == expected
    assert client.write_contract_calls[0]["fees"] == expected
