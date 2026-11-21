# Integration Testing

Test contracts against a running GenLayer network (localnet, studionet, or testnet).

## Setup Functions

### `get_contract_factory`

Get a ContractFactory instance for a contract.

Args:
    contract_name: Name of the contract to load from artifacts
    contract_file_path: Path to the contract file to load directly

Note: Exactly one of contract_name or contract_file_path must be provided.

```python
get_contract_factory(contract_name: Optional[str] = None, contract_file_path: Union[str, pathlib._local.Path, NoneType] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `contract_name` | `Optional[str]` | No | `None` |
| `contract_file_path` | `Union[str, pathlib._local.Path, NoneType]` | No | `None` |

**Returns:** `gltest.contracts.contract_factory.ContractFactory`

---
### `get_default_account`

Returns the default account for the current network.

**Returns:** `eth_account.signers.local.LocalAccount`

---
### `get_accounts`

Returns all configured accounts for the current network.

**Returns:** `List[eth_account.signers.local.LocalAccount]`

---
### `create_accounts`

Creates n new accounts with random private keys.

```python
create_accounts(n_accounts: int)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `n_accounts` | `int` | Yes |  |

---
### `get_gl_client`

Get the GenLayer client instance.

---
### `get_validator_factory`



**Returns:** `gltest.validators.validator_factory.ValidatorFactory`

---
## ContractFactory

A factory for deploying contracts.

### `factory.build_contract`

Build contract from address

