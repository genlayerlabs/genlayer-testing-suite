import inspect
from typing import Callable, Literal

from gltest.types import TransactionStatus


def wait_until_from_status(
    status: TransactionStatus,
) -> Literal["decided", "finalized"]:
    if status == TransactionStatus.FINALIZED:
        return "finalized"
    return "decided"


def _status_from_wait_until(wait_until: Literal["decided", "finalized"]):
    if wait_until == "finalized":
        return TransactionStatus.FINALIZED
    return TransactionStatus.ACCEPTED


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
