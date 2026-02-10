# Write Direct Mode Tests

Write fast tests for GenLayer intelligent contracts using direct mode execution.

## When to Use

- Writing unit tests for intelligent contracts
- Testing contract logic without simulator overhead
- Testing nondet operations (web calls, LLM) with mocks
- Rapid iteration during development

## Direct Mode Overview

Direct mode runs contract Python code in-memory without the GenLayer simulator. Tests execute in ~30ms instead of minutes.

## Fixtures

```python
from gltest.direct import create_address

# Core fixtures (from pytest_plugin)
def test_example(direct_vm, direct_deploy, direct_alice, direct_bob):
    # direct_vm: VMContext with cheatcodes
    # direct_deploy: Deploy contracts from file path
    # direct_alice/bob/charlie: Test addresses
    # direct_owner: Default sender address
    # direct_accounts: List of 10 test addresses
    pass
```

## Basic Contract Test

Using the Storage contract (`tests/examples/contracts/storage.py`):

```python
from pathlib import Path

CONTRACTS = Path(__file__).parent.parent / "examples" / "contracts"

def test_storage(direct_vm, direct_deploy):
    storage = direct_deploy(str(CONTRACTS / "storage.py"), "initial")

    assert storage.get_storage() == "initial"

    storage.update_storage("updated")
    assert storage.get_storage() == "updated"
```

## Testing with Sender / Access Control

Using UserStorage (per-user data via `gl.message.sender_address`):

```python
def test_per_user_storage(direct_vm, direct_deploy, direct_alice, direct_bob):
    user_storage = direct_deploy(str(CONTRACTS / "user_storage.py"))

    direct_vm.sender = direct_alice
    user_storage.update_storage("alice data")

    direct_vm.sender = direct_bob
    user_storage.update_storage("bob data")

    assert user_storage.get_account_storage(direct_alice.as_hex) == "alice data"
    assert user_storage.get_account_storage(direct_bob.as_hex) == "bob data"
```

## Mocking Web Requests

For contracts using `gl.nondet.web.get()` (e.g. XUsernameStorage):

```python
import json

def test_web_mock(direct_vm, direct_deploy):
    contract = direct_deploy(str(CONTRACTS / "x_username_storage.py"))

    # Mock the X API endpoint (pattern is a regex)
    direct_vm.mock_web(
        r"domain\.com/api/twitter/users/by/username/testuser",
        {
            "response": {
                "status": 200,
                "headers": {},
                "body": json.dumps({"username": "testuser"}).encode()
            },
            "method": "GET"
        }
    )

    contract.update_username("testuser")
    assert contract.get_username() == "testuser"
```

### Flat mock format (auto-adapted)

```python
direct_vm.mock_web(
    r"api\.example\.com/price",
    {"status": 200, "body": '{"price": 42000}'}
)
```

## Mocking LLM Prompts

For contracts using `gl.nondet.exec_prompt()` (e.g. WizardOfCoin):

```python
import json

def test_llm_mock(direct_vm, direct_deploy):
    contract = direct_deploy(str(CONTRACTS / "wizard_of_coin.py"), True)

    # Mock LLM response (pattern matched against prompt text)
    direct_vm.mock_llm(
        r"wizard.*coin",
        json.dumps({"reasoning": "No coin for you!", "give_coin": False})
    )

    contract.ask_for_coin("Give me the coin!")
    assert contract.get_have_coin() == True  # wizard refused
```

## VMContext Cheatcodes

```python
# Set sender for next call
direct_vm.sender = direct_alice

# Set native value (wei)
direct_vm.value = 1000000000000000000

# Expect revert (catches ContractRollback + generic exceptions)
with direct_vm.expect_revert("Error substring"):
    contract.method_that_reverts()

# Prank (temporary sender change)
with direct_vm.prank(direct_bob):
    contract.method()  # called as bob

# Snapshot and revert state
snap_id = direct_vm.snapshot()
contract.modify_state()
direct_vm.revert(snap_id)  # state restored

# Set balance
direct_vm.deal(direct_alice, 1000000000000000000)

# Time control (sets gl.message.datetime)
direct_vm.warp("2024-06-01T12:00:00Z")

# Clear all mocks
direct_vm.clear_mocks()
```

## Testing Validators (run_nondet)

After a nondet call, test that the validator function behaves correctly:

```python
def test_validator(direct_vm, direct_deploy):
    contract = direct_deploy(str(CONTRACTS / "x_username_storage.py"))

    direct_vm.mock_web(r"domain\.com/api/twitter/.*", {
        "response": {"status": 200, "headers": {},
                     "body": json.dumps({"username": "alice"}).encode()},
        "method": "GET"
    })

    contract.update_username("alice")

    # Run the captured validator with the leader's result
    result = direct_vm.run_validator()  # defaults to last captured nondet
    assert result == True  # validator agrees with leader
```

## Mock Response Format

The full `mock_web` format must match what the SDK expects:

```python
{
    "response": {
        "status": 200,           # HTTP status code
        "headers": {},           # HTTP headers (usually empty)
        "body": b"..."           # Response body as bytes
    },
    "method": "GET"              # or "POST"
}
```

For JSON APIs, encode the body:
```python
"body": json.dumps({"key": "value"}).encode()
```

## How Nondet Mocking Works

When a contract calls `gl.nondet.web.get(url)` or `gl.nondet.exec_prompt(prompt)`:

1. Contract calls `gl.eq_principle.strict_eq(fn)` or `gl.eq_principle.prompt_comparative(fn, ...)`
2. This triggers `RunNondet` gl_call with cloudpickle-serialized function
3. Direct mode executes the leader function directly (skips pickling)
4. Inside leader, `gl.nondet.web.get()` triggers `GetWebsite` gl_call
5. `mock_web()` intercepts by URL regex matching
6. Mock response returned to contract

Mocks work for ALL nondet operations including those inside equivalence principles.

## Common Patterns

### Testing Validation Errors
```python
def test_revert(direct_vm, direct_deploy):
    contract = direct_deploy(str(CONTRACTS / "storage.py"), "init")

    with direct_vm.expect_revert():
        # Trigger any contract error
        contract.some_method_that_raises()
```

### Snapshot/Revert for Isolation
```python
def test_isolated_changes(direct_vm, direct_deploy):
    storage = direct_deploy(str(CONTRACTS / "storage.py"), "before")

    snap_id = direct_vm.snapshot()
    storage.update_storage("after")
    assert storage.get_storage() == "after"

    direct_vm.revert(snap_id)
    assert storage.get_storage() == "before"
```

### Multiple Accounts
```python
def test_multi_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    user_storage = direct_deploy(str(CONTRACTS / "user_storage.py"))

    direct_vm.sender = direct_alice
    user_storage.update_storage("alice")

    with direct_vm.prank(direct_bob):
        user_storage.update_storage("bob")
```

## Debugging

```python
# Enable traces
direct_vm._trace_enabled = True
# ... run test
print(direct_vm._traces)

# Inspect registered mocks
print(direct_vm._web_mocks)  # [(pattern, response), ...]
print(direct_vm._llm_mocks)  # [(pattern, response), ...]
```
