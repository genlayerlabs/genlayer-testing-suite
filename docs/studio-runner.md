# Studio Mode

Deploy and test intelligent contracts against a running GenLayer Studio instance via RPC. This gives you full network behavior including multi-validator consensus, real transaction receipts, and testnet deployment.

## Overview

Studio mode deploys contracts to GenLayer Studio (or a remote network) and interacts through JSON-RPC. Every write operation goes through the full consensus pipeline.

- **Fidelity**: Real consensus, real validators, real transaction lifecycle
- **Networks**: localnet (Docker), studionet, testnet_asimov, or custom
- **Mocking**: Mock validators with predefined LLM/web responses for deterministic tests

### When to Use Studio Mode

| Studio Mode | Direct Mode |
|-------------|-------------|
| Integration tests | Unit tests |
| Consensus validation | Rapid iteration |
| Multi-validator scenarios | CI/CD pipelines |
| Testnet deployment | Logic validation |

Use Studio mode when you need full network behavior. For fast unit tests, use [Direct mode](direct-runner.md).

## Prerequisites

- Python >= 3.12
- GenLayer Studio running locally (Docker) — or access to studionet/testnet
- pip

## Installation

```bash
pip install genlayer-test
```

## Quick Start

```python
from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

factory = get_contract_factory("Storage")
contract = factory.deploy(args=["initial_value"])

# Read
result = contract.get_storage().call()
assert result == "initial_value"

# Write
tx_receipt = contract.update_storage(args=["new_value"]).transact()
assert tx_execution_succeeded(tx_receipt)

# Verify
assert contract.get_storage().call() == "new_value"
```

Run with the `gltest` CLI:

```bash
gltest tests/test_storage.py -v
```

## Configuration

Create a `gltest.config.yaml` in your project root. While optional, it helps manage network configs, contract paths, and environment settings.

### Full Configuration Reference

```yaml
networks:
  default: localnet  # Which network to use by default

  localnet:
    url: "http://127.0.0.1:4000/api"
    leader_only: false

  studionet:
    # Pre-configured — accounts auto-generated
    # Override any settings if needed

  testnet_asimov:
    accounts:
      - "${ACCOUNT_PRIVATE_KEY_1}"
      - "${ACCOUNT_PRIVATE_KEY_2}"
      - "${ACCOUNT_PRIVATE_KEY_3}"
    from: "${ACCOUNT_PRIVATE_KEY_2}"  # Use as default instead of first account

  custom_network:
    id: 1234
    url: "http://custom.network:8545"
    chain_type: "localnet"  # Required for custom networks
    accounts:
      - "${CUSTOM_ACCOUNT_1}"
      - "${CUSTOM_ACCOUNT_2}"
    from: "${CUSTOM_ACCOUNT_1}"

paths:
  contracts: "contracts"  # Contract files directory
  artifacts: "artifacts"  # Analysis results directory

environment: .env  # File containing private keys and secrets
```

### Networks

**Pre-configured networks** work out of the box:

| Network | Accounts | Notes |
|---------|----------|-------|
| `localnet` | Auto-generated | Local Docker deployment |
| `studionet` | Auto-generated | GenLayer Studio cloud |
| `testnet_asimov` | Must be configured | Public testnet |

**Network configuration fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `url` | For custom networks | RPC endpoint |
| `id` | For custom networks | Chain ID |
| `chain_type` | For custom networks | One of: `localnet`, `studionet`, `testnet_asimov` |
| `accounts` | For testnet/custom | List of private keys (use env vars) |
| `from` | No | Which account to use as default (defaults to first) |
| `leader_only` | No | Skip consensus for all operations |

### Default Account Selection

The `from` field controls which account is used as the default for deployments and transactions:

```yaml
testnet_asimov:
  accounts:
    - "${DEPLOYER_KEY}"    # accounts[0]
    - "${USER_KEY}"        # accounts[1]
    - "${ADMIN_KEY}"       # accounts[2]
  from: "${ADMIN_KEY}"     # ADMIN_KEY becomes the default, not DEPLOYER_KEY
```

If `from` is not specified, the first account in the list is used.

