"""Tests for time manipulation RPC methods (sim_increaseTime, sim_setTime, sim_getTime).

Anvil-style cumulative time offset for glsim.
"""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TIME_CONTRACT = str(
    Path(__file__).parent.parent / "examples" / "contracts" / "simple_time_contract.py"
)


@pytest.fixture
def client():
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(num_validators=1, verbose=True)
    with TestClient(app) as c:
        yield c


def _rpc(client, method, params=None, req_id=1):
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params is not None:
        payload["params"] = params
    resp = client.post("/api", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    return data


class TestSimIncreaseTime:
    """Test sim_increaseTime RPC method."""

    def test_basic_increase(self, client):
        """sim_increaseTime advances the offset by given seconds."""
        data = _rpc(client, "sim_increaseTime", [3600])
        assert "result" in data
        assert data["result"]["total_offset_seconds"] == 3600

    def test_cumulative(self, client):
        """Multiple calls accumulate the offset."""
        _rpc(client, "sim_increaseTime", [100])
        data = _rpc(client, "sim_increaseTime", [200])
        assert data["result"]["total_offset_seconds"] == 300

    def test_returns_effective_datetime(self, client):
        """Response includes the effective datetime."""
        data = _rpc(client, "sim_increaseTime", [86400])
        effective = datetime.fromisoformat(data["result"]["effective_datetime"])
        expected = datetime.now(timezone.utc) + timedelta(days=1)
        # Within 5 seconds tolerance
        assert abs((effective - expected).total_seconds()) < 5

    def test_missing_param(self, client):
        """Error when seconds not provided."""
        data = _rpc(client, "sim_increaseTime", [])
        assert "error" in data


class TestSimSetTime:
    """Test sim_setTime RPC method."""

    def test_set_future(self, client):
        """Set time to a specific future datetime."""
        target = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        data = _rpc(client, "sim_setTime", [target])
        assert "result" in data
        effective = datetime.fromisoformat(data["result"]["effective_datetime"])
        expected = datetime.fromisoformat(target)
        assert abs((effective - expected).total_seconds()) < 5

    def test_set_past(self, client):
        """Set time to a past datetime (negative offset)."""
        target = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        data = _rpc(client, "sim_setTime", [target])
        assert data["result"]["total_offset_seconds"] < 0

    def test_overrides_increase(self, client):
        """sim_setTime replaces any existing offset from sim_increaseTime."""
        _rpc(client, "sim_increaseTime", [99999])
        target = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        data = _rpc(client, "sim_setTime", [target])
        # Should be ~3600, not ~103599
        assert abs(data["result"]["total_offset_seconds"] - 3600) < 5


class TestSimGetTime:
    """Test sim_getTime RPC method."""

    def test_initial_zero(self, client):
        """Initially offset is zero."""
        data = _rpc(client, "sim_getTime")
        assert data["result"]["total_offset_seconds"] == 0

    def test_after_increase(self, client):
        """Reflects offset after sim_increaseTime."""
        _rpc(client, "sim_increaseTime", [42])
        data = _rpc(client, "sim_getTime")
        assert data["result"]["total_offset_seconds"] == 42


class TestTimeAffectsContracts:
    """Test that time offset actually affects contract execution."""

    def test_contract_sees_warped_time(self, client):
        """Deploy a time-dependent contract and verify time offset affects it."""
        # Deploy with start date 10 days ago
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=10)).isoformat()
        deploy = _rpc(client, "sim_deploy", {
            "code_path": TIME_CONTRACT,
            "args": [start_date],
        })
        assert "result" in deploy
        addr = deploy["result"]["contract_address"]

        # Read status — should show ~10 days since start
        status = _rpc(client, "sim_read", {
            "to": addr,
            "method": "get_status",
        })
        assert "result" in status
        days = status["result"]["result"]["days_since_start"]
        assert 9 <= days <= 11  # ~10 days

        # Advance time by 25 days
        _rpc(client, "sim_increaseTime", [25 * 86400])

        # Read again — should show ~35 days since start
        status = _rpc(client, "sim_read", {
            "to": addr,
            "method": "get_status",
        })
        days = status["result"]["result"]["days_since_start"]
        assert 34 <= days <= 36  # ~35 days

    def test_block_timestamp_uses_offset(self, client):
        """eth_getBlockByNumber returns timestamp with offset applied."""
        before = _rpc(client, "eth_getBlockByNumber", ["latest", False])
        ts_before = int(before["result"]["timestamp"], 16)

        # Jump forward 1 day
        _rpc(client, "sim_increaseTime", [86400])

        after = _rpc(client, "eth_getBlockByNumber", ["latest", False])
        ts_after = int(after["result"]["timestamp"], 16)

        # Timestamp should have jumped ~86400 seconds
        diff = ts_after - ts_before
        assert 86390 <= diff <= 86410


class TestTimeWithSnapshots:
    """Test that time offset is preserved across snapshots."""

    def test_snapshot_preserves_offset(self, client):
        """Snapshot captures time offset and restore reverts it."""
        _rpc(client, "sim_increaseTime", [5000])

        # Create snapshot
        snap = _rpc(client, "sim_createSnapshot")
        snap_id = snap["result"]

        # Change time further
        _rpc(client, "sim_increaseTime", [10000])
        data = _rpc(client, "sim_getTime")
        assert data["result"]["total_offset_seconds"] == 15000

        # Restore snapshot
        _rpc(client, "sim_restoreSnapshot", [snap_id])
        data = _rpc(client, "sim_getTime")
        assert data["result"]["total_offset_seconds"] == 5000
