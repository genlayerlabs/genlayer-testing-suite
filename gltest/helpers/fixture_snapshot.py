from typing import TypeVar, Callable, List, Any
from dataclasses import dataclass
from urllib.parse import urlparse
from .take_snapshot import SnapshotRestorer, take_snapshot
from gltest.exceptions import (
    FixtureSnapshotError,
    InvalidSnapshotError,
    FixtureAnonymousFunctionError,
)
from gltest_cli.config.general import get_general_config

SUPPORTED_RPC_DOMAINS = ["localhost", "127.0.0.1"]

T = TypeVar("T")


@dataclass
class Snapshot:
    """Represents a snapshot of the blockchain state."""

    restorer: SnapshotRestorer
    fixture: Callable[[], Any]
    data: Any


# Global storage for snapshots
_snapshots: List[Snapshot] = []


def load_fixture(fixture: Callable[[], T]) -> T:
    """
    Useful in tests for setting up the desired state of the network.
    """
    if fixture.__name__ == "<lambda>":
        raise FixtureAnonymousFunctionError("Fixtures must be named functions")

    general_config = get_general_config()
    rpc_url = general_config.get_rpc_url()
    domain = urlparse(rpc_url).netloc.split(":")[0]  # Extract domain without port
    if domain not in SUPPORTED_RPC_DOMAINS:
        return fixture()

    # Find existing snapshot for this fixture
    global _snapshots
    snapshot = next((s for s in _snapshots if s.fixture == fixture), None)

    if snapshot is not None:
        try:
            snapshot.restorer.restore()

            # Remove snapshots that were taken after this one
            _snapshots = [
                s
                for s in _snapshots
                if int(s.restorer.snapshot_id) <= int(snapshot.restorer.snapshot_id)
            ]
        except Exception as e:
            if isinstance(e, InvalidSnapshotError):
                raise FixtureSnapshotError(e) from e
            raise e

        return snapshot.data
    else:
        # Execute the fixture and take a snapshot
        data = fixture()
        restorer = take_snapshot()

        _snapshots.append(Snapshot(restorer=restorer, fixture=fixture, data=data))

        return data


def clear_snapshots() -> None:
    """Clears every existing snapshot."""
    global _snapshots
    _snapshots = []