### Chain vs Network

- **Network**: Connection details (URL, accounts, etc.) for a specific environment
- **Chain**: The GenLayer chain type and its associated behaviors

Pre-configured networks have the correct chain type set automatically. Custom networks must specify `chain_type` explicitly. The `--chain-type` CLI flag can override the chain type for any network.

### Environment Variables

Use `${VAR_NAME}` syntax in config files. Variables are resolved from the file specified in `environment:` (default: `.env`). Missing variables produce a clear error message.

## CLI Reference

### Running Tests

```bash
gltest                                  # Run all tests
gltest tests/test_mycontract.py         # Specific file
gltest -m "integration"                 # By pytest marker
gltest -v                               # Verbose output
```

### Network and Connection

```bash
gltest --network localnet               # Specific network (from config)
gltest --network studionet
gltest --network testnet_asimov
gltest --rpc-url http://custom:4000/api # Custom RPC URL
gltest --chain-type localnet            # Override chain type
```

### Contract Paths

```bash
gltest --contracts-dir custom/contracts/path
```

### Transaction Tuning

```bash
gltest --default-wait-interval 2000     # ms between receipt checks
gltest --default-wait-retries 20        # Max retries for receipts
```

### Leader-Only Mode

```bash
gltest --leader-only
```

Configures all deployments and write operations to run only on the leader node. Useful for:
- Faster test execution by skipping consensus
- Development and debugging
- Reducing computational overhead

**Note:** Leader-only mode only works on studio-based networks (localhost, 127.0.0.1, *.genlayer.com, *.genlayerlabs.com). On other networks it has no effect and a warning is logged.

### Chain Type Override

```bash
gltest --chain-type localnet
gltest --chain-type studionet
gltest --chain-type testnet_asimov
```

Overrides the chain type configured for the network. The chain type determines RPC endpoints, consensus mechanisms, and available features.

## Contract Deployment

Two methods for deploying contracts:

### `deploy()` — Returns Contract Instance (Recommended)

```python
from gltest import get_contract_factory, get_default_account

factory = get_contract_factory("Storage")

contract = factory.deploy(
    args=["initial_value"],           # Constructor arguments
    account=get_default_account(),    # Account to deploy from
    consensus_max_rotations=3,        # Max consensus rotations
    transaction_context=None,         # Custom validators/datetime
)

assert contract.address is not None
```

### `deploy_contract_tx()` — Returns Receipt Only

```python
from gltest.assertions import tx_execution_succeeded
from gltest.utils import extract_contract_address

receipt = factory.deploy_contract_tx(
    args=["initial_value"],
    account=get_default_account(),
)

assert tx_execution_succeeded(receipt)
contract_address = extract_contract_address(receipt)
```

## Read Methods

Read methods return values directly via `.call()`:

```python
result = contract.get_storage(args=[]).call(
    transaction_context=None,  # Optional: custom validators/datetime
)
assert result == "initial_value"
```

## Write Methods

Write methods return transaction receipts via `.transact()`:

```python
from gltest.assertions import tx_execution_succeeded

tx_receipt = contract.update_storage(args=["new_value"]).transact(
    value=0,                       # Native currency to send
    consensus_max_rotations=3,     # Max consensus rotations
    wait_interval=1000,            # ms between status checks
    wait_retries=10,               # Max retry attempts
    transaction_context=None,      # Custom validators/datetime
)

assert tx_execution_succeeded(tx_receipt)
```

## Assertions

### Basic Transaction Assertions

```python
from gltest.assertions import tx_execution_succeeded, tx_execution_failed

assert tx_execution_succeeded(tx_receipt)
assert tx_execution_failed(tx_receipt)
```

### Output Matching

Match patterns in the transaction's stdout and stderr using regex (similar to pytest's `match` parameter):

