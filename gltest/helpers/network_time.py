"""
Helpers to manipulate the network clock seen by contracts during tests.

They wrap glsim's Anvil-style time RPCs (``sim_increaseTime``, ``sim_setTime``,
``sim_getTime``): the network keeps a cumulative offset that is added to the
wall clock for every subsequent transaction, call and block timestamp, until
it is changed again or reset.

Any change made through these helpers is undone automatically after each test
by the ``gltest`` pytest plugin (see ``gltest.fixtures``), so tests do not leak
a shifted clock into each other.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Union

import threading

import requests

from gltest.clients import get_gl_provider
from gltest_cli.config.general import get_general_config
from gltest.exceptions import HelperError


@dataclass(frozen=True)
class NetworkTime:
    """Current clock state of the network."""

    offset_seconds: int
    """Seconds added to the wall clock by the network."""

    datetime: datetime
    """Effective "now" seen by contracts (timezone-aware)."""




# Seconds to wait for each clock RPC. The SDK provider's HTTP request has no
# timeout of its own, so a server that accepts the connection but never answers
# would otherwise hang the whole test run.
REQUEST_TIMEOUT_SECONDS = 10.0


def _post_with_timeout(url: str, method: str, params: list):
    """JSON-RPC POST with a transport-level timeout (releases the socket)."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json", "User-Agent": "gltest"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp = response.json()
    if resp.get("error"):
        err = resp["error"]
        raise RuntimeError(
            f"{method} failed (code={err.get('code', 'unknown')}): "
            f"{err.get('message', 'unknown error')}"
        )
    return resp


def _make_request_with_deadline(method: str, params: list):
    provider = get_gl_provider()
    url = getattr(provider, "url", None)
    if isinstance(url, str):
        return _post_with_timeout(url, method, params)
    # Providers without a URL (e.g. in-process fakes): bound the wait instead.
    outcome: dict = {}

    def run():
        try:
            outcome["value"] = provider.make_request(method=method, params=params)
        except BaseException as e:  # noqa: BLE001 - re-raised in the caller
            outcome["error"] = e

    worker = threading.Thread(target=run, daemon=True, name=f"gltest-{method}")
    worker.start()
    worker.join(REQUEST_TIMEOUT_SECONDS)
    if worker.is_alive():
        raise TimeoutError(f"no response within {REQUEST_TIMEOUT_SECONDS}s")
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


_MUTATING_METHODS = ("sim_increaseTime", "sim_setTime")
# RPC URLs whose clock was successfully or ambiguously changed by a helper.
_modified_urls: set = set()


def _quarantine_error(url: str) -> HelperError:
    return HelperError(
        f"A previous clock change on {url} has an unknown outcome (the "
        "request may still be applied), so the network clock is not "
        "touched again in this session. Restart the network and rerun."
    )


def _is_definitive_failure(error: BaseException) -> bool:
    """The request certainly did not change the clock."""
    text = str(error).lower()
    if "code=" in text or "method not found" in text:  # JSON-RPC error reply
        return True
    for cause in _cause_chain(error):
        if isinstance(cause, ConnectionRefusedError):
            return True
        if "connection refused" in str(cause).lower() or "errno 111" in str(cause).lower():
            return True
    return False


def raise_if_quarantined(url: str) -> None:
    """Raise if a clock write at ``url`` has an unknown outcome."""
    if url in _unknown_write_urls:
        raise _quarantine_error(url)


def clock_was_modified(url: str) -> bool:
    """True if a helper changed (or may have changed) the clock at ``url``."""
    return url in _modified_urls


