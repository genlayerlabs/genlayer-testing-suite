#!/usr/bin/env python3
"""Generate multi-page Markdown API reference for the GenLayer Testing Suite."""

import inspect
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def clean_readme(content):
    lines = content.split("\n")
    lines = [l for l in lines if not re.match(r'^\[!\[.*\]\(https://(img\.shields\.io|dcbadge|badge\.fury)', l)]
    content = "\n".join(lines)
    content = re.sub(r'(## )\S*[\U0001F000-\U0001FFFF\u2600-\u27BF\u200d]+\s*', r'\1', content)
    return content


def format_type(annotation):
    if annotation is inspect.Parameter.empty:
        return ""
    name = getattr(annotation, "__name__", None)
    if name:
        return name
    return str(annotation).replace("typing.", "").replace("ForwardRef('", "").replace("')", "")


def generate_method_doc(name, method, prefix=""):
    sig = inspect.signature(method)
    docstring = inspect.getdoc(method) or ""
    params = []
    for pname, param in sig.parameters.items():
        if pname == "self" or pname == "cls":
            continue
        type_str = format_type(param.annotation)
        default = ""
        if param.default is not inspect.Parameter.empty:
            default = f" = {param.default!r}"
        required = param.default is inspect.Parameter.empty
        params.append((pname, type_str, required, default))

    lines = [f"### `{prefix}{name}`\n"]
    lines.append(f"{docstring}\n")

    param_parts = []
    for pname, type_str, required, default in params:
        display = f"{pname}: {type_str}" if type_str else pname
        display += default
        param_parts.append(display)

    if param_parts:
        lines.append(f"```python\n{prefix}{name}({', '.join(param_parts)})\n```\n")

    if params:
        lines.append("**Parameters:**\n")
        lines.append("| Parameter | Type | Required | Default |")
        lines.append("|-----------|------|----------|---------|")
        for pname, type_str, required, default in params:
            req_str = "Yes" if required else "No"
            type_display = f"`{type_str}`" if type_str else ""
            default_display = f"`{default.strip(' = ')}`" if default else ""
            lines.append(f"| `{pname}` | {type_display} | {req_str} | {default_display} |")
        lines.append("")

    ret = format_type(sig.return_annotation)
    if ret:
        lines.append(f"**Returns:** `{ret}`\n")

    lines.append("---\n")
    return "\n".join(lines)


