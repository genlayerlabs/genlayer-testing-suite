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
        monkeypatch.setattr(network_time, "_unsupported_urls", set())
        monkeypatch.setattr(network_time, "_unknown_write_urls", set())
        monkeypatch.setattr(network_time, "_modified_urls", set())
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
    assert reset_time().offset_seconds == 0
    assert get_network_time().offset_seconds == 0


def test_reset_if_supported_resets_shifted_clock(provider, monkeypatch):
    monkeypatch.setattr(network_time, "_unsupported_urls", set())
    monkeypatch.setattr(network_time, "_unknown_write_urls", set())
    monkeypatch.setattr(network_time, "_modified_urls", set())
    increase_time(60)
    network_time._reset_time_if_supported()
    assert get_network_time().offset_seconds == 0


@pytest.fixture(autouse=True)
def _fresh_support_cache(monkeypatch):
    monkeypatch.setattr(network_time, "_unsupported_urls", set())
    monkeypatch.setattr(network_time, "_unknown_write_urls", set())
    monkeypatch.setattr(network_time, "_modified_urls", set())


def test_method_not_found_is_cached_per_url(monkeypatch):
    calls = []

    class _NoMethod:
        def make_request(self, method, params):
            calls.append(method)
            raise RuntimeError("sim_getTime failed (code=-32601): Method not found")

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _NoMethod())
    network_time._reset_time_if_supported()
    network_time._reset_time_if_supported()
    assert calls == ["sim_getTime"]  # definitive answer: probed once


def test_unreachable_endpoint_is_skipped_but_not_cached(monkeypatch):
    import requests

    calls = []

    class _Down:
        def make_request(self, method, params):
            calls.append(method)
            raise requests.exceptions.ConnectionError(
                "HTTPConnectionPool: Max retries exceeded (Caused by NewConnectionError: [Errno 111] Connection refused)"
            )

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Down())
    network_time._reset_time_if_supported()
    network_time._reset_time_if_supported()
    assert calls == ["sim_getTime", "sim_getTime"]
    assert not network_time._unsupported_urls


def test_transient_failure_recovers_and_resets(monkeypatch):
    state = {"offset": 60, "fail": 1}

    class _Flaky:
        def make_request(self, method, params):
            if state["fail"]:
                state["fail"] -= 1
                raise TimeoutError("timed out")
            if method == "sim_increaseTime":
                state["offset"] += params[0]
            return {"result": {
                "total_offset_seconds": state["offset"],
                "effective_datetime": "2030-01-01T00:00:00+00:00",
            }}

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Flaky())
    network_time._reset_time_if_supported()  # first probe times out, retry works
    assert state["offset"] == 0
    assert not network_time._unsupported_urls


def test_persistent_transient_failure_is_raised(monkeypatch):
    class _Timeout:
        def make_request(self, method, params):
            raise TimeoutError("timed out")

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Timeout())
    with pytest.raises(HelperError):
        network_time._reset_time_if_supported()
    assert not network_time._unsupported_urls


def test_reset_if_supported_raises_when_reset_fails(monkeypatch):
    class _Flaky:
        def make_request(self, method, params):
            if method == "sim_increaseTime":
                raise RuntimeError("boom")
            return {"result": {
                "total_offset_seconds": 60,
                "effective_datetime": "2030-01-01T00:00:00+00:00",
            }}

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Flaky())
    with pytest.raises(HelperError, match="sim_increaseTime"):
        network_time._reset_time_if_supported()


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
    with pytest.raises(HelperError, match="sim_increaseTime"):
        increase_time(60)


def test_tls_or_dropped_connection_is_not_silently_skipped(monkeypatch):
    import requests

    class _Dropped:
        def make_request(self, method, params):
            raise requests.exceptions.ConnectionError(
                "Connection aborted. RemoteDisconnected: closed without response"
            )

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Dropped())
    with pytest.raises(HelperError):
        network_time._reset_time_if_supported()
    assert not network_time._unsupported_urls


def test_accepted_connection_that_never_replies_times_out(monkeypatch):
    import socket
    import threading
    import time

    import requests

    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(5)
    port = server.getsockname()[1]
    held = []

    def accept_and_hold():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            held.append(conn)  # never answer

    threading.Thread(target=accept_and_hold, daemon=True).start()

    class _Hanging:
        def make_request(self, method, params):
            return requests.post(f"http://127.0.0.1:{port}/api", json={}).json()

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _Hanging())
    monkeypatch.setattr(network_time, "REQUEST_TIMEOUT_SECONDS", 0.3)
    start = time.monotonic()
    try:
        with pytest.raises(HelperError):
            network_time._reset_time_if_supported()
        assert time.monotonic() - start < 5
    finally:
        server.close()
        for c in held:
            c.close()