```python
# Simple string matching
assert tx_execution_succeeded(tx_receipt, match_std_out="Process completed")
assert tx_execution_failed(tx_receipt, match_std_err="Warning: deprecated")

# Regex patterns
assert tx_execution_succeeded(tx_receipt, match_std_out=r".*code \d+")
assert tx_execution_failed(tx_receipt, match_std_err=r"Method.*failed")
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `result` | Transaction result from contract method calls |
| `match_std_out` | String or regex to match in stdout (optional) |
| `match_std_err` | String or regex to match in stderr (optional) |

**Note:** `match_std_out` and `match_std_err` are only available on **localnet** and **studionet**. Not supported on testnet.

## Fixtures

### `gl_client` (session scope)

GenLayer client instance for direct network operations:

```python
def test_client_operations(gl_client):
    tx_hash = "0x1234..."
    transaction = gl_client.get_transaction(tx_hash)
```

### `default_account` (session scope)

The default account for transactions when none is specified:

```python
def test_with_default_account(default_account):
    factory = get_contract_factory("MyContract")
    contract = factory.deploy(account=default_account)
```

### `accounts` (session scope)

List of accounts loaded from config private keys, or pre-created test accounts:

```python
def test_multiple_accounts(accounts):
    sender = accounts[0]
    receiver = accounts[1]

    contract.transfer(args=[receiver.address, 100], account=sender)
```

### Using Fixtures Together

```python
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

def test_complete_workflow(gl_client, default_account, accounts):
    factory = get_contract_factory("MyContract")
    contract = factory.deploy(account=default_account)

    other_account = accounts[1]
    tx_receipt = contract.some_method(args=["value"], account=other_account)

    assert tx_execution_succeeded(tx_receipt)
```

## Mock LLM Responses

Simulate LLM responses for deterministic tests by providing predefined responses instead of relying on actual LLM calls.

### Structure

```python
from gltest.types import MockedLLMResponse

mock_response: MockedLLMResponse = {
    "nondet_exec_prompt": {},                          # gl.nondet.exec_prompt
    "eq_principle_prompt_comparative": {},              # gl.eq_principle.prompt_comparative
    "eq_principle_prompt_non_comparative": {}           # gl.eq_principle.prompt_non_comparative
}
```

### Method Mappings

| Mock Key | GenLayer Method |
|----------|----------------|
| `"nondet_exec_prompt"` | `gl.nondet.exec_prompt` |
| `"eq_principle_prompt_comparative"` | `gl.eq_principle.prompt_comparative` |
| `"eq_principle_prompt_non_comparative"` | `gl.eq_principle.prompt_non_comparative` |

### How String Matching Works

When a GenLayer method is called:

1. A user message is constructed internally from the method's arguments
2. The mock system searches for **substrings** within that message
3. If a matching string is found in the mock dictionary, the associated response is returned

The key in your mock dictionary must be **contained within** the actual user message. This is substring matching, not exact matching.

```python
mock_response: MockedLLMResponse = {
    "nondet_exec_prompt": {
        # Key "analyze this" will match any user message containing "analyze this"
        "analyze this": "positive sentiment",
        "summarize": "brief summary here"
    },
    "eq_principle_prompt_comparative": {
        "values match": True,
        "prices are equal": True
    }
}
```

### Using Mock Validators

```python
from gltest import get_contract_factory, get_validator_factory
from gltest.types import MockedLLMResponse

mock_response: MockedLLMResponse = {
    "nondet_exec_prompt": {
        "analyze this": "positive sentiment"
    },
    "eq_principle_prompt_comparative": {
        "values match": True
    }
}

validator_factory = get_validator_factory()
mock_validators = validator_factory.batch_create_mock_validators(
    count=5,
    mock_llm_response=mock_response
)

transaction_context = {
    "validators": [v.to_dict() for v in mock_validators],
    "genvm_datetime": "2024-01-01T00:00:00Z"  # Fixed datetime for reproducibility
}

factory = get_contract_factory("LLMContract")
contract = factory.deploy(transaction_context=transaction_context)

result = contract.analyze_text(args=["analyze this"]).transact(
    transaction_context=transaction_context
)
# Result will consistently return "positive sentiment"
```

## Mock Web Responses

Simulate HTTP responses for contracts that call `gl.nondet.web.get()`, `gl.nondet.web.post()`, and other web methods.

### Basic Example

```python
from gltest import get_contract_factory, get_validator_factory
from gltest.types import MockedWebResponse
import json

