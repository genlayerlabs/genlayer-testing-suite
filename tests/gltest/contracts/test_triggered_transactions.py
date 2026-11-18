import pytest

from gltest.contracts.contract import Contract
from gltest.contracts.contract_factory import ContractFactory
from gltest.types import TransactionStatus, TransactionTree
from gltest.contracts.wait import wait_for_triggered_transactions as _wait_triggered
from gltest.utils import wait_for_transaction


def wait_for_triggered_transactions(client, receipt, interval=1, retries=1, **kwargs):
    return _wait_triggered(
        client, receipt, interval=interval, retries=retries, **kwargs
    )


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
    """Client whose receipts form a triggered-transaction graph.

    0xroot -> [0xa, 0xb]; 0xa -> [0xa1]; 0xa1 -> [0xa1x]; 0xb -> [0xa] (dup)
    """

    GRAPH = {
        "0xroot": ["0xa", "0xb"],
        "0xa": ["0xa1"],
        "0xa1": ["0xa1x"],
        "0xb": ["0xa"],
        "0xa1x": [],
    }

    def __init__(self, root="0xroot"):
        self.root = root
        self.write_contract_calls = []
        self.waited = []
        self.wait_calls = []

    def write_contract(self, **kwargs):
        self.write_contract_calls.append(kwargs)
        return self.root

    def deploy_contract(self, **kwargs):
        return self.root

    # Same signature as genlayer-py 0.19 GenLayerClient.wait_for_transaction_receipt
    def wait_for_transaction_receipt(
        self,
        transaction_hash,
        wait_until="decided",
        interval=3000,
        retries=10,
        full_transaction=False,
    ):
        tx_hash = transaction_hash
        self.waited.append(tx_hash)
        self.wait_calls.append(
            {
                "transaction_hash": transaction_hash,
                "wait_until": wait_until,
                "interval": interval,
                "retries": retries,
            }
        )
        return {
            "hash": tx_hash,
            "status": "ACCEPTED",
            "triggered_transactions": list(self.GRAPH.get(tx_hash, [])),
            "data": {"contract_address": "0xcontract"},
            "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]},
        }


@pytest.fixture
def client(monkeypatch):
    client = FakeClient()
    for module in ("gltest.contracts.contract", "gltest.contracts.contract_factory"):
        monkeypatch.setattr(f"{module}.get_gl_client", lambda: client)
        monkeypatch.setattr(f"{module}.get_general_config", lambda: FakeGeneralConfig())
    monkeypatch.setattr("gltest.clients.get_gl_client", lambda: client)
    monkeypatch.setattr(
        "gltest_cli.config.general.get_general_config", lambda: FakeGeneralConfig()
    )
    return client


def _contract():
    return Contract.new(
        address="0x123",
        schema={"methods": {"set_value": {"readonly": False}}},
    )


def test_wait_for_triggered_transactions_respects_depth(client):
    root = {"triggered_transactions": ["0xa", "0xb"]}

    trees = wait_for_triggered_transactions(client, root, depth=1)
    assert [t.hash for t in trees] == ["0xa", "0xb"]
    assert all(t.children == [] for t in trees)
    assert client.waited == ["0xa", "0xb"]

    client.waited.clear()
    trees = wait_for_triggered_transactions(client, root, depth=2)
    # each hash is waited for once, even though 0xa is reachable via 0xb too
    assert client.waited == ["0xa", "0xa1", "0xb"]
    assert [c.hash for c in trees[0].children] == ["0xa1"]
    assert [c.hash for c in trees[1].children] == ["0xa"]

    client.waited.clear()
    assert wait_for_triggered_transactions(client, root, depth=0) == []
    assert client.waited == []


def test_wait_for_triggered_transactions_uses_status(client):
    wait_for_triggered_transactions(
        client,
        {"triggered_transactions": ["0xa1x"]},
        status=TransactionStatus.FINALIZED,
        interval=5,
        retries=7,
    )
    assert client.wait_calls == [
        {
            "transaction_hash": "0xa1x",
            "wait_until": "finalized",
            "interval": 5,
            "retries": 7,
        }
    ]


def test_wait_for_triggered_transactions_rejects_negative_depth(client):
    with pytest.raises(ValueError):
        wait_for_triggered_transactions(client, {}, depth=-1)


def test_transact_waits_for_nested_triggered_transactions(client):
    receipt = (
        _contract()
        .set_value([1])
        .transact(
            wait_triggered_transactions=True,
            wait_triggered_transactions_depth=3,
        )
    )
    assert receipt["hash"] == "0xroot"
    assert client.waited == ["0xroot", "0xa", "0xa1", "0xa1x", "0xb"]


def test_transact_does_not_wait_for_triggered_by_default(client):
    _contract().set_value([1]).transact()
    assert client.waited == ["0xroot"]


def test_deploy_waits_for_nested_triggered_transactions(client):
    factory = ContractFactory(contract_name="C", contract_code="code")
    factory.deploy_contract_tx(
        wait_triggered_transactions=True,
        wait_triggered_transactions_depth=2,
    )
    assert client.waited == ["0xroot", "0xa", "0xa1", "0xb"]


