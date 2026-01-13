from typing import List, Optional
from genlayer_py.types import GenLayerTransaction
from gltest.types import TransactionStatus, TransactionTree
from gltest.clients import get_gl_client
from gltest_cli.config.general import get_general_config


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
    wait_transaction_status: TransactionStatus = TransactionStatus.ACCEPTED,
    wait_interval: Optional[int] = None,
    wait_retries: Optional[int] = None,
    wait_triggered_transactions: bool = False,
    wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
    wait_triggered_transactions_depth: int = 3,
) -> TransactionTree:
    """Wait for a transaction and optionally its triggered transactions.

    Args:
        tx_hash: The transaction hash to wait for.
        wait_transaction_status: The status to wait for on the main transaction.
        wait_interval: Polling interval in seconds. Uses default if not specified.
        wait_retries: Number of retries. Uses default if not specified.
        wait_triggered_transactions: Whether to wait for triggered transactions.
        wait_triggered_transactions_status: The status to wait for on triggered transactions.
        wait_triggered_transactions_depth: Maximum depth to follow triggered transactions.

    Returns:
        A TransactionTree with the root transaction and nested children for
        triggered transactions. Use .flatten() to get a flat list of receipts,
        or .children to access direct children, or .get_children_receipts() for all descendants.
    """
    general_config = get_general_config()
    actual_wait_interval = (
        wait_interval
        if wait_interval is not None
        else general_config.get_default_wait_interval()
    )
    actual_wait_retries = (
        wait_retries
        if wait_retries is not None
        else general_config.get_default_wait_retries()
    )

    client = get_gl_client()
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx_hash,
        status=wait_transaction_status,
        interval=actual_wait_interval,
        retries=actual_wait_retries,
    )

    root = TransactionTree(receipt=receipt)

    if wait_triggered_transactions and wait_triggered_transactions_depth > 0:
        pending_nodes = [root]
        for _ in range(wait_triggered_transactions_depth):
            next_nodes = []
            for current_node in pending_nodes:
                triggered_transactions = current_node.receipt.get(
                    "triggered_transactions", []
                )
                for triggered_transaction in triggered_transactions:
                    triggered_receipt = client.wait_for_transaction_receipt(
                        transaction_hash=triggered_transaction,
                        status=wait_triggered_transactions_status,
                        interval=actual_wait_interval,
                        retries=actual_wait_retries,
                    )
                    child_node = TransactionTree(receipt=triggered_receipt)
                    current_node.children.append(child_node)
                    next_nodes.append(child_node)
            if not next_nodes:
                break
            pending_nodes = next_nodes

    return root