def generate_class_doc(cls, method_names, prefix=""):
    docstring = inspect.getdoc(cls) or ""
    lines = [f"## {cls.__name__}\n", f"{docstring}\n"]
    for name in method_names:
        method = getattr(cls, name, None)
        if method and callable(method):
            lines.append(generate_method_doc(name, method, prefix))
    return "\n".join(lines)


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "api-references")
    os.makedirs(output_dir, exist_ok=True)

    # === index.md (copy README as overview page) ===
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    readme_content = clean_readme(open(readme_path).read())
    with open(os.path.join(output_dir, "index.md"), "w") as f:
        f.write(readme_content)

    # === integration.md ===
    from gltest.contracts.contract_factory import ContractFactory
    from gltest.contracts.contract_functions import ContractFunction

    integration = "# Integration Testing\n\n"
    integration += "Test contracts against a running GenLayer network (localnet, studionet, or testnet).\n\n"

    integration += "## Setup Functions\n\n"
    setup_fns = [
        ("get_contract_factory", "gltest"),
        ("get_default_account", "gltest"),
        ("get_accounts", "gltest"),
        ("create_accounts", "gltest"),
        ("get_gl_client", "gltest"),
        ("get_validator_factory", "gltest"),
    ]
    import gltest
    for name, mod in setup_fns:
        fn = getattr(gltest, name, None)
        if fn:
            integration += generate_method_doc(name, fn)

    integration += generate_class_doc(
        ContractFactory,
        ["deploy", "deploy_contract_tx", "build_contract"],
        "factory.",
    )

    integration += generate_class_doc(
        ContractFunction,
        ["call", "transact", "analyze"],
        "contract.method_name.",
    )

    # Validators
    from gltest.validators import ValidatorFactory, Validator
    integration += generate_class_doc(
        ValidatorFactory,
        ["create_validator", "batch_create_validators", "create_mock_validator", "batch_create_mock_validators"],
        "validator_factory.",
    )
    integration += generate_class_doc(
        Validator,
        ["to_dict", "clone", "batch_clone"],
        "validator.",
    )

    with open(os.path.join(output_dir, "integration.md"), "w") as f:
        f.write(integration)

    # === direct.md ===
    from gltest.direct import VMContext
    from gltest.direct.loader import deploy_contract, load_contract_class, create_address, create_test_addresses

    direct = "# Direct Mode Testing\n\n"
    direct += "Run contracts directly in Python without a network. Provides Foundry-style cheatcodes for fast test execution.\n\n"

    direct += "## Setup Functions\n\n"
    for name, fn in [
        ("deploy_contract", deploy_contract),
        ("load_contract_class", load_contract_class),
        ("create_address", create_address),
        ("create_test_addresses", create_test_addresses),
    ]:
        direct += generate_method_doc(name, fn)

    direct += generate_class_doc(
        VMContext,
        [
            "activate", "warp", "deal", "snapshot", "revert",
            "mock_web", "mock_llm", "clear_mocks",
            "prank", "startPrank", "stopPrank", "expect_revert",
            "run_validator", "clear_validators",
        ],
        "vm.",
    )

    with open(os.path.join(output_dir, "direct.md"), "w") as f:
        f.write(direct)

    # === glsim.md ===
    glsim = """# glsim — Local GenLayer Network

A lightweight single-process GenLayer network that runs contracts via direct mode. Supports real LLM and web calls without Docker or WASM.

## Installation

```bash
pip install genlayer-test[sim]
```

## Usage

```bash
# Start with defaults (port 4000, 5 validators)
glsim

# Custom configuration
glsim --port 8000 --validators 3 --llm-provider openai:gpt-4o

# Deterministic mode (reproducible addresses)
glsim --seed my-test-seed
```

## CLI Options

| Option | Default | Description |
|---|---|---|
| `--port` | 4000 | RPC server port |
| `--host` | 127.0.0.1 | Bind address |
| `--validators` | 5 | Number of validators |
| `--max-rotations` | 3 | Max leader rotations |
| `--chain-id` | 61127 | Network chain ID |
| `--llm-provider` | None | LLM provider:model (e.g., `openai:gpt-4o`) |
| `--no-browser` | false | Use httpx instead of Playwright for web |
| `--seed` | None | Deterministic seed for addresses |
| `-v, --verbose` | false | Verbose logging |

## JSON-RPC Methods

glsim exposes a JSON-RPC 2.0 endpoint at `POST /api` compatible with both GenLayer Studio and standard Ethereum methods:

### GenLayer Methods
- `gen_call` — Call a contract method
- `gen_get_contract_schema` — Get contract schema
- `gen_get_contract_schema_for_code` — Get schema from code
- `gen_get_transaction_status` — Get transaction status

### Simulator Methods
- `sim_deploy` — Deploy a contract
- `sim_call` — Call a contract method
- `sim_read` — Read contract state
- `sim_fund_account` — Fund an account
- `sim_get_balance` — Get account balance
- `sim_create_snapshot` — Create state snapshot
- `sim_restore_snapshot` — Restore snapshot
- `sim_install_mocks` — Install web/LLM mocks
- `sim_get_mocks` — Get current mocks
- `sim_increase_time` — Advance time (Anvil-style)
- `sim_set_time` — Set time to specific datetime

### Ethereum Compatible
- `eth_chainId`, `eth_blockNumber`, `eth_getBalance`
- `eth_getTransactionReceipt`, `eth_getTransactionByHash`
- `eth_estimateGas`, `eth_gasPrice`, `eth_sendRawTransaction`
"""

    with open(os.path.join(output_dir, "glsim.md"), "w") as f:
        f.write(glsim)

    print(f"Generated: {output_dir}/index.md")
    print(f"Generated: {output_dir}/integration.md")
    print(f"Generated: {output_dir}/direct.md")
    print(f"Generated: {output_dir}/glsim.md")


if __name__ == "__main__":
    main()
