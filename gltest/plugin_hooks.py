from gltest.plugin_config import (
    set_contracts_dir,
    set_default_wait_interval,
    set_default_wait_retries,
    set_rpc_url,
)
from pathlib import Path
from genlayer_py.chains.localnet import SIMULATOR_JSON_RPC_URL


def pytest_addoption(parser):
    group = parser.getgroup("gltest")
    group.addoption(
        "--contracts-dir",
        action="store",
        default="contracts",
        help="Directory containing contract files",
    )

    group.addoption(
        "--default-wait-interval",
        action="store",
        default=10000,
        help="Default wait interval for waiting transaction receipts",
    )

    group.addoption(
        "--default-wait-retries",
        action="store",
        default=15,
        help="Default wait retries for waiting transaction receipts",
    )

    group.addoption(
        "--rpc-url",
        action="store",
        default=SIMULATOR_JSON_RPC_URL,
        help="RPC URL for the genlayer network",
    )


def pytest_configure(config):
    contracts_dir = config.getoption("--contracts-dir")
    default_wait_interval = config.getoption("--default-wait-interval")
    default_wait_retries = config.getoption("--default-wait-retries")
    rpc_url = config.getoption("--rpc-url")

    set_contracts_dir(Path(contracts_dir))
    set_default_wait_interval(int(default_wait_interval))
    set_default_wait_retries(int(default_wait_retries))
    set_rpc_url(str(rpc_url))
