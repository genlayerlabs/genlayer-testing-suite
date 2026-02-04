# Direct Execution Mode

Run GenLayer intelligent contracts directly in Python for ultra-fast unit testing.

## Overview

The Direct Runner executes contract code in-memory without the GenLayer simulator. This provides:

- **Speed**: ~milliseconds per test vs minutes with simulator
- **Simplicity**: No Docker, no RPC, no network setup
- **Cheatcodes**: Foundry-style test utilities (prank, snapshot, expect_revert)

### When to Use Each Mode

| Direct Mode | Simulator Mode |
|-------------|----------------|
| Unit tests | Integration tests |
| Rapid iteration | Consensus validation |
| CI/CD pipelines | Multi-validator scenarios |
| Logic validation | Full network behavior |

## Installation

Direct mode is included in `genlayer-test`. No additional installation needed.

```bash
pip install genlayer-test
```

## Quick Start

```python
def test_storage(direct_vm, direct_deploy):
    # Deploy contract
    storage = direct_deploy("contracts/Storage.py", "initial")

    # Interact
    assert storage.get_storage() == "initial"
    storage.update_storage("updated")
    assert storage.get_storage() == "updated"
```

Run with pytest:

```bash
pytest tests/ -v
```

## Fixtures

### `direct_vm`

The VM context providing cheatcodes and state management.

```python
def test_example(direct_vm):
    direct_vm.sender = some_address
    direct_vm.warp("2024-06-15T12:00:00Z")
```

### `direct_deploy`

Factory function for deploying contracts.

```python
def test_deploy(direct_deploy):
    # With constructor args
    token = direct_deploy("contracts/Token.py", "MyToken", "MTK", 1000000)

    # With keyword args
    registry = direct_deploy(
        "contracts/Registry.py",
        admin="0x1234...",
        fee_rate=100
    )
```

### Address Fixtures

| Fixture | Description |
|---------|-------------|
| `direct_alice` | Test address (deterministic) |
| `direct_bob` | Test address (deterministic) |
| `direct_charlie` | Test address (deterministic) |
| `direct_owner` | Default sender address |
| `direct_accounts` | List of 10 test addresses |

**Note**: Address fixtures created before contract deployment return `bytes`. After deployment (when genlayer is loaded), use `create_address()` for proper `Address` objects:

```python
def test_addresses(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/MyContract.py")

    # Now create addresses (returns Address objects)
    from gltest.direct import create_address
    alice = create_address("alice")
    bob = create_address("bob")

    direct_vm.sender = alice
    # alice.as_hex now works
```

## Cheatcodes

### Changing Sender

```python
def test_sender(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/Token.py")

    from gltest.direct import create_address
    alice = create_address("alice")
    bob = create_address("bob")

    # Set sender for subsequent calls
    direct_vm.sender = alice
    contract.mint(1000)

    direct_vm.sender = bob
    contract.mint(500)
```

### Pranking

Temporarily change sender for a single operation:

```python
def test_prank(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/Token.py")

    from gltest.direct import create_address
    alice = create_address("alice")
    bob = create_address("bob")

    direct_vm.sender = alice

    # Temporarily act as bob
    with direct_vm.prank(bob):
        contract.approve(alice, 100)  # Called as bob

    # Back to alice
    contract.transfer_from(bob, alice, 50)  # Called as alice
```

For persistent pranking:

```python
direct_vm.startPrank(bob)
contract.method1()  # As bob
contract.method2()  # As bob
direct_vm.stopPrank()
```

### Snapshots

Save and restore state:

```python
def test_snapshots(direct_vm, direct_deploy):
    token = direct_deploy("contracts/Token.py")

    from gltest.direct import create_address
    alice = create_address("alice")

    direct_vm.sender = alice
    token.mint(1000)

    # Take snapshot
    snap_id = direct_vm.snapshot()

    # Modify state
    token.burn(500)
    assert token.balance_of(alice) == 500

    # Revert to snapshot
    direct_vm.revert(snap_id)
    assert token.balance_of(alice) == 1000
```

### Expecting Reverts

Test that operations fail correctly:

```python
def test_reverts(direct_vm, direct_deploy):
    token = direct_deploy("contracts/Token.py")

    from gltest.direct import create_address
    alice = create_address("alice")
    bob = create_address("bob")

    direct_vm.sender = alice
    token.mint(100)

    # Expect any revert
    with direct_vm.expect_revert():
        token.transfer(bob, 1000)  # Insufficient balance

    # Expect specific message
    with direct_vm.expect_revert("Insufficient balance"):
        token.transfer(bob, 1000)
```

### Setting Balances

```python
def test_balances(direct_vm):
    from gltest.direct import create_address
    alice = create_address("alice")

    direct_vm.deal(alice, 1000000)  # Set native balance
```

### Time Manipulation

