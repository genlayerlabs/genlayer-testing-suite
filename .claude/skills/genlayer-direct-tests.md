# Write Direct Mode Tests

Write fast, comprehensive tests for GenLayer intelligent contracts using direct mode execution.

## When to Use

- Writing unit tests for intelligent contracts
- Testing contract logic without simulator overhead
- Testing nondet operations (web calls, LLM) with mocks
- Rapid iteration during development

## Direct Mode Overview

Direct mode runs contract Python code in-memory without the GenLayer simulator. Tests execute in ~30ms instead of minutes.

**Two approaches:**

| Approach | When to Use | Speed |
|----------|-------------|-------|
| DEV MODE | Contract has dev bypass (`bridge_sender=zero_address`) | ~30ms |
| Production + Mocks | Test actual nondet logic with `mock_web()` | ~50ms |

## Fixtures

```python
from gltest.direct import create_address

# Core fixtures (from pytest_plugin)
def test_example(direct_vm, direct_deploy, direct_alice, direct_bob):
    # direct_vm: VMContext with cheatcodes
    # direct_deploy: Deploy contracts
    # direct_alice/bob/charlie: Test addresses
    pass
```

## DEV MODE Tests

For contracts with DEV MODE support (skip external verification when `bridge_sender=zero_address`):

```python
@pytest.fixture
def dev_contract(direct_vm, direct_deploy, contract_path, direct_alice):
    """Deploy contract in DEV MODE."""
    direct_vm.sender = direct_alice
    return direct_deploy(
        str(contract_path),
        bridge_sender="0x0000000000000000000000000000000000000000",  # DEV MODE
        # ... other args
    )

def test_create_item(dev_contract, direct_vm, direct_alice):
    """Test basic creation flow."""
    direct_vm.sender = direct_alice
    dev_contract.dev_register_identity("alice_github")  # DEV MODE method

    result = dev_contract.create_item("item_1", 100)
    assert result == "item_1"

    item = dev_contract.get_item("item_1")
    assert item["status"] == "active"
```

## Production Mode with Mocks

For testing actual nondet operations (GitHub API, RPC calls, LLM):

```python
@pytest.fixture
def prod_contract(direct_vm, direct_deploy, contract_path, direct_alice):
    """Deploy contract in production mode (requires mocks)."""
    direct_vm.sender = direct_alice
    return direct_deploy(
        str(contract_path),
        bridge_sender="0x1111111111111111111111111111111111111111",  # Non-zero
        github_api_base="https://api.github.com",
        # ... other args
    )

def test_github_verification(prod_contract, direct_vm, direct_alice):
    """Test GitHub verification with mocked API."""
    direct_vm.sender = direct_alice

    # Start verification to get challenge
    challenge = prod_contract.start_identity_verification()

    # Mock GitHub API response
    direct_vm.mock_web(
        r"api\.github\.com/users/testuser",
        {
            "response": {
                "status": 200,
                "headers": {},
                "body": json.dumps({
                    "id": 12345,
                    "login": "testuser",
                    "bio": challenge  # Challenge in bio
                }).encode()
            },
            "method": "GET"
        }
    )

    # Verify identity (makes real nondet web call, intercepted by mock)
    prod_contract.verify_identity("testuser")

    # Assert result
    identity = prod_contract.get_identity(direct_alice)
    assert identity["github_username"] == "testuser"
```

## Mock Helpers Pattern

Create reusable mock helpers in conftest.py:

```python
import json

def mock_github_user(direct_vm, username: str, user_id: int, bio: str = ""):
    """Mock GitHub user API response."""
    direct_vm.mock_web(
        rf"api\.github\.com/users/{username}",
        {
            "response": {
                "status": 200,
                "headers": {},
                "body": json.dumps({
                    "id": user_id,
                    "login": username,
                    "bio": bio
                }).encode()
            },
            "method": "GET"
        }
    )

def mock_rpc_call(direct_vm, rpc_url_pattern: str, result_hex: str):
    """Mock JSON-RPC response."""
    direct_vm.mock_web(
        rpc_url_pattern,
        {
            "response": {
                "status": 200,
                "headers": {},
                "body": json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": result_hex
                }).encode()
            },
            "method": "POST"
        }
    )

def mock_github_pr(direct_vm, repo: str, pr_number: int, user_id: int, merged: bool = False):
    """Mock GitHub PR API response."""
    repo_escaped = repo.replace("/", r"\/")
    direct_vm.mock_web(
        rf"api\.github\.com/repos/{repo_escaped}/pulls/{pr_number}",
        {
            "response": {
                "status": 200,
                "headers": {},
                "body": json.dumps({
                    "id": pr_number * 1000,
                    "number": pr_number,
                    "state": "closed" if merged else "open",
                    "merged": merged,
                    "user": {"id": user_id}
                }).encode()
            },
            "method": "GET"
        }
    )
```

