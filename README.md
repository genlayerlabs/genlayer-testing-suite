# GenLayer Testing Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/license/mit/)
[![Discord](https://dcbadge.vercel.app/api/server/8Jm4v89VAu?compact=true&style=flat)](https://discord.gg/VpfmXEMN66)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/yeagerai.svg?style=social&label=Follow%20%40GenLayer)](https://x.com/GenLayer)


## About

The GenLayer Testing Suite is a powerful testing framework designed to streamline the development and validation of intelligent contracts within the GenLayer ecosystem. Built on top of [pytest](https://docs.pytest.org/en/stable/), this suite provides developers with a comprehensive set of tools for deploying, interacting with, and testing intelligent contracts efficiently in a simulated GenLayer environment.


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

For more detailed information and advanced usage, please refer to our [documentation](https://docs.genlayer.com/api-references/genlayer-testing-suite).

## 🚀 Key Features
- **Pytest Integration** – Extends pytest to support intelligent contract testing, making it familiar and easy to adopt.

- **Account & Transaction Management** – Create, fund, and track accounts and transactions within the GenLayer Simulator.

- **Contract Deployment & Interaction** – Deploy contracts, call methods, and monitor events seamlessly.

- **CLI Compatibility** – Run tests directly from the command line, ensuring smooth integration with the GenLayer CLI.

- **State Injection & Consensus Simulation** – Modify contract states dynamically and simulate consensus scenarios for advanced testing.

- **Prompt Testing & Statistical Analysis** – Evaluate and statistically test prompts for AI-driven contract execution.

- **Scalability to Security & Audit Tools** – Designed to extend into security testing and smart contract auditing.


By leveraging the GenLayer Testing Suite, developers can ensure their contracts perform reliably and securely before deployment on the live network. 