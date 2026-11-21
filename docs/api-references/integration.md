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
get_contract_factory(contract_name: Optional[str] = None, contract_file_path: Union[str, Path, NoneType] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `contract_name` | positional or keyword | `Optional[str]` | No | `None` |
| `contract_file_path` | positional or keyword | `Union[str, Path, NoneType]` | No | `None` |

**Returns:** `ContractFactory`

---
### `get_default_account`

Returns the default account for the current network.

**Returns:** `LocalAccount`

---
### `get_accounts`

Returns all configured accounts for the current network.

**Returns:** `List[LocalAccount]`

---
### `create_accounts`

Creates n new accounts with random private keys.

```python
create_accounts(n_accounts: int)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `n_accounts` | positional or keyword | `int` | Yes |  |

---
### `get_gl_client`

Get the GenLayer client instance.

---
### `get_validator_factory`



**Returns:** `ValidatorFactory`

---
## ContractFactory

A factory for deploying contracts.

### `factory.build_contract`

Build contract from address

```python
factory.build_contract(contract_address: Union[Address, ChecksumAddress], account: Optional[LocalAccount] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `contract_address` | positional or keyword | `Union[Address, ChecksumAddress]` | Yes |  |
| `account` | positional or keyword | `Optional[LocalAccount]` | No | `None` |

**Returns:** `Contract`

---

### `factory.deploy`

Deploy the contract and return a Contract instance (convenience method).

This is a convenience method that handles receipt validation
and contract instantiation automatically.

```python
factory.deploy(args: Optional[List[Union[NoneType, bool, str, int, bytes, CalldataAddress, Sequence['CalldataEncodable'], Mapping[str, 'CalldataEncodable']]]] = None, account: Optional[LocalAccount] = None, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_transaction_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[TransactionContext] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `args` | positional or keyword | `Optional[List[Union[NoneType, bool, str, int, bytes, CalldataAddress, Sequence['CalldataEncodable'], Mapping[str, 'CalldataEncodable']]]]` | No | `None` |
| `account` | positional or keyword | `Optional[LocalAccount]` | No | `None` |
| `consensus_max_rotations` | positional or keyword | `Optional[int]` | No | `None` |
| `fees` | positional or keyword | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_until` | positional or keyword | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_interval` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_retries` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_transaction_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_triggered_transactions` | positional or keyword | `bool` | No | `False` |
| `wait_triggered_transactions_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | positional or keyword | `Optional[TransactionContext]` | No | `None` |

**Returns:** `Contract`

---

### `factory.deploy_contract_tx`

Deploy the contract and return the transaction receipt.

```python
factory.deploy_contract_tx(args: Optional[List[Union[NoneType, bool, str, int, bytes, CalldataAddress, Sequence['CalldataEncodable'], Mapping[str, 'CalldataEncodable']]]] = None, account: Optional[LocalAccount] = None, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_transaction_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[TransactionContext] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `args` | positional or keyword | `Optional[List[Union[NoneType, bool, str, int, bytes, CalldataAddress, Sequence['CalldataEncodable'], Mapping[str, 'CalldataEncodable']]]]` | No | `None` |
| `account` | positional or keyword | `Optional[LocalAccount]` | No | `None` |
| `consensus_max_rotations` | positional or keyword | `Optional[int]` | No | `None` |
| `fees` | positional or keyword | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_until` | positional or keyword | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_interval` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_retries` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_transaction_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_triggered_transactions` | positional or keyword | `bool` | No | `False` |
| `wait_triggered_transactions_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | positional or keyword | `Optional[TransactionContext]` | No | `None` |

**Returns:** `GenLayerTransaction`

---
## ContractFunction

ContractFunction(method_name: str, read_only: bool, call_method: Optional[Callable] = None, analyze_method: Optional[Callable] = None, transact_method: Optional[Callable] = None)

### `contract.method_name.call`

Read a view method or preview a write on a simulation-capable chain.

```python
contract.method_name.call(transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL, transaction_context: Optional[TransactionContext] = None, *, value: int = 0, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `transaction_hash_variant` | positional or keyword | `TransactionHashVariant` | No | `TransactionHashVariant.LATEST_NONFINAL` |
| `transaction_context` | positional or keyword | `Optional[TransactionContext]` | No | `None` |
| `value` | keyword-only | `int` | No | `0` |
| `fees` | keyword-only | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | keyword-only | `Optional[int]` | No | `None` |

---

### `contract.method_name.transact`

Executes a state-changing contract method through consensus. Returns the transaction receipt.

```python
contract.method_name.transact(value: int = 0, consensus_max_rotations: Optional[int] = None, fees: Optional[Dict[str, Any]] = None, fee_value: Optional[int] = None, wait_until: Optional[Literal['decided', 'finalized']] = None, wait_transaction_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, wait_interval: Optional[int] = None, wait_retries: Optional[int] = None, wait_triggered_transactions: bool = False, wait_triggered_transactions_status: ProtocolTransactionStatus = ProtocolTransactionStatus.ACCEPTED, transaction_context: Optional[TransactionContext] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `value` | positional or keyword | `int` | No | `0` |
| `consensus_max_rotations` | positional or keyword | `Optional[int]` | No | `None` |
| `fees` | positional or keyword | `Optional[Dict[str, Any]]` | No | `None` |
| `fee_value` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_until` | positional or keyword | `Optional[Literal['decided', 'finalized']]` | No | `None` |
| `wait_transaction_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `wait_interval` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_retries` | positional or keyword | `Optional[int]` | No | `None` |
| `wait_triggered_transactions` | positional or keyword | `bool` | No | `False` |
| `wait_triggered_transactions_status` | positional or keyword | `ProtocolTransactionStatus` | No | `ProtocolTransactionStatus.ACCEPTED` |
| `transaction_context` | positional or keyword | `Optional[TransactionContext]` | No | `None` |

---

### `contract.method_name.analyze`

Runs statistical analysis of method behavior across multiple executions.

```python
contract.method_name.analyze(provider: str, model: str, config: Optional[Dict[str, Any]] = None, plugin: Optional[str] = None, plugin_config: Optional[Dict[str, Any]] = None, runs: int = 100, genvm_datetime: Optional[str] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `provider` | positional or keyword | `str` | Yes |  |
| `model` | positional or keyword | `str` | Yes |  |
| `config` | positional or keyword | `Optional[Dict[str, Any]]` | No | `None` |
| `plugin` | positional or keyword | `Optional[str]` | No | `None` |
| `plugin_config` | positional or keyword | `Optional[Dict[str, Any]]` | No | `None` |
| `runs` | positional or keyword | `int` | No | `100` |
| `genvm_datetime` | positional or keyword | `Optional[str]` | No | `None` |

---
## ValidatorFactory



### `validator_factory.create_validator`



```python
validator_factory.create_validator(stake: int, provider: str, model: str, config: Dict[str, Any], plugin: str, plugin_config: Dict[str, Any])
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `stake` | positional or keyword | `int` | Yes |  |
| `provider` | positional or keyword | `str` | Yes |  |
| `model` | positional or keyword | `str` | Yes |  |
| `config` | positional or keyword | `Dict[str, Any]` | Yes |  |
| `plugin` | positional or keyword | `str` | Yes |  |
| `plugin_config` | positional or keyword | `Dict[str, Any]` | Yes |  |

**Returns:** `Validator`

---

### `validator_factory.batch_create_validators`



```python
validator_factory.batch_create_validators(count: int, stake: int, provider: str, model: str, config: Dict[str, Any], plugin: str, plugin_config: Dict[str, Any])
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `count` | positional or keyword | `int` | Yes |  |
| `stake` | positional or keyword | `int` | Yes |  |
| `provider` | positional or keyword | `str` | Yes |  |
| `model` | positional or keyword | `str` | Yes |  |
| `config` | positional or keyword | `Dict[str, Any]` | Yes |  |
| `plugin` | positional or keyword | `str` | Yes |  |
| `plugin_config` | positional or keyword | `Dict[str, Any]` | Yes |  |

**Returns:** `List[Validator]`

---

### `validator_factory.create_mock_validator`



```python
validator_factory.create_mock_validator(mock_llm_response: Optional[MockedLLMResponse] = None, mock_web_response: Optional[MockedWebResponse] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `mock_llm_response` | positional or keyword | `Optional[MockedLLMResponse]` | No | `None` |
| `mock_web_response` | positional or keyword | `Optional[MockedWebResponse]` | No | `None` |

**Returns:** `Validator`

---

### `validator_factory.batch_create_mock_validators`



```python
validator_factory.batch_create_mock_validators(count: int, mock_llm_response: Optional[MockedLLMResponse] = None, mock_web_response: Optional[MockedWebResponse] = None)
```

**Parameters:**

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `count` | positional or keyword | `int` | Yes |  |
| `mock_llm_response` | positional or keyword | `Optional[MockedLLMResponse]` | No | `None` |
| `mock_web_response` | positional or keyword | `Optional[MockedWebResponse]` | No | `None` |

**Returns:** `List[Validator]`

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

| Parameter | Kind | Type | Required | Default |
|-----------|------|------|----------|---------|
| `count` | positional or keyword | `int` | Yes |  |

**Returns:** `List[Validator]`

---

### `validator.clone`



**Returns:** `Validator`

---
