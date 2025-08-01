# GenLayer Testing Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/license/mit/)
[![Discord](https://dcbadge.vercel.app/api/server/8Jm4v89VAu?compact=true&style=flat)](https://discord.gg/VpfmXEMN66)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/yeagerai.svg?style=social&label=Follow%20%40GenLayer)](https://x.com/GenLayer)
[![PyPI version](https://badge.fury.io/py/genlayer-test.svg)](https://badge.fury.io/py/genlayer-test)
[![Documentation](https://img.shields.io/badge/docs-genlayer-blue)](https://docs.genlayer.com/api-references/genlayer-test)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## About

The GenLayer Testing Suite is a powerful testing framework designed to streamline the development and validation of intelligent contracts within the GenLayer ecosystem. Built on top of [pytest](https://docs.pytest.org/en/stable/) and [genlayer-py](https://docs.genlayer.com/api-references/genlayer-py), this suite provides developers with a comprehensive set of tools for deploying, interacting with, and testing intelligent contracts efficiently in a simulated GenLayer environment.

## 🚀 Quick Start

### Installation

```bash
pip install genlayer-test
```

### Basic Usage

```python
from gltest import get_contract_factory, get_default_account, create_account
from gltest.assertions import tx_execution_succeeded

factory = get_contract_factory("MyContract")
# Deploy a contract with default account
contract = factory.deploy() # This will be deployed with the default account
assert contract.account == get_default_account()

# Deploy a contract with other account
other_account = create_account()
contract = factory.deploy(account=other_account)
assert contract.account == other_account

# Interact with the contract
result = contract.get_value().call()  # Read method
tx_receipt = contract.set_value(args=["new_value"]).transact()  # Write method

assert tx_execution_succeeded(tx_receipt)
```

## 📋 Table of Contents

- [About](#about)
- [Quick Start](#-quick-start)
- [Prerequisites](#prerequisites)
- [Installation and Usage](#installation-and-usage)
- [Key Features](#-key-features)
- [Examples](#-examples)
  - [Project Structure](#project-structure)
  - [Storage Contract Example](#storage-contract-example)
  - [Contract Deployment](#contract-deployment)
  - [Read Methods](#read-methods)
  - [Write Methods](#write-methods)
  - [Assertions](#assertions)
  - [Test Fixtures](#test-fixtures)
  - [Statistical Analysis with `.analyze()`](#statistical-analysis-with-analyze)
  - [Mock LLM Responses](#mock-llm-responses)
- [Best Practices](#-best-practices)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## Prerequisites

Before installing GenLayer Testing Suite, ensure you have the following prerequisites installed:

- Python (>=3.12)
- GenLayer Studio (Docker deployment)
- pip (Python package installer)

## Installation and Usage

### Installation Options

1. Install from PyPI (recommended):
```bash
$ pip install genlayer-test
```

2. Install from source:
```bash
$ git clone https://github.com/yeagerai/genlayer-testing-suite
$ cd genlayer-testing-suite
$ pip install -e .
```

### Configuration

The GenLayer Testing Suite can be configured using an optional but recommended `gltest.config.yaml` file in your project root. While not required, this file helps manage network configurations, contract paths, and environment settings in a centralized way, making it easier to maintain different environments and share configurations across team members.

```yaml
# gltest.config.yaml
networks:
  default: localnet  # Default network to use

  localnet:  # Local development network configuration (pre-configured)
    url: "http://127.0.0.1:4000/api"
    leader_only: false  # Set to true to run all contracts in leader-only mode by default

  studionet:  # Studio network configuration (pre-configured)
    # Pre-configured network - accounts are automatically generated
    # You can override any settings if needed

  testnet_asimov:  # Test network configuration (pre-configured)
    # Pre-configured network - requires accounts to be specified
    accounts:
      - "${ACCOUNT_PRIVATE_KEY_1}"
      - "${ACCOUNT_PRIVATE_KEY_2}"
      - "${ACCOUNT_PRIVATE_KEY_3}"
    from: "${ACCOUNT_PRIVATE_KEY_2}"  # Optional: specify default account

  custom_network:  # Custom network configuration
    id: 1234
    url: "http://custom.network:8545"
    accounts:
      - "${CUSTOM_ACCOUNT_1}"
      - "${CUSTOM_ACCOUNT_2}"
    from: "${CUSTOM_ACCOUNT_1}"  # Optional: specify default account

paths:
  contracts: "contracts"  # Path to your contracts directory
  artifacts: "artifacts" # Path to your artifacts directory

environment: .env  # Path to your environment file containing private keys and other secrets
```

Key configuration sections:

1. **Networks**: Define different network environments
   - `default`: Specifies which network to use by default
   - **Pre-configured Networks**:
     - `localnet`: Local development network with auto-generated test accounts
     - `studionet`: GenLayer Studio network with auto-generated test accounts
     - `testnet_asimov`: Public testnet (requires account configuration)
   - Network configurations can include:
     - `url`: The RPC endpoint for the network (optional for pre-configured networks)
     - `id`: Chain ID (optional for pre-configured networks)
     - `accounts`: List of account private keys (using environment variables)
     - `from`: Specify which account to use as the default for transactions (optional, defaults to first account)
     - `leader_only`: Leader only mode
   - For custom networks (non-pre-configured), `id`, `url`, and `accounts` are required fields

**Note on Environment Variables**: When using environment variables in your configuration (e.g., `${ACCOUNT_PRIVATE_KEY_1}`), ensure they are properly set in your `environment` file. If an environment variable is not found, the system will raise a clear error message indicating which variable is missing.

**Default Account Selection**: The `from` field allows you to specify which account from the `accounts` list should be used as the default for deployments and transactions. If not specified, the first account in the list is used by default. This is useful when you want a specific account to be the primary account for your tests without having to specify it in every transaction.

Example:
```yaml
testnet_asimov:
  accounts:
    - "${DEPLOYER_KEY}"      # accounts[0]
    - "${USER_KEY}"          # accounts[1] 
    - "${ADMIN_KEY}"         # accounts[2]
  from: "${ADMIN_KEY}"       # Use ADMIN_KEY as default instead of DEPLOYER_KEY
```

2. **Paths**: Define important directory paths
   - `contracts`: Location of your contract files
   - `artifacts`: Location of your artifacts files (analysis results will be stored here)

3. **Environment**: Path to your `.env` file containing sensitive information like private keys

If you don't provide a config file, the suite will use default values. You can override these settings using command-line arguments. For example:
```bash
# Override the default network
gltest --network testnet_asimov

# Override the contracts directory
gltest --contracts-dir custom/contracts/path
```

### Running Tests

1. Run all tests:
```bash
$ gltest
```

2. Run specific test file:
```bash
$ gltest tests/test_mycontract.py
```

3. Run tests with specific markers:
```bash
$ gltest -m "integration"
```

4. Run tests with verbose output:
```bash
$ gltest -v
```

5. Run tests in specific contracts directories, by default `<path_to_contracts>` is set to `contracts/`
```bash
$ gltest --contracts-dir <path_to_contracts>
```

6. Run tests on a specific network:
```bash
# Run tests on localnet (default)
$ gltest --network localnet

# Run tests on studionet
$ gltest --network studionet

# Run tests on testnet (requires account configuration)
$ gltest --network testnet_asimov

# Run tests on a custom network
$ gltest --network custom_network
```
The `--network` flag allows you to specify which network configuration to use from your `gltest.config.yaml`. If not specified, it will use the `default` network defined in your config file.

**Pre-configured Networks**:
- `localnet` and `studionet`: Work out of the box with auto-generated test accounts
- `testnet_asimov`: Requires account configuration in `gltest.config.yaml`

When using `testnet_asimov` without proper account configuration, you'll receive a clear error message directing you to configure accounts in your config file.

7. Run tests with a custom RPC url
```bash
$ gltest --rpc-url <custom_rpc_url>
```

8. Run tests with a default wait interval for waiting transaction receipts
```bash
$ gltest --default-wait-interval <default_wait_interval>
```

9. Run tests with a default wait retries for waiting transaction receipts
```bash
$ gltest --default-wait-retries <default_wait_retries>
```

10. Run tests with mocked LLM responses (localnet only)
```bash
$ gltest --test-with-mocks
```
The `--test-with-mocks` flag enables mocking of LLM responses when creating validators. This is particularly useful for:
- Testing without actual LLM API calls
- Ensuring deterministic test results
- Faster test execution
- Testing specific edge cases with controlled responses

When using this flag with the `setup_validators` fixture, you can provide custom mock responses:
```python
def test_with_mocked_llm(setup_validators):
    # Setup validators with a specific mock response
    mock_response = {"result": "This is a mocked LLM response"}
    setup_validators(mock_response=mock_response)
    
    # Your LLM-based contract will receive the mocked response
    contract = factory.deploy()
    result = contract.llm_method()  # Will use the mocked response
```

Note: This feature is only available when running tests on localnet.

11. Run tests with leader-only mode enabled
```bash
$ gltest --leader-only
```
The `--leader-only` flag configures all contract deployments and write operations to run only on the leader node. This is useful for:
- Faster test execution by avoiding consensus
- Testing specific leader-only scenarios
- Development and debugging purposes
- Reducing computational overhead in test environments

When this flag is enabled, all contracts deployed and all write transactions will automatically use leader-only mode, regardless of individual method parameters.

**Note:** Leader-only mode is only available for studio-based networks (localhost, 127.0.0.1, *.genlayer.com, *.genlayerlabs.com). When enabled on other networks, it will have no effect and a warning will be logged.

## 🚀 Key Features

- **Pytest Integration** – Extends pytest to support intelligent contract testing, making it familiar and easy to adopt.
- **Account & Transaction Management** – Create, fund, and track accounts and transactions within the GenLayer Simulator.
- **Contract Deployment & Interaction** – Deploy contracts, call methods, and monitor events seamlessly.
- **CLI Compatibility** – Run tests directly from the command line, ensuring smooth integration with the GenLayer CLI.
- **State Injection & Consensus Simulation** – Modify contract states dynamically and simulate consensus scenarios for advanced testing.
- **Prompt Testing & Statistical Analysis** – Evaluate and statistically test prompts for AI-driven contract execution.
- **Scalability to Security & Audit Tools** – Designed to extend into security testing and smart contract auditing.

## 📚 Examples

### Project Structure

Before diving into the examples, let's understand the basic project structure:

```
genlayer-example/
├── contracts/              # Contract definitions
│   └── storage.py          # Example storage contract
├── test/                   # Test files
│   └── test_contract.py    # Contract test cases
└── gltest.config.yaml      # Configuration file
```

### Storage Contract Example

Let's examine a simple Storage contract that demonstrates basic read and write operations:

```python
# { "Depends": "py-genlayer:test" }

from genlayer import *


# contract class
class Storage(gl.Contract):
    # State variable to store data
    storage: str

    # Constructor - initializes the contract state
    def __init__(self, initial_storage: str):
        self.storage = initial_storage

    # Read method - marked with @gl.public.view decorator
    # Returns the current storage value
    @gl.public.view
    def get_storage(self) -> str:
        return self.storage

    # Write method - marked with @gl.public.write decorator
    # Updates the storage value
    @gl.public.write
    def update_storage(self, new_storage: str) -> None:
        self.storage = new_storage
```

Key features demonstrated in this contract:
- State variable declaration
- Constructor with initialization
- Read-only method with `@gl.public.view` decorator
- State-modifying method with `@gl.public.write` decorator
- Type hints for better code clarity

### Contract Deployment

The GenLayer Testing Suite provides two methods for deploying contracts:

1. **`deploy()`** - Returns the deployed contract instance (recommended for most use cases)
2. **`deploy_contract_tx()`** - Returns only the transaction receipt

Here's how to deploy the Storage contract:

```python
from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded
from gltest.utils import extract_contract_address

def test_deployment():
    # Get the contract factory for your contract
    # it will search in the contracts directory
    factory = get_contract_factory("Storage")
    
    # Method 1: Deploy the contract with constructor arguments (recommended)
    contract = factory.deploy(
        args=["initial_value"],  # Constructor arguments
        account=get_default_account(),  # Account to deploy from
        consensus_max_rotations=3,  # Optional: max consensus rotations
    )
    
    # Contract is now deployed and ready to use
    assert contract.address is not None
    
    # Method 2: Deploy and get only the receipt
    receipt = factory.deploy_contract_tx(
        args=["initial_value"],
        account=get_default_account(),
    )
    
    # Verify deployment succeeded
    assert tx_execution_succeeded(receipt)

    # Get the contract address
    contract_address = extract_contract_address(receipt)
```

### Read Methods

Reading from the contract requires calling `.call()` on the method:

```python
from gltest import get_contract_factory

def test_read_methods():

    # Get the contract factory and deploy the contract
    factory = get_contract_factory("Storage")
    contract = factory.deploy()

    # Call a read-only method
    result = contract.get_storage(args=[]).call()
    
    # Assert the result matches the initial value
    assert result == "initial_value"
```

### Write Methods

Writing to the contract requires calling `.transact()` on the method. Method arguments are passed to the write method, while transaction parameters are passed to `.transact()`:

```python
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

def test_write_methods():
    # Get the contract factory and deploy the contract
    factory = get_contract_factory("Storage")
    contract = factory.deploy()
    
    # Call a write method with arguments
    tx_receipt = contract.update_storage(
        args=["new_value"],  # Method arguments
    ).transact(
        value=0,  # Optional: amount of native currency to send
        consensus_max_rotations=3,  # Optional: max consensus rotations
        wait_interval=1,  # Optional: seconds between status checks
        wait_retries=10,  # Optional: max number of retries
    )
    
    # Verify the transaction was successful
    assert tx_execution_succeeded(tx_receipt)
    
    # Verify the value was updated
    assert contract.get_storage().call() == "new_value"
```

### Assertions

The GenLayer Testing Suite provides powerful assertion functions to validate transaction results and their output:

#### Basic Transaction Assertions

```python
from gltest.assertions import tx_execution_succeeded, tx_execution_failed

# Basic success/failure checks
assert tx_execution_succeeded(tx_receipt)
assert tx_execution_failed(tx_receipt)  # Opposite of tx_execution_succeeded
```

#### Advanced Output Matching

You can match specific patterns in the transaction's stdout and stderr output using regex patterns, similar to pytest's `match` parameter:

```python
# Simple string matching
assert tx_execution_succeeded(tx_receipt, match_std_out="Process completed")
assert tx_execution_failed(tx_receipt, match_std_err="Warning: deprecated")

# Regex pattern matching
assert tx_execution_succeeded(tx_receipt, match_std_out=r".*code \d+")
assert tx_execution_failed(tx_receipt, match_std_err=r"Method.*failed")
```

#### Assertion Function Parameters

Both `tx_execution_succeeded` and `tx_execution_failed` accept the following parameters:

- `result`: The transaction result object from contract method calls
- `match_std_out` (optional): String or regex pattern to match in stdout
- `match_std_err` (optional): String or regex pattern to match in stderr

**Network Compatibility**: The stdout/stderr matching feature (`match_std_out` and `match_std_err` parameters) is only available when running on **studionet** and **localnet**. These features are not supported on testnet.

For more example contracts, check out the [contracts directory](tests/examples/contracts) which contains various sample contracts demonstrating different features and use cases.

### Test Fixtures

The GenLayer Testing Suite provides reusable pytest fixtures in `gltest.fixtures` to simplify common testing operations. These fixtures can be imported and used in your test files to avoid repetitive setup code.

#### Available Fixtures

The following fixtures are available in `gltest.fixtures`:

- **`gl_client`** (session scope) - GenLayer client instance for network operations
- **`default_account`** (session scope) - Default account for testing and deployments
- **`accounts`** (session scope) - List of test accounts for multi-account scenarios
- **`setup_validators`** (function scope) - Function to create test validators for LLM operations

##### 1. `gl_client` (session scope)
Provides a GenLayer PY client instance that's created once per test session. This is useful for operations that interact directly with the GenLayer network.

```python
def test_client_operations(gl_client):
    # Use the client for network operations
    tx_hash = "0x1234..."
    transaction = gl_client.get_transaction(tx_hash)
```

##### 2. `default_account` (session scope)
Provides the default account used to execute transactions when no account is specified.

```python
def test_with_default_account(default_account):
    # Use the default account for deployments
    factory = get_contract_factory("MyContract")
    contract = factory.deploy(account=default_account)
```

##### 3. `accounts` (session scope)
Provides a list of account objects loaded from the private keys defined in `gltest.config.yaml` for the current network, or pre-created test accounts if no config is present

```python
def test_multiple_accounts(accounts):
    # Get multiple accounts for testing
    sender = accounts[0]
    receiver = accounts[1]
    
    # Test transfers or multi-party interactions
    contract.transfer(args=[receiver.address, 100], account=sender)
```

##### 4. `setup_validators` (function scope)
Creates test validators for localnet environment. This fixture is particularly useful for testing LLM-based contract methods and consensus behavior. It yields a function that allows you to configure validators with custom settings.

```python
def test_with_validators(setup_validators):
    # Setup validators with default configuration
    setup_validators()
    
    # Or setup with custom mock responses for testing
    mock_response = {"result": "mocked LLM response"}
    setup_validators(mock_response=mock_response, n_validators=3)
    
    # Now test your LLM-based contract methods
    contract = factory.deploy()
    result = contract.llm_based_method()
```

Parameters for `setup_validators`:
- `mock_response` (dict, optional): Mock validator response when using `--test-with-mocks` flag
- `n_validators` (int, optional): Number of validators to create (default: 5)

#### Using Fixtures in Your Tests

To use these fixtures, simply import them and include them as parameters in your test functions:

```python
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

def test_complete_workflow(gl_client, default_account, accounts, setup_validators):
    # Setup validators for LLM operations
    setup_validators()
    
    # Deploy contract with default account
    factory = get_contract_factory("MyContract")
    contract = factory.deploy(account=default_account)
    
    # Interact using other accounts
    other_account = accounts[1]
    tx_receipt = contract.some_method(args=["value"], account=other_account)
    
    assert tx_execution_succeeded(tx_receipt)
```

Fixtures help maintain clean, DRY test code by:
- Eliminating repetitive setup code
- Ensuring consistent test environments
- Managing resource cleanup automatically
- Providing appropriate scoping for performance
### Statistical Analysis with `.analyze()`

The GenLayer Testing Suite provides a powerful `.analyze()` method for write operations that performs statistical analysis through multiple simulation runs. This is particularly useful for testing LLM-based contracts where outputs may vary:

```python
from gltest import get_contract_factory

def test_analyze_method():
    factory = get_contract_factory("LlmContract")
    contract = factory.deploy()
    
    # Analyze a write method's behavior across multiple runs
    analysis = contract.process_with_llm(args=["input_data"]).analyze(
        provider="openai",           # LLM provider
        model="gpt-4o",             # Model to use
        runs=100,                   # Number of simulation runs (default: 100)
        config=None,                # Optional: provider-specific config
        plugin=None,                # Optional: plugin name
        plugin_config=None,         # Optional: plugin configuration
    )
    
    # Access analysis results
    print(f"Method: {analysis.method}")
    print(f"Success rate: {analysis.success_rate:.2f}%")
    print(f"Reliability score: {analysis.reliability_score:.2f}%")
    print(f"Unique states: {analysis.unique_states}")
    print(f"Execution time: {analysis.execution_time:.1f}s")
    
    # The analysis returns a MethodStatsSummary object with:
    # - method: The contract method name
    # - args: Arguments passed to the method
    # - total_runs: Total number of simulation runs
    # - successful_runs: Number of successful executions
    # - failed_runs: Number of failed executions
    # - unique_states: Number of unique contract states observed
    # - reliability_score: Percentage of runs with the most common state
    # - execution_time: Total time for all simulations
```

The `.analyze()` method helps you:
- Test non-deterministic contract methods
- Measure consistency of LLM-based operations
- Identify edge cases and failure patterns
- Benchmark performance across multiple runs

### Mock LLM Responses

The Mock LLM system allows you to simulate Large Language Model responses in GenLayer tests. This is essential for creating deterministic tests by providing predefined responses instead of relying on actual LLM calls.

#### Basic Structure

The mock system consists of a response dictionary that maps GenLayer methods to their mocked responses:

```python
mock_response = {
    "response": {},                               # Optional: mocks gl.nondet.exec_prompt
    "eq_principle_prompt_comparative": {},        # Optional: mocks gl.eq_principle.prompt_comparative
    "eq_principle_prompt_non_comparative": {}     # Optional: mocks gl.eq_principle.prompt_non_comparative
}

setup_validators(mock_response)
```

#### Method Mappings

| Mock Key | GenLayer Method |
|----------|----------------|
| `"response"` | `gl.nondet.exec_prompt` |
| `"eq_principle_prompt_comparative"` | `gl.eq_principle.prompt_comparative` |
| `"eq_principle_prompt_non_comparative"` | `gl.eq_principle.prompt_non_comparative` |

#### How It Works

The mock system works by pattern matching against the user message that gets built internally. When a GenLayer method is called:

1. A user message is constructed internally (`<user_message>`)
2. The mock system searches for strings within that message
3. If a matching string is found in the mock dictionary, the associated response is returned

##### String Matching Rules

The system performs **substring matching** on the user message. The key in your mock dictionary must be contained within the actual user message.

#### Examples

##### Basic Example

```python
# Mock setup
mock_response = {
    "eq_principle_prompt_comparative": {
        "The value of give_coin has to match": True
    }
}
setup_validators(mock_response)

# In your contract
result = gl.eq_principle.prompt_comparative(
    get_wizard_answer, 
    "The value of give_coin has to match"  # This string will be matched
)
# result will be True
```

##### Substring Matching Examples

✅ **Will work** - Partial match:
```python
"eq_principle_prompt_comparative": {
    "The value of give_coin": True  # Substring of the full message
}
```

❌ **Won't work** - Extra words break the match:
```python
"eq_principle_prompt_comparative": {
    "The good value of give_coin": True  # "good" is not in the actual message
}
```

##### Complete Example

```python
from gltest import get_contract_factory
from gltest.fixtures import setup_validators

def test_with_mocked_llm(setup_validators):
    # Define mock responses
    mock_response = {
        "response": {
            "What is the weather?": "It's sunny today",
            "Calculate 2+2": "4"
        },
        "eq_principle_prompt_comparative": {
            "values must be equal": True,
            "amounts should match": False
        },
        "eq_principle_prompt_non_comparative": {
            "Is this valid?": True
        }
    }
    
    # Initialize the mock system
    setup_validators(mock_response)
    
    # Deploy and test your contract
    factory = get_contract_factory("MyLLMContract")
    contract = factory.deploy()
    
    # Your LLM methods will use the mocked responses
    result = contract.check_weather()  # Uses mocked response
```

#### Best Practices

1. **Be specific with match strings**: Use unique substrings that won't accidentally match other prompts
2. **Test your matches**: Verify that your mock strings actually appear in the generated user messages
3. **Keep mocks simple**: Mock responses should be minimal and focused on the test case
4. **Document your mocks**: Comment why specific responses are mocked for future reference
5. **Use with `--test-with-mocks` flag**: Enable mocking when running tests: `gltest --test-with-mocks`

#### Notes

- Mock responses are only available when running tests on localnet
- The `setup_validators` fixture handles the mock setup when provided with a mock_response
- Mocking is particularly useful for CI/CD pipelines where deterministic results are required

## 📝 Best Practices

1. **Test Organization**
   - Keep tests in a dedicated `tests` directory
   - Use descriptive test names
   - Group related tests using pytest markers

2. **Contract Deployment**
   - Always verify deployment success
   - Use appropriate consensus parameters
   - Handle deployment errors gracefully

3. **Transaction Handling**
   - Always wait for transaction finalization
   - Verify transaction status
   - Handle transaction failures appropriately

4. **State Management**
   - Reset state between tests
   - Use fixtures for common setup
   - Avoid test dependencies

## 🔧 Troubleshooting

### Common Issues

1. **Deployment Failures**
   - **Problem**: Contract deployment fails due to various reasons like insufficient funds, invalid contract code, or network issues.
   - **Solution**: Implement proper error handling
   ```python
   try:
       contract = factory.deploy(args=["initial_value"])
   except DeploymentError as e:
       print(f"Deployment failed: {e}")
   ```

2. **Transaction Timeouts**
   - **Problem**: Transactions take too long to complete or fail due to network congestion or consensus delays.
   - **Solution**: Adjust timeout parameters and implement retry logic:
   ```python
   tx_receipt = contract.set_value(
       args=["new_value"],
   ).transact(
       wait_interval=2,  # Increase wait interval between status checks
       wait_retries=20,  # Increase number of retry attempts
   )
   ```

3. **Consensus Issues**
   - **Problem**: Transactions fail due to consensus-related problems like network partitions or slow consensus.
   - **Solution**: Adjust consensus parameters and try different modes:
   ```python
   # Try with increased consensus parameters
   contract = factory.deploy(
       consensus_max_rotations=5,  # Increase number of consensus rotations
   )
   
   # For critical operations, use more conservative settings
   contract = factory.deploy(
       consensus_max_rotations=10,  # More rotations for better reliability
       wait_interval=3,  # Longer wait between checks
       wait_retries=30  # More retries for consensus
   )
   ```

4. **Contracts Directory Issues**
   - **Problem**: `get_contract_factory` can't find your contract files.
   - **Solution**: Ensure proper directory structure and configuration:
   ```bash
   # Default structure
   your_project/
   ├── contracts/           # Default contracts directory
   │   └── my_contract.py   # Your contract file
   └── tests/
       └── test_contract.py # Your test file
   
   # If using a different directory structure
   gltest --contracts-dir /path/to/your/contracts
   ```

5. **Contract File Naming and Structure**
   - **Problem**: Contracts aren't being recognized or loaded properly.
   - **Solution**: Follow the correct naming and structure conventions:
   ```python
   # Correct file: contracts/my_contract.py

   # Correct structure:
   from genlayer import *
   
   class MyContract(gl.Contract):
       # Contract code here
       pass
   

   # Incorrect structure:
   class MyContract:  # Missing gl.Contract inheritance
       pass
   ```

6. **Environment Setup Issues**
   - **Problem**: Tests fail due to missing or incorrect environment setup.
   - **Solution**: Verify your environment:
   ```bash
   # Check Python version
   python --version  # Should be >= 3.12
   
   # Check GenLayer Studio status
   docker ps  # Should show GenLayer Studio running
   
   # Verify package installation
   pip list | grep genlayer-test  # Should show installed version
   ```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- [Documentation](https://docs.genlayer.com/api-references/genlayer-test)
- [Discord Community](https://discord.gg/VpfmXEMN66)
- [GitHub Issues](https://github.com/yeagerai/genlayer-testing-suite/issues)
- [Twitter](https://x.com/GenLayer)



