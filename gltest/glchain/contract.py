from eth_typing import (
    Address,
    ChecksumAddress,
)
from eth_account.signers.local import LocalAccount
from typing import Union
from dataclasses import dataclass
from gltest.artifacts import find_contract_definition
from gltest.assertions import tx_execution_failed
from gltest.exceptions import DeploymentError
from .client import get_gl_client
from gltest.types import CalldataEncodable, GenLayerTransaction, TransactionStatus
from typing import List, Any, Type, Optional, Dict, Callable
import types
from gltest.plugin_config import get_default_wait_interval, get_default_wait_retries


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
            wait_triggered_transactions_status: TransactionStatus = TransactionStatus.ACCEPTED,
        ) -> GenLayerTransaction:
            """
            Wrapper to the contract write method.
            """
            if wait_interval is None:
                wait_interval = get_default_wait_interval()
            if wait_retries is None:
                wait_retries = get_default_wait_retries()
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
    def from_artifact(
        cls: Type["ContractFactory"], contract_name: str
    ) -> "ContractFactory":
        """
        Create a ContractFactory instance given the contract name.
        """
        contract_info = find_contract_definition(contract_name)
        if contract_info is None:
            raise ValueError(
                f"Contract {contract_name} not found in the contracts directory"
            )
        return cls(
            contract_name=contract_name, contract_code=contract_info.contract_code
        )

    def build_contract(
        self,
        contract_address: Union[Address, ChecksumAddress],
        account: Optional[LocalAccount] = None,
    ) -> Contract:
        """
        Build contract from address
        """
        client = get_gl_client()
        try:
            schema = client.get_contract_schema(address=contract_address)
            return Contract.new(
                address=contract_address, schema=schema, account=account
            )
        except Exception as e:
            raise ValueError(
                f"Failed to build contract {self.contract_name}: {str(e)}"
            ) from e

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
        if wait_interval is None:
            wait_interval = get_default_wait_interval()
        if wait_retries is None:
            wait_retries = get_default_wait_retries()
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
            if (
                not tx_receipt
                or "data" not in tx_receipt
                or "contract_address" not in tx_receipt["data"]
            ):
                raise ValueError(
                    "Invalid transaction receipt: missing contract address"
                )

            if tx_execution_failed(tx_receipt):
                raise ValueError(
                    f"Deployment transaction finalized with error: {tx_receipt}"
                )

            contract_address = tx_receipt["data"]["contract_address"]
            schema = client.get_contract_schema(address=contract_address)
            return Contract.new(
                address=contract_address, schema=schema, account=account
            )
        except Exception as e:
            raise DeploymentError(
                f"Failed to deploy contract {self.contract_name}: {str(e)}"
            ) from e


def get_contract_factory(contract_name: str) -> ContractFactory:
    """
    Get a ContractFactory instance for a contract.
    """
    return ContractFactory.from_artifact(contract_name)
