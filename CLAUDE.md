# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

GenLayer Testing Suite (`gltest`) is a pytest-based testing framework for GenLayer intelligent contracts. It provides tools for deploying, interacting with, and testing GenLayer contracts in simulated environments.

## Essential Commands

### Development Setup
```bash
# Install dependencies from lockfile
uv sync

# Requires Python >= 3.12
```

### Running Tests
```bash
# Run all tests
gltest

# Run specific test file
gltest tests/test_mycontract.py

# Run tests on different networks
gltest --network localnet  # default
gltest --network testnet_asimov

# Run with custom contracts directory
gltest --contracts-dir /path/to/contracts

# Run with custom artifacts directory
gltest --artifacts-dir /path/to/artifacts

# Run specific test suites
gltest tests/gltest_cli/
gltest tests/gltest/
gltest tests/examples/tests/
```

### Code Formatting
```bash
# Format code with Black
black .

# Check formatting without changes
black --check .
```

### Building
```bash
# Clean and build package
rm -rf dist/ build/ *.egg-info/
uv build
```

### Testing Changes During Development
When making changes to the framework code, sync and run via uv:
```bash
# Sync dependencies (picks up local changes automatically)
uv sync

# Run tests
uv run gltest tests/gltest_cli/
uv run gltest tests/gltest/
```

## Architecture Overview

### Core Components

1. **Contract System** (`gltest/contracts/`)
   - `Contract`: Dynamic proxy for deployed contracts with auto-generated methods
   - `ContractFactory`: Handles contract deployment
   - Methods follow patterns: `.call()` for reads, `.transact()` for writes

2. **Client Management** (`gltest/clients.py`)
   - Manages GenLayer client connections
   - Supports localnet, testnet, and hosted environments
   - Uses caching to avoid recreating clients

3. **Account Management** (`gltest/accounts.py`)
   - Handles blockchain accounts via `eth_account`
   - Network-specific account configuration

4. **Configuration** (`gltest_cli/config/`)
   - User config: `gltest.config.yaml`
   - CLI overrides: `--network`, `--rpc-url`, `--contracts-dir`, `--artifacts-dir`
   - Merged into singleton `GeneralConfig`

5. **Assertions** (`gltest/assertions.py`)
   - `tx_execution_succeeded()`: Verify transaction success
   - `tx_execution_failed()`: Verify transaction failure

### Contract Development Patterns

GenLayer contracts are Python classes:
```python
import genlayer as gl

class MyContract(gl.Contract):
    def __init__(self, initial_value: int):
        self.value = initial_value
    
    @gl.public.view
    def get_value(self) -> int:
        return self.value
    
    @gl.public.write
    def set_value(self, new_value: int):
        self.value = new_value
```

Testing pattern:
```python
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

# Deploy
factory = get_contract_factory("MyContract")
contract = factory.deploy(args=[42])

# Read
value = contract.get_value().call()

# Write
tx = contract.set_value(100).transact()
assert tx_execution_succeeded(tx)

# Statistical analysis of contract methods
stats = contract.set_value(200).analyze(provider="openai", model="gpt-4o", runs=100)
print(stats)  # Shows success rate, reliability score, execution time, etc.
```

### Key Directories

- `gltest/`: Core testing framework
- `gltest_cli/`: CLI implementation and pytest plugin
- `tests/examples/contracts/`: Example GenLayer contracts
- `tests/examples/tests/`: Example test cases
- `contracts/`: Default directory for user contracts

### Network Configuration

Networks are configured in `gltest.config.yaml`:
- `localnet`: Local development (chain ID 61999)
- `testnet_asimov`: Public testnet (chain ID 4221)

Paths can be configured in `gltest.config.yaml`:
- `contracts`: Directory containing contract source files
- `artifacts`: Directory for storing contract artifacts (for future caching)

### Multi-File Contracts

Multi-file contracts use a `runner.json` manifest:
```json
{
  "contract_entry_file": "main_contract.py",
  "contract_class_name": "MainContract"
}
```

## Development Notes

1. The framework extends pytest - all pytest features are available
2. Contracts are discovered automatically from the contracts directory
3. Transaction receipts include consensus information and triggered transactions
4. LLM-based contract methods use `gl.eq_principle_prompt_non_comparative()`
5. Version is managed automatically via semantic release (no manual updates)