## VMContext Cheatcodes

```python
# Set sender for next call
direct_vm.sender = direct_alice

# Set native value
direct_vm.value = 1000000000000000000  # 1 ETH in wei

# Expect revert
with direct_vm.expect_revert("Error message substring"):
    contract.method_that_reverts()

# Prank (temporary sender change)
with direct_vm.prank(direct_bob):
    contract.method()  # Called as bob

# Snapshot and revert state
snap_id = direct_vm.snapshot()
contract.modify_state()
direct_vm.revert(snap_id)  # State restored

# Set balance
direct_vm.deal(direct_alice, 1000000000000000000)

# Time control (sets gl.message.datetime)
direct_vm.warp("2024-06-01T12:00:00Z")
```

## Mock Response Format

The mock_web response format must match what the SDK expects:

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

When contract calls `gl.nondet.web.get(url)` or similar:

1. Contract calls `gl.eq_principle.strict_eq(fetch_fn)`
2. This triggers `RunNondet` gl_call with cloudpickle-serialized function
3. Direct mode executes the leader function directly
4. Inside leader, `gl.nondet.web.get()` triggers `GetWebsite` gl_call
5. `mock_web()` intercepts by URL pattern matching
6. Mock response returned to contract

This means mocks work for ALL nondet operations including those inside `gl.eq_principle.strict_eq()`.

## Test Organization

```
tests/
├── direct/
│   ├── conftest.py              # Fixtures + mock helpers
│   ├── test_<feature>.py        # DEV MODE tests
│   └── test_<feature>_mocks.py  # Production tests with mocks
└── intelligent_contracts/
    └── unit/
        └── test_smoke.py        # Simulator smoke test (1-2 tests)
```

## Coverage Strategy

| What to Test | Where | Why |
|--------------|-------|-----|
| State transitions | DEV MODE | Fast, no mocks needed |
| Validation logic | DEV MODE | Fast, deterministic |
| Access control | DEV MODE | Fast, test all roles |
| External API parsing | Production + mocks | Test actual parsing |
| Error handling | Both | Cover all paths |
| Happy path E2E | Simulator smoke | Validate deployment |

## Common Patterns

### Testing Validation Errors
```python
def test_invalid_input(dev_contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice

    with direct_vm.expect_revert("Invalid amount"):
        dev_contract.create_item("item", amount=0)
```

### Testing Access Control
```python
def test_only_owner(dev_contract, direct_vm, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    dev_contract.create_item("item_1")

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only owner"):
        dev_contract.delete_item("item_1")
```

### Testing State Changes
```python
def test_state_transition(dev_contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    dev_contract.create_item("item_1")

    assert dev_contract.get_item("item_1")["status"] == "pending"

    dev_contract.approve_item("item_1")

    assert dev_contract.get_item("item_1")["status"] == "approved"
```

### Testing with Multiple Accounts
```python
def test_multi_party(dev_contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    # Alice creates
    direct_vm.sender = direct_alice
    dev_contract.create_item("item_1")

    # Bob participates
    direct_vm.sender = direct_bob
    dev_contract.join_item("item_1")

    # Charlie verifies
    direct_vm.sender = direct_charlie
    dev_contract.verify_item("item_1")
```

## Debugging

Enable traces in VMContext:
```python
direct_vm._trace_enabled = True
# ... run test
print(direct_vm._traces)
```

Check mock matching:
```python
# Mocks are stored as (pattern, response) tuples
print(direct_vm._web_mocks)
```
