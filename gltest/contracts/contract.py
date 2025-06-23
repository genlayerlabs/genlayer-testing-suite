from eth_account.signers.local import LocalAccount
from dataclasses import dataclass
from gltest.glchain import get_gl_client
from gltest.types import CalldataEncodable, GenLayerTransaction, TransactionStatus
from typing import List, Any, Optional, Dict, Callable
import types
from gltest_cli.config.general import get_general_config


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
        """
        Build the methods from the schema.
        """
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
