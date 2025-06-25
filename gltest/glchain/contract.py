from eth_typing import (
    Address,
    ChecksumAddress,
)
from eth_account.signers.local import LocalAccount
from typing import Union
from pathlib import Path
from dataclasses import dataclass
from gltest.artifacts import (
    find_contract_definition_from_name,
    find_contract_definition_from_path,
)
from gltest.assertions import tx_execution_failed
from gltest.exceptions import DeploymentError
from .client import get_gl_client, get_gl_hosted_studio_client, get_local_client
from gltest.types import CalldataEncodable, GenLayerTransaction, TransactionStatus
from typing import List, Any, Type, Optional, Dict, Callable
import types
from gltest_cli.config.general import get_general_config
from gltest_cli.logging import logger


@dataclass
class Contract:
    """
    Class to interact with a contract, its methods
    are implemented dynamically at build time.
    """

    address: str
    account: Optional[LocalAccount] = None
    _schema: Optional[Dict[str, Any]] = None

    @classmethod
    def new(
        cls,
        address: str,
        schema: Dict[str, Any],
        account: Optional[LocalAccount] = None,
    ) -> "Contract":
        """
        Build the methods from the schema.
        """
        if not isinstance(schema, dict) or "methods" not in schema:
            raise ValueError("Invalid schema: must contain 'methods' field")
        instance = cls(address=address, _schema=schema, account=account)
        instance._build_methods_from_schema()
        return instance

    def _build_methods_from_schema(self):
        if self._schema is None:
            raise ValueError("No schema provided")
        for method_name, method_info in self._schema["methods"].items():
            if not isinstance(method_info, dict) or "readonly" not in method_info:
                raise ValueError(
                    f"Invalid method info for '{method_name}': must contain 'readonly' field"
                )
            method_func = self.contract_method_factory(
                method_name, method_info["readonly"]
            )
            bound_method = types.MethodType(method_func, self)
            setattr(self, method_name, bound_method)

    def connect(self, account: LocalAccount) -> "Contract":
        """
        Create a new instance of the contract with the same methods and a different account.
        """
        new_contract = self.__class__(
            address=self.address, account=account, _schema=self._schema
        )
        new_contract._build_methods_from_schema()
        return new_contract

    @staticmethod
    def contract_method_factory(method_name: str, read_only: bool) -> Callable:
        """
        Create a function that interacts with a specific contract method.
        """

        def read_contract_wrapper(
            self,
            args: Optional[List[CalldataEncodable]] = None,
        ) -> Any:
            """
            Wrapper to the contract read method.
            """
            client = get_gl_client()
            return client.read_contract(
                address=self.address,
                function_name=method_name,
                account=self.account,
                args=args,
            )

        def write_contract_wrapper(
            self,
            args: Optional[List[CalldataEncodable]] = None,
            value: int = 0,
            consensus_max_rotations: Optional[int] = None,
            leader_only: bool = False,
            wait_transaction_status: TransactionStatus = TransactionStatus.FINALIZED,
            wait_interval: Optional[int] = None,
            wait_retries: Optional[int] = None,
            wait_triggered_transactions: bool = True,
            wait_triggered_transactions_status: TransactionStatus = TransactionStatus.FINALIZED,
        ) -> GenLayerTransaction:
            """
            Wrapper to the contract write method.
            """
            general_config = get_general_config()
            if wait_interval is None:
                wait_interval = general_config.get_default_wait_interval()
            if wait_retries is None:
                wait_retries = general_config.get_default_wait_retries()
            client = get_gl_client()
            tx_hash = client.write_contract(
                address=self.address,
                function_name=method_name,
                account=self.account,
                value=value,
                consensus_max_rotations=consensus_max_rotations,
                leader_only=leader_only,
                args=args,
            )
            receipt = client.wait_for_transaction_receipt(
                transaction_hash=tx_hash,
                status=wait_transaction_status,
                interval=wait_interval,
                retries=wait_retries,
            )
            if wait_triggered_transactions:
                triggered_transactions = receipt["triggered_transactions"]
                for triggered_transaction in triggered_transactions:
                    client.wait_for_transaction_receipt(
                        transaction_hash=triggered_transaction,
                        status=wait_triggered_transactions_status,
                        interval=wait_interval,
                        retries=wait_retries,
                    )
            return receipt

        return read_contract_wrapper if read_only else write_contract_wrapper


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
        1. Hosted studio client
        2. Local client
        3. Regular client

        Returns:
            Optional[Dict[str, Any]]: The contract schema if successful, None if all attempts fail.
        """
        clients = (
            ("hosted studio", get_gl_hosted_studio_client()),
            ("local", get_local_client()),
            ("default", get_gl_client()),
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
                "Failed to get schema from all clients (hosted studio, local, and regular)"
            )

        return Contract.new(address=contract_address, schema=schema, account=account)

    def deploy(
        self,
        args: List[Any] = [],
        account: Optional[LocalAccount] = None,
        consensus_max_rotations: Optional[int] = None,
        leader_only: bool = False,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
        wait_transaction_status: TransactionStatus = TransactionStatus.FINALIZED,
    ) -> Contract:
        """
        Deploy the contract
        """
        general_config = get_general_config()
        if wait_interval is None:
            wait_interval = general_config.get_default_wait_interval()
        if wait_retries is None:
            wait_retries = general_config.get_default_wait_retries()

        client = get_gl_client()
        try:
            tx_hash = client.deploy_contract(
                code=self.contract_code,
                args=args,
                account=account,
                consensus_max_rotations=consensus_max_rotations,
                leader_only=leader_only,
            )
            tx_receipt = client.wait_for_transaction_receipt(
                transaction_hash=tx_hash,
                status=wait_transaction_status,
                interval=wait_interval,
                retries=wait_retries,
            )
            if tx_execution_failed(tx_receipt):
                raise ValueError(
                    f"Deployment transaction finalized with error: {tx_receipt}"
                )

            if (
                "tx_data_decoded" in tx_receipt
                and "contract_address" in tx_receipt["tx_data_decoded"]
            ):
                contract_address = tx_receipt["tx_data_decoded"]["contract_address"]
            elif "data" in tx_receipt and "contract_address" in tx_receipt["data"]:
                contract_address = tx_receipt["data"]["contract_address"]
            else:
                raise ValueError("Transaction receipt missing contract address")

            schema = self._get_schema_with_fallback()
            if schema is None:
                raise ValueError(
                    "Failed to get schema from all clients (hosted studio, local, and regular)"
                )

            return Contract.new(
                address=contract_address, schema=schema, account=account
            )
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