```python
factory.build_contract(contract_address: Union[eth_typing.evm.Address, eth_typing.evm.ChecksumAddress], account: Optional[eth_account.signers.local.LocalAccount] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `contract_address` | `Union[eth_typing.evm.Address, eth_typing.evm.ChecksumAddress]` | Yes |  |
| `account` | `Optional[eth_account.signers.local.LocalAccount]` | No | `None` |

**Returns:** `gltest.contracts.contract.Contract`

---

### `factory.deploy`

Deploy the contract and return a Contract instance (convenience method).

This is a convenience method that handles receipt validation
and contract instantiation automatically.

```python
factory.deploy(args: Optional[List[Union[NoneType, bool, str, int, bytes, genlayer_py.types.calldata.CalldataAddress, collections.abc.Sequence['CalldataEncodable'], collections.abc.Mapping[str, 'CalldataEncodable']]]] = None, account: Optional[eth_account.signers.local.LocalAccount] = None, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_transaction_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[gltest.types.TransactionContext] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `args` | `Optional[List[Union[NoneType, bool, str, int, bytes, genlayer_py.types.calldata.CalldataAddress, collections.abc.Sequence['CalldataEncodable'], collections.abc.Mapping[str, 'CalldataEncodable']]]]` | No | `None` |
| `account` | `Optional[eth_account.signers.local.LocalAccount]` | No | `None` |
| `consensus_max_rotations` | `Optional[int]` | No | `None` |
| `fees` | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | `Optional[int]` | No | `None` |
| `wait_until` | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_interval` | `Optional[int]` | No | `None` |
| `wait_retries` | `Optional[int]` | No | `None` |
| `wait_transaction_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_triggered_transactions` | `bool` | No | `False` |
| `wait_triggered_transactions_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | `Optional[gltest.types.TransactionContext]` | No | `None` |

**Returns:** `gltest.contracts.contract.Contract`

---

### `factory.deploy_contract_tx`

Deploy the contract and return the transaction receipt.

```python
factory.deploy_contract_tx(args: Optional[List[Union[NoneType, bool, str, int, bytes, genlayer_py.types.calldata.CalldataAddress, collections.abc.Sequence['CalldataEncodable'], collections.abc.Mapping[str, 'CalldataEncodable']]]] = None, account: Optional[eth_account.signers.local.LocalAccount] = None, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_transaction_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[gltest.types.TransactionContext] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `args` | `Optional[List[Union[NoneType, bool, str, int, bytes, genlayer_py.types.calldata.CalldataAddress, collections.abc.Sequence['CalldataEncodable'], collections.abc.Mapping[str, 'CalldataEncodable']]]]` | No | `None` |
| `account` | `Optional[eth_account.signers.local.LocalAccount]` | No | `None` |
| `consensus_max_rotations` | `Optional[int]` | No | `None` |
| `fees` | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | `Optional[int]` | No | `None` |
| `wait_until` | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_interval` | `Optional[int]` | No | `None` |
| `wait_retries` | `Optional[int]` | No | `None` |
| `wait_transaction_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_triggered_transactions` | `bool` | No | `False` |
| `wait_triggered_transactions_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | `Optional[gltest.types.TransactionContext]` | No | `None` |

**Returns:** `genlayer_py.types.transactions.GenLayerTransaction`

---
## ContractFunction

ContractFunction(method_name: str, read_only: bool, call_method: Optional[Callable] = None, analyze_method: Optional[Callable] = None, transact_method: Optional[Callable] = None)

### `contract.method_name.call`

Read a view method or preview a write on a simulation-capable chain.

```python
contract.method_name.call(transaction_hash_variant: genlayer_py.types.transactions.TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL, transaction_context: Optional[gltest.types.TransactionContext] = None, value: int = 0, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `transaction_hash_variant` | `genlayer_py.types.transactions.TransactionHashVariant` | No | `TransactionHashVariant.LATEST_NONFINAL` |
| `transaction_context` | `Optional[gltest.types.TransactionContext]` | No | `None` |
| `value` | `int` | No | `0` |
| `fees` | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | `Optional[int]` | No | `None` |

---

### `contract.method_name.transact`

Executes a state-changing contract method through consensus. Returns the transaction receipt.

```python
contract.method_name.transact(value: int = 0, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_transaction_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: genlayer_py.types.transactions.ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[gltest.types.TransactionContext] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `value` | `int` | No | `0` |
| `consensus_max_rotations` | `Optional[int]` | No | `None` |
| `fees` | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | `Optional[int]` | No | `None` |
| `wait_until` | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_transaction_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_interval` | `Optional[int]` | No | `None` |
| `wait_retries` | `Optional[int]` | No | `None` |
| `wait_triggered_transactions` | `bool` | No | `False` |
| `wait_triggered_transactions_status` | `genlayer_py.types.transactions.ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | `Optional[gltest.types.TransactionContext]` | No | `None` |

---

### `contract.method_name.analyze`

Runs statistical analysis of method behavior across multiple executions.

```python
contract.method_name.analyze(provider: str, model: str, config: Optional[Dict[str, Any]] = None, plugin: Optional[str] = None, plugin_config: Optional[Dict[str, Any]] = None, runs: int = 100, genvm_datetime: Optional[str] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `provider` | `str` | Yes |  |
| `model` | `str` | Yes |  |
| `config` | `Optional[Dict[str, Any]]` | No | `None` |
| `plugin` | `Optional[str]` | No | `None` |
| `plugin_config` | `Optional[Dict[str, Any]]` | No | `None` |
| `runs` | `int` | No | `100` |
| `genvm_datetime` | `Optional[str]` | No | `None` |

---
## ValidatorFactory



### `validator_factory.create_validator`



```python
validator_factory.create_validator(stake: int, provider: str, model: str, config: Dict[str, Any], plugin: str, plugin_config: Dict[str, Any])
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `stake` | `int` | Yes |  |
| `provider` | `str` | Yes |  |
| `model` | `str` | Yes |  |
| `config` | `Dict[str, Any]` | Yes |  |
| `plugin` | `str` | Yes |  |
| `plugin_config` | `Dict[str, Any]` | Yes |  |

**Returns:** `gltest.validators.validator_factory.Validator`

---

### `validator_factory.batch_create_validators`



```python
validator_factory.batch_create_validators(count: int, stake: int, provider: str, model: str, config: Dict[str, Any], plugin: str, plugin_config: Dict[str, Any])
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `count` | `int` | Yes |  |
| `stake` | `int` | Yes |  |
| `provider` | `str` | Yes |  |
| `model` | `str` | Yes |  |
| `config` | `Dict[str, Any]` | Yes |  |
| `plugin` | `str` | Yes |  |
| `plugin_config` | `Dict[str, Any]` | Yes |  |

**Returns:** `List[gltest.validators.validator_factory.Validator]`

---

### `validator_factory.create_mock_validator`



```python
validator_factory.create_mock_validator(mock_llm_response: Optional[gltest.types.MockedLLMResponse] = None, mock_web_response: Optional[gltest.types.MockedWebResponse] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `mock_llm_response` | `Optional[gltest.types.MockedLLMResponse]` | No | `None` |
| `mock_web_response` | `Optional[gltest.types.MockedWebResponse]` | No | `None` |

**Returns:** `gltest.validators.validator_factory.Validator`

---

### `validator_factory.batch_create_mock_validators`



```python
validator_factory.batch_create_mock_validators(count: int, mock_llm_response: Optional[gltest.types.MockedLLMResponse] = None, mock_web_response: Optional[gltest.types.MockedWebResponse] = None)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `count` | `int` | Yes |  |
| `mock_llm_response` | `Optional[gltest.types.MockedLLMResponse]` | No | `None` |
| `mock_web_response` | `Optional[gltest.types.MockedWebResponse]` | No | `None` |

**Returns:** `List[gltest.validators.validator_factory.Validator]`

---
## Validator

Validator(stake: int, provider: str, model: str, config: Dict[str, Any], plugin: str, plugin_config: Dict[str, Any], mock_enabled: bool, mock_llm_response: Optional[gltest.types.MockedLLMResponse], mock_web_response: Optional[gltest.types.MockedWebResponse])

### `validator.to_dict`



**Returns:** `Dict[str, Any]`

---

### `validator.batch_clone`



```python
validator.batch_clone(count: int)
```

**Parameters:**

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `count` | `int` | Yes |  |

**Returns:** `List[Validator]`

---

### `validator.clone`



**Returns:** `'Validator'`

---
