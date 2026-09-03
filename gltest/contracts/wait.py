import inspect
from typing import Any, Callable, Literal

from gltest.types import ProtocolTransactionStatus


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
