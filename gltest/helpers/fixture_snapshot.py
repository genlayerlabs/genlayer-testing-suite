from typing import TypeVar, Callable, List, Any
from dataclasses import dataclass
from .take_snapshot import SnapshotRestorer, take_snapshot
from gltest.exceptions import (
    FixtureSnapshotError,
    InvalidSnapshotError,
    FixtureAnonymousFunctionError,
)
from gltest_cli.config.general import get_general_config

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
    if not general_config.check_local_rpc():
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
