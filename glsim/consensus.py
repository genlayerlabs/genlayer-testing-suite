"""Consensus simulation for glsim.

Runs one leader + N validators per transaction. Validators check each
captured run_nondet result. Majority vote determines outcome. Rotates
leader on disagreement.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import SimEngine

from .state import TxStatus


@dataclass
class ConsensusResult:
    status: TxStatus
    result: Any = None
    error: Optional[str] = None
    result_bytes: bytes = b""
    votes: List[str] = field(default_factory=list)
    rotation: int = 0


def run_consensus(
    engine: SimEngine,
    execute_fn: Callable[[], Tuple[Any, bytes]],
    num_validators: int,
    max_rotations: int,
) -> ConsensusResult:
    """Run leader + validator consensus with rotation on disagreement.

    Args:
        engine: SimEngine (has .vm with _captured_validators, snapshots).
        execute_fn: Runs the contract operation. Returns (result, result_bytes)
            on success, raises on failure. Populates vm._captured_validators.
        num_validators: Number of validators (1 = leader-only, auto-agree).
        max_rotations: Max leader rotations before UNDETERMINED.
    """
    if max_rotations < 1:
        max_rotations = 1

    for rotation in range(max_rotations):
        # Snapshot for potential rollback
        state_snap = engine.create_snapshot()
        storage_snap = _snapshot_storages(engine)

        engine.vm._captured_validators.clear()

        # --- Leader execution ---
        result = None
        result_bytes = b""
        error = None
        try:
            result, result_bytes = execute_fn()
        except Exception as exc:
            error = str(exc)

        captured = list(engine.vm._captured_validators)

        # --- Validator voting ---
        if num_validators <= 1:
            votes = ["agree"]
        elif not captured:
            # No run_nondet calls → deterministic → all agree
            votes = ["agree"] * num_validators
        else:
            votes = _run_validators(engine.vm, captured, num_validators)

        agree_count = sum(1 for v in votes if v == "agree")
        majority = num_validators // 2 + 1

        if agree_count >= majority:
            return ConsensusResult(
                status=TxStatus.FINALIZED,
                result=result,
                error=error,
                result_bytes=result_bytes,
                votes=votes,
                rotation=rotation,
            )

        # Majority disagreed → restore and rotate
        _restore_storages(engine, storage_snap, state_snap)

    # Exhausted all rotations
    return ConsensusResult(
        status=TxStatus.UNDETERMINED,
        result=result,
        error=error or "No consensus after max rotations",
        result_bytes=result_bytes,
        votes=votes,
        rotation=max_rotations - 1,
    )


def _run_validators(vm, captured, num_validators):
    """Run captured validator_fns for each validator. Returns list of votes."""
    import genlayer.gl.vm as gl_vm

    votes = []
    for _ in range(num_validators):
        all_agree = True
        for stored_result, _leader_fn, validator_fn in captured:
            try:
                wrapped = gl_vm.Return(calldata=stored_result)
                if not validator_fn(wrapped):
                    all_agree = False
                    break
            except Exception:
                all_agree = False
                break
        votes.append("agree" if all_agree else "disagree")
    return votes


def _snapshot_storages(engine):
    """Deep-copy contract storages for rotation rollback."""
    return {
        "storages": copy.deepcopy(engine._storages),
        "vm_storage": copy.deepcopy(engine.vm._storage),
        "instances_keys": set(engine._instances.keys()),
        "classes_keys": set(engine._classes.keys()),
    }


def _restore_storages(engine, snap, state_snap_id):
    """Restore storages + state-store for rotation."""
    engine.restore_snapshot(state_snap_id)
    engine._storages = snap["storages"]
    engine.vm._storage = snap["vm_storage"]
    for k in list(engine._instances.keys()):
        if k not in snap["instances_keys"]:
            del engine._instances[k]
    for k in list(engine._classes.keys()):
        if k not in snap["classes_keys"]:
            del engine._classes[k]
