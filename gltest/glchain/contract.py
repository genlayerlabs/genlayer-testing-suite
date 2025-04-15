from dataclasses import dataclass
from gltest.artifacts import find_contract_definition
from gltest.assertions import tx_execution_failed
from gltest.exceptions import DeploymentError
from .client import get_gl_client
from genlayer_py.types import CalldataEncodable, GenLayerTransaction
from eth_account.signers.local import LocalAccount
from typing import List, Any, Type, Optional, Dict, Callable
import types


@dataclass
class Contract:
    """
    Class to interact with a contract, its methods
    are implemented dynamically at build time.
    """

    address: str
    account: Optional[LocalAccount] = None

    @classmethod
    def from_address_and_schema(
        cls, address: str, schema: Dict[str, Any]
    ) -> "Contract":
        """
        Build the methods from the schema.
        """
        if not isinstance(schema, dict) or "methods" not in schema:
            raise ValueError("Invalid schema: must contain 'methods' field")

        instance = cls(address=address)
        for method_name, method_info in schema["methods"].items():
            if not isinstance(method_info, dict) or "readonly" not in method_info:
                raise ValueError(
                    f"Invalid method info for {method_name}: must contain 'readonly' field"
                )
            setattr(
                instance,
                method_name,
                types.MethodType(
                    cls.contract_method_factory(method_name, method_info["readonly"]),
                    instance,
                ),
            )
        return instance

    def connect(self, account: LocalAccount) -> "Contract":
        self.account = account
        return self

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
            wait_interval: Optional[int] = None,
            wait_retries: Optional[int] = None,
        ) -> GenLayerTransaction:
            """
            Wrapper to the contract write method.
            """
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
            extra_args = {}
            if wait_interval is not None:
                extra_args["interval"] = wait_interval
            if wait_retries is not None:
                extra_args["retries"] = wait_retries
            receipt = client.wait_for_transaction_receipt(
                transaction_hash=tx_hash, status="FINALIZED", **extra_args
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

    def deploy(
        self,
        args: List[Any] = [],
        account: Optional[LocalAccount] = None,
        consensus_max_rotations: Optional[int] = None,
        leader_only: bool = False,
        wait_interval: Optional[int] = None,
        wait_retries: Optional[int] = None,
    ) -> Contract:
        """
        Deploy the contract
        """
        client = get_gl_client()
        try:
            tx_hash = client.deploy_contract(
                code=self.contract_code,
                args=args,
                account=account,
                consensus_max_rotations=consensus_max_rotations,
                leader_only=leader_only,
            )
            extra_args = {}
            if wait_interval is not None:
                extra_args["interval"] = wait_interval
            if wait_retries is not None:
                extra_args["retries"] = wait_retries
            tx_receipt = client.wait_for_transaction_receipt(
                transaction_hash=tx_hash, status="FINALIZED", **extra_args
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
            return Contract.from_address_and_schema(
                address=contract_address, schema=schema
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