def test_timed_out_reset_write_is_not_retried(monkeypatch):
    """A write whose outcome is unknown must not be sent a second time."""
    import threading

    state = {"offset": 60}
    writes = []
    release = threading.Event()

    class _SlowWrite:
        def make_request(self, method, params):
            if method == "sim_increaseTime":
                writes.append(params[0])
                release.wait(5)  # reply (and apply) only after the deadline
                state["offset"] += params[0]
            return {"result": {
                "total_offset_seconds": state["offset"],
                "effective_datetime": "2030-01-01T00:00:00+00:00",
            }}

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _SlowWrite())
    monkeypatch.setattr(network_time, "REQUEST_TIMEOUT_SECONDS", 0.2)
    with pytest.raises(HelperError):
        network_time._reset_time_if_supported()
    # A second fixture invocation while the write is still pending must not
    # touch the clock again.
    writes_before = list(writes)
    with pytest.raises(HelperError, match="unknown outcome"):
        network_time._reset_time_if_supported()
    assert writes == writes_before
    release.set()
    import time

    time.sleep(0.2)
    assert writes == [-60]  # sent exactly once
    assert state["offset"] == 0  # no double application (would be -60)


def test_timed_out_public_write_quarantines_across_teardown_and_setup(monkeypatch):
    """increase_time() times out; later resets must not touch the clock."""
    import threading
    import time

    state = {"offset": 0}
    release = threading.Event()
    writes = []

    class _SlowWrite:
        def make_request(self, method, params):
            if method == "sim_increaseTime":
                writes.append(params[0])
                release.wait(5)
                state["offset"] += params[0]
            return {"result": {
                "total_offset_seconds": state["offset"],
                "effective_datetime": "2030-01-01T00:00:00+00:00",
            }}

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _SlowWrite())
    monkeypatch.setattr(network_time, "REQUEST_TIMEOUT_SECONDS", 0.2)
    with pytest.raises(HelperError):
        increase_time(60)
    for _ in range(2):  # teardown, then next test's setup
        with pytest.raises(HelperError, match="unknown outcome"):
            network_time._reset_time_if_supported()
    with pytest.raises(HelperError, match="unknown outcome"):
        increase_time(5)
    assert writes == [60]
    release.set()
    time.sleep(0.2)


def test_helper_change_is_tracked_for_reset(provider):
    from gltest_cli.config.general import get_general_config

    url = get_general_config().get_rpc_url()
    assert not network_time.clock_was_modified(url)
    increase_time(60)
    assert network_time.clock_was_modified(url)
    network_time._reset_time_if_supported()
    assert not network_time.clock_was_modified(url)
    assert get_network_time().offset_seconds == 0


def test_fractional_seconds_are_rejected(provider):
    with pytest.raises(ValueError):
        increase_time(0.5)
    with pytest.raises(ValueError):
        increase_time(timedelta(milliseconds=1500))
    assert increase_time(2.0).offset_seconds == 2
    assert increase_time(timedelta(seconds=3)).offset_seconds == 5


def test_refused_detected_via_context_args_and_windows_text():
    refused = ConnectionRefusedError()
    wrapped = HelperError("x")
    try:
        try:
            raise refused
        except ConnectionRefusedError:
            raise RuntimeError("wrapper")  # implicit __context__ only
    except RuntimeError as e:
        wrapped = e
    assert network_time._is_connection_refused(wrapped)
    assert network_time._is_connection_refused(OSError(OSError(), refused))
    assert network_time._is_connection_refused(
        OSError("[WinError 10061] No connection could be made because the "
                "target machine actively refused it")
    )
    assert not network_time._is_connection_refused(OSError("TLS handshake failed"))


def test_unrelated_outer_refusal_does_not_mask_timed_out_write(monkeypatch):
    import threading
    import time

    release = threading.Event()

    class _SlowWrite:
        def make_request(self, method, params):
            if method == "sim_increaseTime":
                release.wait(5)
            return {"result": {
                "total_offset_seconds": 0,
                "effective_datetime": "2030-01-01T00:00:00+00:00",
            }}

    monkeypatch.setattr(network_time, "get_gl_provider", lambda: _SlowWrite())
    monkeypatch.setattr(network_time, "REQUEST_TIMEOUT_SECONDS", 0.2)
    try:
        try:
            raise ConnectionRefusedError("[Errno 111] Connection refused")
        except ConnectionRefusedError:
            increase_time(60)  # times out while handling an unrelated refusal
    except HelperError as e:
        assert not network_time._is_connection_refused(e)
    else:
        pytest.fail("expected HelperError")
    from gltest_cli.config.general import get_general_config

    assert get_general_config().get_rpc_url() in network_time._unknown_write_urls
    release.set()
    time.sleep(0.1)
