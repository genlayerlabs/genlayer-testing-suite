"""Tests for gltest network time helpers against an in-process glsim."""

from datetime import datetime, timedelta, timezone

import pytest

from gltest.exceptions import HelperError
from gltest.helpers import (
    get_network_time,
    increase_time,
    reset_time,
    set_time,
)
from gltest.helpers import network_time


class _GlsimProvider:
    """Minimal provider routing JSON-RPC requests to a glsim TestClient."""

    def __init__(self, client):
        self.client = client
        self.methods = []

    def make_request(self, method, params):
        self.methods.append(method)
        resp = self.client.post(
            "/api",
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(data["error"].get("message"))
        return data


@pytest.fixture
def provider(monkeypatch):
    from glsim.server import create_app
    from starlette.testclient import TestClient

    with TestClient(create_app(num_validators=1)) as client:
        provider = _GlsimProvider(client)
        monkeypatch.setattr(network_time, "get_gl_provider", lambda: provider)
        monkeypatch.setattr(network_time, "_time_modified", False)
        yield provider


def _close(a: datetime, b: datetime, tolerance: float = 5) -> bool:
    return abs((a - b).total_seconds()) < tolerance


def test_get_network_time_starts_at_wall_clock(provider):
    current = get_network_time()
    assert current.offset_seconds == 0
    assert _close(current.datetime, datetime.now(timezone.utc))


def test_increase_time_is_cumulative_and_accepts_timedelta(provider):
    assert increase_time(timedelta(days=1)).offset_seconds == 86400
    result = increase_time(3600)
    assert result.offset_seconds == 86400 + 3600
    assert _close(
        result.datetime, datetime.now(timezone.utc) + timedelta(days=1, hours=1)
    )
    assert get_network_time().offset_seconds == 90000


def test_increase_time_zero_does_not_mark_modified(provider):
    assert increase_time(0).offset_seconds == 0
    assert network_time._time_modified is False
    assert "sim_increaseTime" not in provider.methods


def test_set_time_with_datetime_and_string(provider):
    target = datetime.now(timezone.utc) + timedelta(weeks=1)
    assert _close(set_time(target).datetime, target)

    result = set_time("2030-01-01T00:00:00Z")
    assert _close(result.datetime, datetime(2030, 1, 1, tzinfo=timezone.utc))


def test_set_time_naive_datetime_is_utc(provider):
    result = set_time(datetime(2030, 6, 1, 12, 0, 0))
    assert _close(result.datetime, datetime(2030, 6, 1, 12, tzinfo=timezone.utc))


def test_reset_time_removes_offset(provider):
    increase_time(timedelta(days=7))
    assert network_time._time_modified is True
    assert reset_time().offset_seconds == 0
    assert get_network_time().offset_seconds == 0
    assert network_time._time_modified is False


def test_reset_if_modified_skips_rpc_when_untouched(provider):
    network_time._reset_time_if_modified()
    assert provider.methods == []


def test_reset_if_modified_resets_after_change(provider):
    increase_time(60)
    network_time._reset_time_if_modified()
    assert get_network_time().offset_seconds == 0


def test_invalid_arguments(provider):
    with pytest.raises(TypeError):
        increase_time("1 day")
    with pytest.raises(TypeError):
        set_time(12345)


def test_unsupported_network_raises_helper_error(monkeypatch):
    class _Failing:
        def make_request(self, method, params):
            raise RuntimeError("Method not found")

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Failing())
    monkeypatch.setattr(network_time, "_time_modified", False)
    with pytest.raises(HelperError, match="sim_increaseTime"):
        increase_time(60)
    assert network_time._time_modified is False