def _request(method: str, params: list) -> NetworkTime:
    mutating = method in _MUTATING_METHODS
    url = get_general_config().get_rpc_url() if mutating else None
    if mutating and url in _unknown_write_urls:
        raise _quarantine_error(url)
    try:
        result = _make_request_with_deadline(method, params)["result"]
    except HelperError:
        raise
    except Exception as e:
        if mutating and not _is_definitive_failure(e):
            # Outcome unknown: the write may still land later. Stop using the
            # endpoint so it cannot be compounded or mistaken for a clean slate.
            _unknown_write_urls.add(url)
            _modified_urls.add(url)
        raise HelperError(
            f"{method} failed: {e}. Network time manipulation requires a "
            "network that supports it (e.g. glsim)."
        ) from e
    if mutating:
        _modified_urls.add(url)
    try:
        effective = datetime.fromisoformat(
            str(result["effective_datetime"]).replace("Z", "+00:00")
        )
        if effective.tzinfo is None:
            effective = effective.replace(tzinfo=timezone.utc)
        return NetworkTime(
            offset_seconds=int(result["total_offset_seconds"]),
            datetime=effective,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise HelperError(f"Unexpected {method} response: {result!r}") from e


def _to_seconds(value: Union[int, float, timedelta]) -> int:
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("seconds must be an int, float or timedelta")
    return int(value)


def get_network_time() -> NetworkTime:
    """Return the network's current time offset and effective datetime."""
    return _request("sim_getTime", [])


def increase_time(seconds: Union[int, float, timedelta]) -> NetworkTime:
    """
    Move the network clock forward by ``seconds`` (an int or a ``timedelta``).

    Cumulative: ``increase_time(timedelta(days=1))`` twice leaves the network
    two days ahead. Negative values move the clock back.
    """
    delta = _to_seconds(seconds)
    if delta == 0:
        return get_network_time()
    result = _request("sim_increaseTime", [delta])
    return result


def set_time(when: Union[datetime, str]) -> NetworkTime:
    """
    Set the network clock to an absolute datetime (``datetime`` or ISO 8601
    string). Naive datetimes are interpreted as UTC. The clock keeps ticking
    from there.
    """
    if isinstance(when, datetime):
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        when = when.isoformat()
    elif not isinstance(when, str):
        raise TypeError("when must be a datetime or an ISO 8601 string")
    result = _request("sim_setTime", [when])
    return result


def reset_time() -> NetworkTime:
    """Remove any offset so the network clock matches the wall clock again."""
    current = get_network_time()
    if current.offset_seconds != 0:
        current = _request("sim_increaseTime", [-current.offset_seconds])
    return current


# RPC URLs whose backend definitively answered "method not found" for the time
# RPCs. Only this answer is cached; transient failures never are.
_unsupported_urls: set = set()
# URLs where a relative clock write ended with an unknown outcome.
_unknown_write_urls: set = set()


def _cause_chain(error: BaseException):
    while error is not None:
        yield error
        error = error.__cause__


def _is_method_unavailable(error: HelperError) -> bool:
    text = str(error).lower()
    return "code=-32601" in text or "method not found" in text


def _is_unreachable(error: HelperError) -> bool:
    """Connection refused: nothing is listening on the endpoint, so no clock.

    Timeouts, TLS failures, dropped connections and the like are *not*
    treated as "unavailable" and are retried and then raised.
    """
    for cause in _cause_chain(error):
        if isinstance(cause, ConnectionRefusedError):
            return True
        if "connection refused" in str(cause).lower() or "errno 111" in str(cause).lower():
            return True
    return False


def _reset_time_if_supported() -> None:
    """
    Reset the clock to wall time on a backend that supports it.

    * A definitive "method not found" answer marks the configured endpoint as
      unsupported (cached per URL) and the reset is skipped from then on.
    * An endpoint refusing connections is skipped for this call
      only (connection refused), so tests that do not need a network keep working and a localnet
      started later is still reset.
    * Reads are retried once on other failures; the relative write is sent
      once only and any failure is raised, so a stale clock is never silently
      left behind and a reset is never applied twice.
    """
    url = get_general_config().get_rpc_url()
    if url in _unsupported_urls:
        return
    if url in _unknown_write_urls:
        raise _quarantine_error(url)

    def handled(error: HelperError) -> bool:
        if _is_method_unavailable(error):
            _unsupported_urls.add(url)
            return True
        return _is_unreachable(error)

    # Reading the clock is idempotent, so it may be retried.
    for attempt in (1, 2):
        try:
            current = get_network_time()
            break
        except HelperError as e:
            if handled(e):
                return
            if attempt == 2:
                raise
    if current.offset_seconds == 0:
        _modified_urls.discard(url)
        return
    # Shifting the clock is relative: it is sent exactly once. If its outcome
    # is unknown (timeout), retrying could apply it twice, so the error is
    # raised and the next test's read-first reset corrects whatever state the
    # backend ended up in.
    try:
        _request("sim_increaseTime", [-current.offset_seconds])
    except HelperError as e:
        if not handled(e):
            raise
    else:
        _modified_urls.discard(url)
