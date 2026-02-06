# glsim — Lightweight GenLayer Simulator

A single-process Python server that speaks the same JSON-RPC protocol as GenLayer Studio localnet. Drop-in replacement for local development — no Docker, no WASM, starts in ~1 second.

## Quick Start

```bash
# Install with sim extras
pip install genlayer-test[sim]

# Start the server
glsim

# Or with options
glsim --port 4000 --verbose
```

The server runs at `http://127.0.0.1:4000/api` with health check at `/health`.

## Using with Your App

### 1. Configure your `gltest.config.yaml`

Point your localnet URL to glsim:

```yaml
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    leader_only: false

paths:
  contracts: "intelligent-contracts"
```

### 2. Start glsim

```bash
glsim --port 4000
```

### 3. Run your app or tests

glsim implements the same RPCs that the GenLayer SDK (`genlayer-py`) expects. Your app's `GenLayerClient` talks to glsim exactly as it would to Studio.

```python
from genlayer_py.client import GenLayerClient

# Works identically against glsim or Studio
client = GenLayerClient(chain=localnet)
```

## Supported RPCs

### SDK-compatible (drop-in for GenLayer Studio)

| RPC Method | Description |
|---|---|
| `eth_sendRawTransaction` | Deploy or call contracts via signed transactions |
| `eth_getTransactionReceipt` | Ethereum-style receipt with NewTransaction event log |
| `eth_getTransactionByHash` | Full transaction data with consensus_data, leader_receipt |
| `gen_call` | Read-only contract calls |
| `gen_getContractSchema` | Schema for deployed contract |
| `gen_getContractSchemaForCode` | Schema from source code |
| `eth_chainId` | Returns `0xf21f` (localnet chain ID) |
| `eth_blockNumber` | Current block number |
| `eth_getBalance` | Account balance |
| `eth_getTransactionCount` | Account nonce |
| `eth_gasPrice` / `eth_estimateGas` | Gas stubs (returns 0) |

### Simulator-specific

| RPC Method | Description |
|---|---|
| `sim_deploy` | Deploy contract from source code (non-SDK path) |
| `sim_call` | Call contract method (non-SDK path) |
| `sim_read` | Read-only contract call (non-SDK path) |
| `sim_fundAccount` | Fund an account with tokens |
| `sim_getBalance` | Get account balance |
| `sim_getContractSchema` | Get schema for deployed contract |
| `sim_createSnapshot` | Snapshot full state (for test fixtures) |
| `sim_restoreSnapshot` | Restore to a previous snapshot |

## Features

### Transaction Mocks via sim_config

Pass web and LLM mocks through `sim_config` in `eth_sendRawTransaction`:

```python
transaction_context = {
    "validators": [{
        "plugin_config": {
            # Mock web responses
            "mock_web_response": {
                "nondet_web_request": {
                    "https://api.example.com/data": {
                        "method": "GET",
                        "status": 200,
                        "body": '{"result": "mocked"}'
                    }
                }
            },
            # Mock LLM responses
            "mock_response": {
                "response": {
                    "some_prompt_key": "mocked LLM response"
                }
            }
        }
    }]
}

result = contract.my_method(args=[...]).transact(
    transaction_context=transaction_context
)
```

### ZIP Contract Packages

Multi-file contracts packaged as ZIP archives work out of the box. The standard layout is:

```
contract/
  __init__.py      # Entry point
  OtherModule.py   # Additional files
runner.json        # Dependencies
```

Contracts that read sibling files via `open("/contract/OtherModule.py")` work — glsim patches `builtins.open` to redirect `/contract/*` paths to the extracted package directory.

### Cross-Contract Calls

Contracts using `gl.deploy_contract()`, `gl.contract_at().view()`, and `gl.contract_at().emit()` work. glsim handles:
- **DeployContract** — deploys child contract with isolated storage
- **CallContract** — calls method on deployed contract, returns result
- **PostMessage** — fire-and-forget call (no return value)

### GenVM Library Stubs

Contracts that depend on GenVM-only libraries (e.g. `genlayer_embeddings`) work via built-in stubs:
- `VecDB` — in-memory vector store with insert/knn
- `SentenceTransformer` — returns deterministic pseudo-embeddings
- `EuclideanDistanceSquared` — distance metric stub

The stubs are automatically installed when glsim starts. The real GenVM SDK libraries (`py-genlayer`, `py-lib-genlayer-std`) are downloaded from GitHub releases on first use and cached at `~/.cache/gltest-direct/`.

### Snapshots

```python
# Save state
snapshot_id = client.provider.make_request("sim_createSnapshot", [])

# ... do some work ...

# Restore to saved state
client.provider.make_request("sim_restoreSnapshot", [snapshot_id])
```

Used by `load_fixture()` for test fixture caching.

## CLI Options

```
glsim [OPTIONS]

Options:
  --port PORT          RPC server port (default: 4000)
  --host HOST          Bind address (default: 127.0.0.1)
  --validators N       Number of validators (default: 1, leader-only)
  --llm-provider P     Default LLM provider, e.g. openai:gpt-4o
  --no-browser         Disable Playwright browser for web requests
  --verbose, -v        Verbose logging
```

## Prerequisites

For contracts that use numpy (e.g. Rally's CampaignIC):

```bash
pip install numpy
```

The GenVM SDK artifacts are auto-downloaded on first contract deployment (~50MB, cached).

## Architecture

```
Client (GenLayerClient / web3.py)
  ↓ JSON-RPC over HTTP
glsim server (FastAPI + uvicorn)
  ↓
SimEngine (wraps gltest.direct)
  ├── VMContext (cheatcodes, mocks)
  ├── InmemManager (per-contract storage)
  ├── Cross-contract hooks
  └── GenVM stubs
  ↓
StateStore (accounts, transactions, contracts)
```

Each contract gets isolated storage. The VM context persists across requests, enabling stateful interactions across multiple RPC calls.

## Differences from Studio

| | glsim | Studio |
|---|---|---|
| Startup | ~1 second | Minutes (Docker) |
| Execution | Native Python | WASM in GenVM |
| Consensus | Simulated (instant) | Full protocol |
| Web requests | httpx / Playwright | GenVM sandbox |
| LLM requests | Direct API calls | GenVM sandbox |
| State | In-memory (lost on restart) | Persistent |
| Multi-validator | Simulated votes | Real consensus |

## Limitations

- **In-memory state**: All state is lost when glsim restarts. Use snapshots within a session.
- **No real consensus**: All validators auto-agree. Validator functions run but consensus is not enforced.
- **GenVM-only libraries**: Stubs provide basic functionality but not full fidelity (e.g., VecDB uses simple L2 distance, not cover trees).
- **No gas metering**: Gas-related RPCs return 0.
