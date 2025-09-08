from dataclasses import dataclass
from typing import Type, Union, Optional, List, Any
from pathlib import Path
from eth_typing import (
    Address,
    ChecksumAddress,
)
from eth_account.signers.local import LocalAccount
from gltest.artifacts import (
    find_contract_definition_from_name,
    find_contract_definition_from_path,
)
from gltest.clients import (
    get_gl_client,
    get_gl_hosted_studio_client,
    get_local_client,
)
from genlayer_py.types import SimConfig
from .contract import Contract
from gltest.logging import logger
from gltest.types import TransactionStatus, GenLayerTransaction, CalldataEncodable
from gltest.assertions import tx_execution_failed
from gltest.exceptions import DeploymentError
from gltest_cli.config.general import get_general_config
from gltest.utils import extract_contract_address
from gltest.types import TransactionContext


@dataclass
class ContractFactory:
    """
    A factory for deploying contracts.
    """

    contract_name: str
    contract_code: str

    @classmethod
    def from_name(
        cls: Type["ContractFactory"], contract_name: str
    ) -> "ContractFactory":
        """
        Create a ContractFactory instance given the contract name.
        """
        contract_info = find_contract_definition_from_name(contract_name)
        if contract_info is None:
            raise ValueError(
                f"Contract {contract_name} not found in the contracts directory"
            )
        return cls(
            contract_name=contract_name, contract_code=contract_info.contract_code
        )

    @classmethod
    def from_file_path(
        cls: Type["ContractFactory"], contract_file_path: Union[str, Path]
    ) -> "ContractFactory":
        """
        Create a ContractFactory instance given the contract file path.
        """
        contract_info = find_contract_definition_from_path(contract_file_path)
        return cls(
            contract_name=contract_info.contract_name,
            contract_code=contract_info.contract_code,
        )

    def _get_schema_with_fallback(self):
        """Attempts to get the contract schema using multiple clients in a fallback pattern.

        This method tries to get the contract schema in the following order:
        1. Default client
        2. Hosted studio client
        3. Local client

        Returns:
            Optional[Dict[str, Any]]: The contract schema if successful, None if all attempts fail.
        """
        clients = (
            ("default", get_gl_client()),
            ("hosted studio", get_gl_hosted_studio_client()),
            ("local", get_local_client()),
        )
        for label, client in clients:
            try:
                return client.get_contract_schema_for_code(
                    contract_code=self.contract_code
                )
            except Exception as e:
                logger.warning("Schema fetch via %s client failed: %s", label, e)
        return None

    def build_contract(
        self,
        contract_address: Union[Address, ChecksumAddress],
        account: Optional[LocalAccount] = None,
    ) -> Contract:
        """
        Build contract from address
        """
        schema = self._get_schema_with_fallback()
        if schema is None:
            raise ValueError(
                "Failed to get schema from all clients (default, hosted studio, and local)"
            )

        return Contract.new(address=contract_address, schema=schema, account=account)

    def deploy(
        self,
        args: Optional[List[CalldataEncodable]] = None,
        account: Optional[LocalAccount] = None,
        consensus_max_rotations: Optional[int] = None,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
        wait_transaction_status: TransactionStatus = TransactionStatus.ACCEPTED,
        wait_triggered_transactions: bool = False,
        wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
        transaction_context: Optional[TransactionContext] = None,
    ) -> Contract:
        """
        Deploy the contract and return a Contract instance (convenience method).

        This is a convenience method that handles receipt validation
        and contract instantiation automatically.
        """
        receipt = self.deploy_contract_tx(
            args=args,
            account=account,
            consensus_max_rotations=consensus_max_rotations,
            wait_interval=wait_interval,
            wait_retries=wait_retries,
            wait_transaction_status=wait_transaction_status,
            wait_triggered_transactions=wait_triggered_transactions,
            wait_triggered_transactions_status=wait_triggered_transactions_status,
            transaction_context=transaction_context,
        )

        if tx_execution_failed(receipt):
            raise DeploymentError(f"Deployment transaction failed: {receipt}")

        contract_address = extract_contract_address(receipt)
        return self.build_contract(contract_address=contract_address, account=account)

    def deploy_contract_tx(
        self,
        args: Optional[List[CalldataEncodable]] = None,
        account: Optional[LocalAccount] = None,
        consensus_max_rotations: Optional[int] = None,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
        wait_transaction_status: TransactionStatus = TransactionStatus.ACCEPTED,
        wait_triggered_transactions: bool = False,
        wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
        transaction_context: Optional[TransactionContext] = None,
    ) -> GenLayerTransaction:
        """
        Deploy the contract and return the transaction receipt.
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
        leader_only = (
            general_config.get_leader_only()
            if general_config.check_studio_based_rpc()
            else False
        )

        client = get_gl_client()
        try:
            sim_config = None
            if transaction_context:
                try:
                    sim_config = SimConfig(**transaction_context)
                except TypeError as e:
                    raise ValueError(
                        f"Invalid transaction_context keys: {sorted(transaction_context.keys())}"
                    ) from e
            tx_hash = client.deploy_contract(
                code=self.contract_code,
                args=args,
                account=account,
                consensus_max_rotations=consensus_max_rotations,
                leader_only=leader_only,
                sim_config=sim_config,
            )
            tx_receipt = client.wait_for_transaction_receipt(
                transaction_hash=tx_hash,
                status=wait_transaction_status,
                interval=actual_wait_interval,
                retries=actual_wait_retries,
            )
            if wait_triggered_transactions:
                triggered_transactions = tx_receipt.get("triggered_transactions", [])
                for triggered_transaction in triggered_transactions:
                    client.wait_for_transaction_receipt(
                        transaction_hash=triggered_transaction,
                        status=wait_triggered_transactions_status,
                        interval=actual_wait_interval,
                        retries=actual_wait_retries,
                    )
            return tx_receipt
        except Exception as e:
            raise DeploymentError(
                f"Failed to deploy contract {self.contract_name}: {str(e)}"
            ) from e


def get_contract_factory(
    contract_name: Optional[str] = None,
    contract_file_path: Optional[Union[str, Path]] = None,
) -> ContractFactory:
    """
    Get a ContractFactory instance for a contract.

    Args:
        contract_name: Name of the contract to load from artifacts
        contract_file_path: Path to the contract file to load directly

    Note: Exactly one of contract_name or contract_file_path must be provided.
    """
    if contract_name is not None and contract_file_path is not None:
        raise ValueError(
            "Only one of contract_name or contract_file_path should be provided"
        )

    if contract_name is None and contract_file_path is None:
        raise ValueError("Either contract_name or contract_file_path must be provided")

    if contract_name is not None:
        return ContractFactory.from_name(contract_name)
    return ContractFactory.from_file_path(contract_file_path)
