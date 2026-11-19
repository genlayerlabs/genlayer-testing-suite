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

from gltest.clients import get_gl_provider
from gltest.exceptions import HelperError


@dataclass(frozen=True)
class NetworkTime:
    """Current clock state of the network."""

    offset_seconds: int
    """Seconds added to the wall clock by the network."""

    datetime: datetime
    """Effective "now" seen by contracts (timezone-aware)."""


# True while the network clock may differ from what it was before the current
# test touched it. Used by the autouse fixture to only reset when needed.
_time_modified = False


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
    global _time_modified
    delta = _to_seconds(seconds)
    if delta == 0:
        return get_network_time()
    result = _request("sim_increaseTime", [delta])
    _time_modified = True
    return result


def set_time(when: Union[datetime, str]) -> NetworkTime:
    """
    Set the network clock to an absolute datetime (``datetime`` or ISO 8601
    string). Naive datetimes are interpreted as UTC. The clock keeps ticking
    from there.
    """
    global _time_modified
    if isinstance(when, datetime):
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        when = when.isoformat()
    elif not isinstance(when, str):
        raise TypeError("when must be a datetime or an ISO 8601 string")
    result = _request("sim_setTime", [when])
    _time_modified = True
    return result


def reset_time() -> NetworkTime:
    """Remove any offset so the network clock matches the wall clock again."""
    global _time_modified
    current = get_network_time()
    if current.offset_seconds != 0:
        current = _request("sim_increaseTime", [-current.offset_seconds])
    _time_modified = False
    return current


def _reset_time_if_modified() -> None:
    """Reset the network clock only if a helper in this process changed it."""
    if _time_modified:
        reset_time()


def _reset_time_if_supported() -> None:
    """Reset the clock to wall time; silently do nothing if unsupported."""
    try:
        reset_time()
    except HelperError:
        pass
