import inspect
from typing import Any, Callable, Dict, List, Literal

from gltest.types import (
    GenLayerTransaction,
    ProtocolTransactionStatus,
    TransactionTree,
)

DEFAULT_TRIGGERED_TRANSACTIONS_DEPTH = 1


def _status_text(status: Any) -> str:
    """Normalize an enum member, its value, or a bare string to one form."""
    return str(getattr(status, "value", status)).upper()


def wait_until_from_status(
    status: ProtocolTransactionStatus,
) -> Literal["decided", "finalized"]:
    if _status_text(status) == _status_text(ProtocolTransactionStatus.FINALIZED):
        return "finalized"
    return "decided"


def _status_from_wait_until(wait_until: Literal["decided", "finalized"]):
    if wait_until == "finalized":
        return ProtocolTransactionStatus.FINALIZED
    return ProtocolTransactionStatus.ACCEPTED


def _accepts_var_kwargs(call: Callable) -> bool:
    return any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in inspect.signature(call).parameters.values()
    )


def wait_for_transaction_receipt(
    client,
    *,
    transaction_hash: str,
    wait_until: Literal["decided", "finalized"],
    interval: int,
    retries: int,
):
    call = client.wait_for_transaction_receipt
    parameters = inspect.signature(call).parameters
    kwargs = {
        "transaction_hash": transaction_hash,
        "interval": interval,
        "retries": retries,
    }

    if "wait_until" in parameters or (
        "status" not in parameters and _accepts_var_kwargs(call)
    ):
        kwargs["wait_until"] = wait_until
    else:
        kwargs["status"] = _status_from_wait_until(wait_until)

    if "full_transaction" in parameters:
        kwargs["full_transaction"] = True

    return call(**kwargs)


def validate_triggered_transactions_depth(depth: int) -> None:
    if depth < 0:
        raise ValueError("wait_triggered_transactions_depth must be >= 0")


def wait_for_triggered_transactions(
    client,
    receipt: GenLayerTransaction,
    *,
    status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED,
    depth: int = DEFAULT_TRIGGERED_TRANSACTIONS_DEPTH,
    interval: int,
    retries: int,
) -> List[TransactionTree]:
    """Wait for the transactions triggered by ``receipt``, recursively.

    Follows ``triggered_transactions`` up to ``depth`` levels below ``receipt``
    (``depth=1`` waits only for direct children). Every path is expanded to
    the full depth; each hash is still waited for at most once (receipts are
    cached). Returns one ``TransactionTree`` per direct child.
    """
    validate_triggered_transactions_depth(depth)
    receipts: Dict[str, GenLayerTransaction] = {}

    def _receipt(tx_hash: str) -> GenLayerTransaction:
        if tx_hash not in receipts:
            receipts[tx_hash] = wait_for_transaction_receipt(
                client,
                transaction_hash=tx_hash,
                wait_until=wait_until_from_status(status),
                interval=interval,
                retries=retries,
            )
        return receipts[tx_hash]

    def _children(
        current: GenLayerTransaction, remaining: int
    ) -> List[TransactionTree]:
        if remaining <= 0:
            return []
        trees = []
        for tx_hash in current.get("triggered_transactions") or []:
            child_receipt = _receipt(tx_hash)
            trees.append(
                TransactionTree(
                    receipt=child_receipt,
                    children=_children(child_receipt, remaining - 1),
                )
            )
        return trees

    return _children(receipt, depth)