mock_web_response: MockedWebResponse = {
    "nondet_web_request": {
        "https://api.example.com/price": {
            "method": "GET",
            "status": 200,
            "body": json.dumps({"price": 100.50})
        }
    }
}

validator_factory = get_validator_factory()
validators = validator_factory.batch_create_mock_validators(
    count=5,
    mock_web_response=mock_web_response
)

transaction_context = {"validators": [v.to_dict() for v in validators]}

factory = get_contract_factory("PriceOracle")
contract = factory.deploy(transaction_context=transaction_context)
result = contract.update_price().transact(transaction_context=transaction_context)
```

### All HTTP Methods

```python
mock_web_response: MockedWebResponse = {
    "nondet_web_request": {
        "https://api.example.com/users/123": {
            "method": "GET",
            "status": 200,
            "body": '{"id": 123, "name": "Alice"}'
        },
        "https://api.example.com/users": {
            "method": "POST",
            "status": 201,
            "body": '{"id": 124, "name": "Bob", "created": true}'
        },
        "https://api.example.com/users/123": {
            "method": "PUT",
            "status": 200,
            "body": '{"id": 123, "name": "Alice Updated"}'
        },
        "https://api.example.com/users/123": {
            "method": "DELETE",
            "status": 204,
            "body": ""
        },
        "https://api.example.com/error": {
            "method": "GET",
            "status": 500,
            "body": "Internal Server Error"
        }
    }
}
```

All standard HTTP methods are supported: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS.

### How It Works

When a contract calls any web method:
1. The mock system checks if the URL exists in the mock configuration
2. If found, returns the mocked response with the specified status and body
3. If not found, the actual web request is made (or fails if network access is disabled)

### Real-World Example: Twitter/X API

```python
from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedWebResponse
import json
import urllib.parse

def test_x_username_storage():
    def get_username_url(username: str) -> str:
        params = {"user.fields": "public_metrics,verified"}
        return f"https://domain.com/api/twitter/users/by/username/{username}?{urllib.parse.urlencode(params)}"

    mock_web_response: MockedWebResponse = {
        "nondet_web_request": {
            get_username_url("user_a"): {
                "method": "GET",
                "status": 200,
                "body": json.dumps({"username": "user_a", "verified": True})
            },
            get_username_url("user_b"): {
                "method": "GET",
                "status": 200,
                "body": json.dumps({"username": "user_b", "verified": False})
            }
        }
    }

    validator_factory = get_validator_factory()
    validators = validator_factory.batch_create_mock_validators(
        count=5,
        mock_web_response=mock_web_response
    )
    transaction_context = {"validators": [v.to_dict() for v in validators]}

    factory = get_contract_factory("XUsernameStorage")
    contract = factory.deploy(transaction_context=transaction_context)

    tx_receipt = contract.update_username(args=["user_a"]).transact(
        transaction_context=transaction_context
    )
    assert tx_execution_succeeded(tx_receipt)

    username = contract.get_username().call(transaction_context=transaction_context)
    assert username == "user_a"
```

### Combining LLM and Web Mocks

Pass both to `batch_create_mock_validators`:

```python
validators = validator_factory.batch_create_mock_validators(
    count=5,
    mock_llm_response=mock_llm_response,
    mock_web_response=mock_web_response
)
```

### Best Practices

- **URL matching is exact** — the full URL including query parameters must match
- **Response body**: Always provide as a string (use `json.dumps()` for JSON)
- **Status codes**: Use realistic HTTP status codes (200, 404, 500, etc.)
- **Method matching**: Specify the HTTP method your contract actually uses
- **Error testing**: Mock error responses to test error handling paths
- Mock web responses are only available when using mock validators

## Custom Validators

Create validators with specific LLM providers and configurations.

### Creating Individual Validators

```python
from gltest import get_validator_factory

factory = get_validator_factory()

openai_validator = factory.create_validator(
    stake=10,
    provider="openai",
    model="gpt-4o",
    config={"temperature": 0.8, "max_tokens": 2000},
    plugin="openai-compatible",
    plugin_config={"api_key_env_var": "OPENAI_API_KEY"}
)

