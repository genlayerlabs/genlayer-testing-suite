from genlayer_py.types import GenLayerTransaction


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
