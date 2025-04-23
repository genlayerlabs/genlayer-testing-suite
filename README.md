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
from gltest import get_contract_factory, default_account, create_account
from gltest.assertions import tx_execution_succeeded

factory = get_contract_factory("MyContract")
# Deploy a contract with default account
contract = factory.deploy() # This will be deployed with default_account
assert contract.account == default_account

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
- [Installation and Usage](#-installation-and-usage)
- [Key Features](#-key-features)
- [Examples](#-examples)
- [Best Practices](#-best-practices)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)
- [Acknowledgments](#-acknowledgments)

## Prerequisites

Before installing GenLayer Testing Suite, ensure you have the following prerequisites installed:

- Python (>=3.8)
- GenLayer Studio (Docker deployment)
- pip (Python package installer)

## 🛠️ Installation and Usage

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

## 🚀 Key Features

- **Pytest Integration** – Extends pytest to support intelligent contract testing, making it familiar and easy to adopt.
- **Account & Transaction Management** – Create, fund, and track accounts and transactions within the GenLayer Simulator.
- **Contract Deployment & Interaction** – Deploy contracts, call methods, and monitor events seamlessly.
- **CLI Compatibility** – Run tests directly from the command line, ensuring smooth integration with the GenLayer CLI.
- **State Injection & Consensus Simulation** – Modify contract states dynamically and simulate consensus scenarios for advanced testing.
- **Prompt Testing & Statistical Analysis** – Evaluate and statistically test prompts for AI-driven contract execution.
- **Scalability to Security & Audit Tools** – Designed to extend into security testing and smart contract auditing.

## 📚 Examples

### Contract Example

For the following examples, we'll use a simple Storage contract:

```python
class Storage:
    def __init__(self, initial_value: str):
        self.value = initial_value

    def get_value(self) -> str:
        return self.value

    def set_value(self, new_value: str):
        self.value = new_value
```

### Contract Deployment

```python
from gltest import get_contract_factory, default_account

def test_deployment():
    # Get the contract factory for your contract
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

```python
from gltest import get_contract_factory, default_account

def test_read_methods():
    # Get the contract factory and deploy the contract
    factory = get_contract_factory("Storage")
    contract = factory.deploy(account=default_account)
    
    # Call a read-only method
    result = contract.get_value()  # No arguments needed for read methods
    
    # Assert the result
    assert result == "initial_value"
```

### Write Methods

```python
from gltest import get_contract_factory, default_account

def test_write_methods():
    # Get the contract factory and deploy the contract
    factory = get_contract_factory("Storage")
    contract = factory.deploy(account=default_account)
    
    # Call a write method with arguments
    tx_receipt = contract.set_value(
        args=["new_value"],  # Method arguments
        value=0,  # Optional: amount of native currency to send
        consensus_max_rotations=3,  # Optional: max consensus rotations
        leader_only=False,  # Optional: whether to run only on leader
        wait_interval=1,  # Optional: seconds between status checks
        wait_retries=10,  # Optional: max number of retries
    )
    
    # Verify the transaction was successful
    assert tx_receipt["status"] == "FINALIZED"
    
    # Verify the value was updated
    assert contract.get_value() == "new_value"
```

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
   ```python
   try:
       contract = factory.deploy(args=["initial_value"])
   except DeploymentError as e:
       print(f"Deployment failed: {e}")
   ```

2. **Transaction Timeouts**
   ```python
   tx_receipt = contract.set_value(
       args=["new_value"],
       wait_interval=2,  # Increase wait interval
       wait_retries=20,  # Increase retries
   )
   ```

3. **Consensus Issues**
   ```python
   contract = factory.deploy(
       consensus_max_rotations=5,  # Increase rotations
       leader_only=True,  # Try leader-only mode
   )
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