ollama_validator = factory.create_validator(
    stake=8,
    provider="ollama",
    model="mistral",
    config={"temperature": 0.5},
    plugin="ollama",
    plugin_config={"api_url": "http://localhost:11434"}
)
```

### Batch Creation

```python
validators = factory.batch_create_validators(
    count=5,
    stake=10,
    provider="openai",
    model="gpt-4o",
    config={"temperature": 0.7, "max_tokens": 1000},
    plugin="openai-compatible",
    plugin_config={"api_key_env_var": "OPENAI_API_KEY"}
)
```

### Mock Validators

```python
mock_response = {
    "nondet_exec_prompt": {
        "What is 2+2?": "4",
        "Explain quantum physics": "It's complicated"
    },
    "eq_principle_prompt_comparative": {
        "values must match": True
    },
    "eq_principle_prompt_non_comparative": {
        "Is this valid?": True
    }
}

# Single mock validator
mock_validator = factory.create_mock_validator(mock_response)

# Multiple mock validators
mock_validators = factory.batch_create_mock_validators(
    count=5,
    mock_llm_response=mock_response
)
```

### Validator Methods

Each validator object provides:

| Method | Description |
|--------|-------------|
| `to_dict()` | Convert to dictionary for API calls |
| `clone()` | Create an identical copy |
| `batch_clone(count)` | Create multiple identical copies |

```python
base_validator = factory.create_validator(
    stake=10,
    provider="openai",
    model="gpt-4o",
    config={"temperature": 0.7},
    plugin="openai-compatible",
    plugin_config={"api_key_env_var": "OPENAI_API_KEY"}
)

cloned = base_validator.clone()
multiple = base_validator.batch_clone(3)
as_dict = base_validator.to_dict()
```

## Custom Transaction Context

Combine custom validators and GenVM datetime for full control over the execution environment:

```python
from gltest import get_contract_factory, get_validator_factory

factory = get_contract_factory("MyContract")
validator_factory = get_validator_factory()

validators = validator_factory.batch_create_validators(
    count=3,
    stake=10,
    provider="openai",
    model="gpt-4o",
    config={"temperature": 0.7, "max_tokens": 1000},
    plugin="openai-compatible",
    plugin_config={"api_key_env_var": "OPENAI_API_KEY"}
)

transaction_context = {
    "validators": [v.to_dict() for v in validators],
    "genvm_datetime": "2024-03-15T14:30:00Z"  # ISO format
}

# Use in deploy, call, and transact
contract = factory.deploy(args=["initial_value"], transaction_context=transaction_context)
result = contract.read_method().call(transaction_context=transaction_context)
tx_receipt = contract.write_method(args=["value"]).transact(transaction_context=transaction_context)
```

## Statistical Analysis

The `.analyze()` method runs multiple simulations of a write operation to measure consistency. Useful for testing LLM-based contracts where outputs may vary.

```python
from gltest import get_contract_factory

factory = get_contract_factory("LlmContract")
contract = factory.deploy()

analysis = contract.process_with_llm(args=["input_data"]).analyze(
    provider="openai",
    model="gpt-4o",
    runs=100,                                    # Number of simulations (default: 100)
    config=None,                                 # Provider-specific config
    plugin=None,                                 # Plugin name
    plugin_config=None,                          # Plugin configuration
    genvm_datetime="2024-01-15T10:30:00Z",       # Fixed datetime (ISO format)
)
```

### `MethodStatsSummary` Fields

| Field | Type | Description |
|-------|------|-------------|
| `method` | `str` | Contract method name |
| `args` | `list` | Arguments passed to the method |
| `total_runs` | `int` | Total number of simulation runs |
| `successful_runs` | `int` | Number of successful executions |
| `failed_runs` | `int` | Number of failed executions |
| `unique_states` | `int` | Number of unique contract states observed |
| `success_rate` | `float` | Percentage of successful runs |
| `reliability_score` | `float` | Percentage of runs with the most common state |
| `execution_time` | `float` | Total time for all simulations (seconds) |

```python
print(f"Method: {analysis.method}")
print(f"Success rate: {analysis.success_rate:.2f}%")
print(f"Reliability: {analysis.reliability_score:.2f}%")
print(f"Unique states: {analysis.unique_states}")
print(f"Execution time: {analysis.execution_time:.1f}s")
```

## Example: Complete Test Suite

```python
"""tests/test_storage_studio.py"""