```python
def test_time(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/TimeLock.py")

    # Set block timestamp (ISO format)
    direct_vm.warp("2024-12-31T23:59:59Z")

    contract.check_deadline()
```

## Mocking Nondet Operations

Direct mode requires mocking `gl.nondet` operations (web requests, LLM calls).

### Web Mocks

```python
def test_web_mock(direct_vm, direct_deploy):
    # Register mock before contract calls
    direct_vm.mock_web(
        r"api\.coingecko\.com/.*bitcoin",  # URL pattern (regex)
        {
            "status": 200,
            "body": '{"price": 50000}',
            "method": "GET"
        }
    )

    oracle = direct_deploy("contracts/PriceOracle.py")
    price = oracle.get_btc_price()
    assert price == 50000
```

### LLM Mocks

```python
def test_llm_mock(direct_vm, direct_deploy):
    # Register mock before contract calls
    direct_vm.mock_llm(
        r"analyze.*sentiment",  # Prompt pattern (regex)
        "positive"              # Response
    )

    analyzer = direct_deploy("contracts/SentimentAnalyzer.py")
    result = analyzer.analyze("analyze the sentiment of: I love this!")
    assert result == "positive"
```

### Clearing Mocks

```python
direct_vm.clear_mocks()  # Remove all registered mocks
```

## SDK Version Handling

Direct mode automatically downloads and caches the correct GenLayer SDK version based on contract headers:

```python
# Contract with version header
# { "Depends": "py-genlayer:abc123..." }

from genlayer import *

class MyContract(gl.Contract):
    ...
```

SDKs are cached in `~/.cache/gltest-direct/`.

## Limitations

Direct mode does **not** support:

- Multi-validator consensus
- Actual RPC/network calls
- Gas metering
- Cross-contract calls via address (same-file imports work)
- Persistence between test runs

For these features, use Simulator mode.

## Example: Complete Test Suite

```python
"""tests/test_token.py"""

import pytest
from gltest.direct import create_address


class TestToken:
    """Token contract tests using direct mode."""

    def test_mint(self, direct_vm, direct_deploy):
        token = direct_deploy("contracts/Token.py", "Test", "TST")

        alice = create_address("alice")
        direct_vm.sender = alice

        token.mint(1000)
        assert token.balance_of(alice) == 1000

    def test_transfer(self, direct_vm, direct_deploy):
        token = direct_deploy("contracts/Token.py", "Test", "TST")

        alice = create_address("alice")
        bob = create_address("bob")

        direct_vm.sender = alice
        token.mint(1000)
        token.transfer(bob, 100)

        assert token.balance_of(alice) == 900
        assert token.balance_of(bob) == 100

    def test_transfer_insufficient_balance(self, direct_vm, direct_deploy):
        token = direct_deploy("contracts/Token.py", "Test", "TST")

        alice = create_address("alice")
        bob = create_address("bob")

        direct_vm.sender = alice
        token.mint(100)

        with direct_vm.expect_revert("Insufficient balance"):
            token.transfer(bob, 1000)

    def test_snapshot_revert(self, direct_vm, direct_deploy):
        token = direct_deploy("contracts/Token.py", "Test", "TST")

        alice = create_address("alice")
        direct_vm.sender = alice
        token.mint(1000)

        snap = direct_vm.snapshot()
        token.burn(500)
        assert token.balance_of(alice) == 500

        direct_vm.revert(snap)
        assert token.balance_of(alice) == 1000
```

Run:

```bash
pytest tests/test_token.py -v

# Output:
# tests/test_token.py::TestToken::test_mint PASSED
# tests/test_token.py::TestToken::test_transfer PASSED
# tests/test_token.py::TestToken::test_transfer_insufficient_balance PASSED
# tests/test_token.py::TestToken::test_snapshot_revert PASSED
#
# ======================== 4 passed in 0.15s ========================
```

## Troubleshooting

### "No module named 'genlayer'"

The SDK couldn't be loaded. Check:
1. Contract has valid version header or SDK is cached
2. `~/.cache/gltest-direct/` has downloaded SDKs

### "DecodingError: unexpected end of memory"

Message context wasn't injected properly. This usually means:
1. Contract was imported before VM activation
2. Module caching issue between tests

Solution: Ensure `direct_vm.activate()` is called (fixtures do this automatically).

### Address has no `.as_hex` attribute

Addresses created before genlayer loads are `bytes`. Create addresses after deploying:

```python
def test_example(direct_vm, direct_deploy):
    contract = direct_deploy(...)  # Loads genlayer

    # Now create_address returns Address objects
    from gltest.direct import create_address
    alice = create_address("alice")
    alice.as_hex  # Works!
```

### Mock not found for URL/prompt

Direct mode requires explicit mocks for all nondet operations:

```python
direct_vm.mock_web(r".*example\.com.*", {"status": 200, "body": "{}"})
direct_vm.mock_llm(r".*", "default response")  # Catch-all
```
