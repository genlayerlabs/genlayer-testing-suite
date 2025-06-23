from gltest.clients import get_gl_provider
from dataclasses import dataclass
from typing import Callable
from gltest.exceptions import HelperError, InvalidSnapshotError


@dataclass
class SnapshotRestorer:
    """Class responsible for restoring blockchain state to a snapshot."""

    restore: Callable[[], None]
    snapshot_id: int


def take_snapshot() -> SnapshotRestorer:
    """
    Take a snapshot of the current blockchain state and return a function to restore the state and the snapshot ID.
    """
    provider = get_gl_provider()
    snapshot_id = provider.make_request(method="sim_createSnapshot", params=[])[
        "result"
    ]
    if not isinstance(snapshot_id, int):
        raise HelperError(
            "Assertion error: the value returned by evm_snapshot should be a int"
        )

    def restore() -> None:
        reverted = provider.make_request(
            method="sim_restoreSnapshot", params=[snapshot_id]
        )["result"]

        if not isinstance(reverted, bool):
            raise HelperError(
                "Assertion error: the value returned by evm_revert should be a boolean"
            )

        if not reverted:
            raise InvalidSnapshotError("")

    return SnapshotRestorer(restore=restore, snapshot_id=snapshot_id)