from gltest import get_contract_factory, get_default_account, get_validator_factory
from gltest.assertions import tx_execution_succeeded, tx_execution_failed
from gltest.types import MockedLLMResponse, MockedWebResponse
import json


class TestStorageStudio:
    """Storage contract tests using Studio mode."""

    def test_deploy_and_read(self, default_account):
        factory = get_contract_factory("Storage")
        contract = factory.deploy(args=["hello"], account=default_account)

        result = contract.get_storage().call()
        assert result == "hello"

    def test_write_and_verify(self, default_account):
        factory = get_contract_factory("Storage")
        contract = factory.deploy(args=["hello"], account=default_account)

        tx_receipt = contract.update_storage(args=["world"]).transact()
        assert tx_execution_succeeded(tx_receipt)

        assert contract.get_storage().call() == "world"

    def test_with_mock_validators(self):
        factory = get_contract_factory("LLMContract")
        validator_factory = get_validator_factory()

        mock_response: MockedLLMResponse = {
            "nondet_exec_prompt": {
                "analyze": "positive"
            }
        }

        validators = validator_factory.batch_create_mock_validators(
            count=5,
            mock_llm_response=mock_response
        )

        ctx = {
            "validators": [v.to_dict() for v in validators],
            "genvm_datetime": "2024-06-01T12:00:00Z"
        }

        contract = factory.deploy(transaction_context=ctx)
        tx = contract.analyze(args=["analyze this text"]).transact(
            transaction_context=ctx
        )
        assert tx_execution_succeeded(tx)

    def test_with_mock_web(self):
        factory = get_contract_factory("PriceOracle")
        validator_factory = get_validator_factory()

        mock_web: MockedWebResponse = {
            "nondet_web_request": {
                "https://api.example.com/price": {
                    "method": "GET",
                    "status": 200,
                    "body": json.dumps({"price": 42000})
                }
            }
        }

        validators = validator_factory.batch_create_mock_validators(
            count=5,
            mock_web_response=mock_web
        )

        ctx = {"validators": [v.to_dict() for v in validators]}
        contract = factory.deploy(transaction_context=ctx)
        tx = contract.update_price().transact(transaction_context=ctx)
        assert tx_execution_succeeded(tx)
```

Run:

```bash
gltest tests/test_storage_studio.py -v
```

## Troubleshooting

### Deployment Failures

Contract deployment can fail due to insufficient funds, invalid code, or network issues:

```python
try:
    contract = factory.deploy(args=["initial_value"])
except DeploymentError as e:
    print(f"Deployment failed: {e}")
```

### Transaction Timeouts

Transactions may be slow due to network congestion or consensus delays:

```python
tx_receipt = contract.set_value(args=["new_value"]).transact(
    wait_interval=2000,  # Increase from default
    wait_retries=20,     # More attempts
)
```

### Consensus Issues

Transactions may fail due to consensus problems:

```python
# More rotations for better reliability
contract = factory.deploy(consensus_max_rotations=10)

# Or skip consensus entirely for debugging
# gltest --leader-only
```

### Contract Not Found

```
your_project/
├── contracts/           # Default directory
│   └── my_contract.py
└── tests/
    └── test_contract.py

# Or specify a custom directory
gltest --contracts-dir /path/to/contracts
```

### Contract Structure Issues

Contracts must inherit from `gl.Contract`:

```python
# Correct
from genlayer import *

class MyContract(gl.Contract):
    pass

# Wrong — missing gl.Contract inheritance
class MyContract:
    pass
```

### Environment Issues

```bash
python --version         # Must be >= 3.12
docker ps                # GenLayer Studio must be running
pip list | grep genlayer-test
```
