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
contract = factory.deploy() # This will be deployed with default_account
assert contract.account == get_default_account()

# Deploy a contract with other account
other_account = create_account()
contract = factory.deploy(account=other_account)
assert contract.account == other_account

# Interact with the contract
result = contract.get_value()  # Read method
tx_receipt = contract.set_value(args=["new_value"])  # Write method

assert tx_execution_succeeded(tx_receipt)
```

## 📋 Table of Contents

- [About](#about)
- [Quick Start](#-quick-start)
- [Prerequisites](#prerequisites)
- [Installation and Usage](#installation-and-usage)
- [Key Features](#-key-features)
- [Examples](#-examples)
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

  localnet:  # Local development network configuration
    url: "http://127.0.0.1:4000/api"

  testnet_asimov:  # Test network configuration
    id: 4221
    url: "http://34.32.169.58:9151"
    accounts:
      - "${ACCOUNT_PRIVATE_KEY_1}"
      - "${ACCOUNT_PRIVATE_KEY_2}"
      - "${ACCOUNT_PRIVATE_KEY_3}"

paths:
  contracts: "contracts"  # Path to your contracts directory

environment: .env  # Path to your environment file containing private keys and other secrets
```

Key configuration sections:

1. **Networks**: Define different network environments
   - `default`: Specifies which network to use by default
   - Network configurations can include:
     - `url`: The RPC endpoint for the network
     - `id`: Chain ID
     - `accounts`: List of account private keys (using environment variables)
   - Special case for `localnet`:
     - If a network is named `localnet`, missing fields will be filled with default values
     - For all other network names, `id`, `url`, and `accounts` are required fields

2. **Paths**: Define important directory paths
   - `contracts`: Location of your contract files

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

# Run tests on testnet
$ gltest --network testnet_asimov
```
The `--network` flag allows you to specify which network configuration to use from your `gltest.config.yaml`. If not specified, it will use the `default` network defined in your config file.

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
└── test/                   # Test files
    └── test_contract.py    # Contract test cases
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

Here's how to deploy the Storage contract:

```python
from gltest import get_contract_factory, default_account

def test_deployment():
    # Get the contract factory for your contract
    # it will search in the contracts directory
    factory = get_contract_factory("Storage")
    
    # Deploy the contract with constructor arguments
    contract = factory.deploy(
        args=["initial_value"],  # Constructor arguments
        account=default_account,  # Account to deploy from
        consensus_max_rotations=3,  # Optional: max consensus rotations
        leader_only=False,  # Optional: whether to run only on leader
    )
    
    # Contract is now deployed and ready to use
    assert contract.address is not None
```

### Read Methods

Reading from the contract is straightforward:

```python
from gltest import get_contract_factory

def test_read_methods():

    # Get the contract factory and deploy the contract
    factory = get_contract_factory("Storage")
    contract = factory.deploy()

    # Call a read-only method
    result = contract.get_value(args=[])
    
    # Assert the result matches the initial value
    assert result == "initial_value"
```

### Write Methods

Writing to the contract requires transaction handling:

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
        value=0,  # Optional: amount of native currency to send
        consensus_max_rotations=3,  # Optional: max consensus rotations
        leader_only=False,  # Optional: whether to run only on leader
        wait_interval=1,  # Optional: seconds between status checks
        wait_retries=10,  # Optional: max number of retries
    )
    
    # Verify the transaction was successful
    assert tx_execution_succeeded(tx_receipt)
    
    # Verify the value was updated
    assert contract.get_storage() == "new_value"
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
       leader_only=True,  # Try leader-only mode for faster execution
   )
   
   # For critical operations, use more conservative settings
   contract = factory.deploy(
       consensus_max_rotations=10,  # More rotations for better reliability
       leader_only=False,  # Full consensus for better security
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



