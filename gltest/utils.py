from typing import Literal, Optional

from genlayer_py.types import GenLayerTransaction
from gltest.types import ProtocolTransactionStatus, TransactionTree


def extract_contract_address(receipt: GenLayerTransaction) -> str:
    """Extract contract address from a deployment transaction receipt."""
    if (
        "tx_data_decoded" in receipt
        and "contract_address" in receipt["tx_data_decoded"]
    ):
        return receipt["tx_data_decoded"]["contract_address"]
    elif "data" in receipt and "contract_address" in receipt["data"]:
        return receipt["data"]["contract_address"]
    else:
        raise ValueError("Transaction receipt missing contract address")


def wait_for_transaction(
    tx_hash: str,
    wait_transaction_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED,
    wait_until: Optional[Literal["decided", "finalized"]] = None,
    wait_interval: Optional[int] = None,
    wait_retries: Optional[int] = None,
    wait_triggered_transactions: bool = False,
    wait_triggered_transactions_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED,
    wait_triggered_transactions_depth: Optional[int] = None,
) -> TransactionTree:
    """Wait for a transaction (e.g. one sent with ``raw_transact``) and,
    optionally, for the transactions it triggered.

    Returns a ``TransactionTree``: ``.receipt`` is the transaction's receipt and
    ``.children`` hold the triggered transactions' receipts (empty unless
    ``wait_triggered_transactions`` is set). ``wait_triggered_transactions_depth``
    defaults to 1 (direct children only).
    """
    # Imported lazily: gltest.contracts imports this module.
    from gltest.clients import get_gl_client
    from gltest.contracts.wait import (
        DEFAULT_TRIGGERED_TRANSACTIONS_DEPTH,
        wait_for_transaction_receipt,
        wait_for_triggered_transactions,
        wait_until_from_status,
    )
    from gltest_cli.config.general import get_general_config

    general_config = get_general_config()
    interval = (
        wait_interval
        if wait_interval is not None
        else general_config.get_default_wait_interval()
    )
    retries = (
        wait_retries
        if wait_retries is not None
        else general_config.get_default_wait_retries()
    )
    client = get_gl_client()
    receipt = wait_for_transaction_receipt(
        client,
        transaction_hash=tx_hash,
        wait_until=wait_until or wait_until_from_status(wait_transaction_status),
        interval=interval,
        retries=retries,
    )
    children = []
    if wait_triggered_transactions:
        children = wait_for_triggered_transactions(
            client,
            receipt,
            status=wait_triggered_transactions_status,
            depth=(
                DEFAULT_TRIGGERED_TRANSACTIONS_DEPTH
                if wait_triggered_transactions_depth is None
                else wait_triggered_transactions_depth
            ),
            interval=interval,
            retries=retries,
        )
    return TransactionTree(receipt=receipt, children=children)
