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




def _request(method: str, params: list) -> NetworkTime:
    try:
        result = get_gl_provider().make_request(method=method, params=params)["result"]
    except HelperError:
        raise
    except Exception as e:
        raise HelperError(
            f"{method} failed: {e}. Network time manipulation requires a "
            "network that supports it (e.g. glsim)."
        ) from e
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


def _cause_chain(error: BaseException):
    while error is not None:
        yield error
        error = error.__cause__


def _is_method_unavailable(error: HelperError) -> bool:
    text = str(error).lower()
    return "code=-32601" in text or "method not found" in text


def _is_unreachable(error: HelperError) -> bool:
    """Connection refused / DNS failure: nothing is listening, so no clock."""
    causes = list(_cause_chain(error))
    if any(isinstance(c, requests.exceptions.Timeout) for c in causes):
        return False
    return any(
        isinstance(c, (requests.exceptions.ConnectionError, ConnectionError))
        for c in causes
    )


def _reset_time_if_supported() -> None:
    """
    Reset the clock to wall time on a backend that supports it.

    * A definitive "method not found" answer marks the configured endpoint as
      unsupported (cached per URL) and the reset is skipped from then on.
    * An unreachable endpoint (connection refused) is skipped for this call
      only, so tests that do not need a network keep working and a localnet
      started later is still reset.
    * Any other failure (timeout, 5xx, ...) is retried once and then raised,
      so a stale clock is never silently left behind.
    """
    url = get_general_config().get_rpc_url()
    if url in _unsupported_urls:
        return
    for attempt in (1, 2):
        try:
            reset_time()
            return
        except HelperError as e:
            if _is_method_unavailable(e):
                _unsupported_urls.add(url)
                return
            if _is_unreachable(e):
                return
            if attempt == 2:
                raise