def test_raw_transact_returns_hash_without_waiting(client):
    tx_hash = _contract().set_value([1]).raw_transact(fees={"x": 1}, fee_value=3)
    assert tx_hash == "0xroot"
    assert client.waited == []
    assert client.write_contract_calls[0]["function_name"] == "set_value"
    assert client.write_contract_calls[0]["args"] == [1]


def test_raw_transact_rejects_read_only():
    contract = Contract.new(
        address="0x123", schema={"methods": {"get_value": {"readonly": True}}}
    )
    with pytest.raises(ValueError):
        contract.get_value().raw_transact()


def test_wait_for_transaction_returns_tree(client):
    tx_hash = _contract().set_value([1]).raw_transact()

    tree = wait_for_transaction(tx_hash)
    assert isinstance(tree, TransactionTree)
    assert tree.hash == "0xroot"
    assert tree.children == []

    client.waited.clear()
    tree = wait_for_transaction(
        tx_hash,
        wait_triggered_transactions=True,
        wait_triggered_transactions_depth=3,
    )
    assert [r["hash"] for r in tree.flatten()] == [
        "0xroot",
        "0xa",
        "0xa1",
        "0xa1x",
        "0xb",
    ]
    assert [r["hash"] for r in tree.triggered_receipts()] == [
        "0xa",
        "0xa1",
        "0xa1x",
        "0xb",
    ]


class DiamondClient(FakeClient):
    # root -> [a, b]; a -> [b]; b -> [c]
    GRAPH = {"0xroot": ["0xa", "0xb"], "0xa": ["0xb"], "0xb": ["0xc"], "0xc": []}


def test_shared_child_is_expanded_within_depth_on_every_path():
    client = DiamondClient()
    root = {"triggered_transactions": ["0xa", "0xb"]}

    trees = wait_for_triggered_transactions(client, root, depth=2)

    assert sorted(client.waited) == ["0xa", "0xb", "0xc"]
    assert len(client.waited) == 3  # no hash waited for twice
    assert [t.hash for t in trees] == ["0xa", "0xb"]
    assert [c.hash for c in trees[0].children] == ["0xb"]
    assert trees[0].children[0].children == []  # depth exhausted on a -> b
    assert [c.hash for c in trees[1].children] == ["0xc"]

    tree = TransactionTree(receipt={"hash": "0xroot"}, children=trees)
    assert [r["hash"] for r in tree.triggered_receipts()] == ["0xa", "0xb", "0xc"]


def test_self_triggering_transaction_terminates_at_depth():
    class LoopClient(FakeClient):
        GRAPH = {"0xloop": ["0xloop"]}

    client = LoopClient()
    trees = wait_for_triggered_transactions(
        client, {"triggered_transactions": ["0xloop"]}, depth=3
    )
    assert client.waited == ["0xloop"]
    assert trees[0].children[0].children[0].children == []


def test_triggered_wait_supports_status_only_sdk():
    """genlayer-py 0.18-style clients take ``status`` instead of ``wait_until``."""
    calls = []

    class LegacySdkClient:
        def wait_for_transaction_receipt(
            self,
            transaction_hash,
            status=TransactionStatus.ACCEPTED,
            interval=1,
            retries=1,
            full_transaction=False,
        ):
            calls.append((transaction_hash, status))
            return {"hash": transaction_hash, "triggered_transactions": []}

    wait_for_triggered_transactions(
        LegacySdkClient(),
        {"triggered_transactions": ["0x1"]},
        status=TransactionStatus.FINALIZED,
    )
    assert calls == [("0x1", TransactionStatus.FINALIZED)]


def test_helpers_work_with_real_genlayer_py_client(monkeypatch):
    """Exercise the real SDK wait_for_transaction_receipt signature/implementation."""
    from genlayer_py import create_client
    from genlayer_py.chains import localnet

    sdk_client = create_client(chain=localnet)
    graph = {"0xroot": ["0xa"], "0xa": ["0xb"], "0xb": []}
    seen = []

    def get_transaction(transaction_hash):
        seen.append(transaction_hash)
        return {
            "hash": transaction_hash,
            "lifecycle": {"state": "finalized"},
            "triggered_transactions": graph[transaction_hash],
        }

    monkeypatch.setattr(sdk_client, "get_transaction", get_transaction)
    monkeypatch.setattr("gltest.clients.get_gl_client", lambda: sdk_client)
    monkeypatch.setattr(
        "gltest_cli.config.general.get_general_config", lambda: FakeGeneralConfig()
    )

    tree = wait_for_transaction(
        "0xroot",
        wait_until="finalized",
        wait_triggered_transactions=True,
        wait_triggered_transactions_status=TransactionStatus.FINALIZED,
    )

    assert [r["hash"] for r in tree.flatten()] == ["0xroot", "0xa", "0xb"]
    assert seen == ["0xroot", "0xa", "0xb"]
