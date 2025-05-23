from gltest_cli.config.general import (
    get_general_config,
)
from pathlib import Path
from genlayer_py.chains.localnet import SIMULATOR_JSON_RPC_URL
from gltest_cli.config.types import NetworkConfig, PluginConfig


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

    group.addoption(
        "--network",
        action="store",
        default=NetworkConfig.LOCALNET,
        help="The target network, possible values: localnet, testnet_asimov [default: localnet]",
    )


def pytest_configure(config):
    contracts_dir = config.getoption("--contracts-dir")
    default_wait_interval = config.getoption("--default-wait-interval")
    default_wait_retries = config.getoption("--default-wait-retries")
    rpc_url = config.getoption("--rpc-url")
    network = config.getoption("--network")

    plugin_config = PluginConfig()
    plugin_config.contracts_dir = Path(contracts_dir)
    plugin_config.default_wait_interval = int(default_wait_interval)
    plugin_config.default_wait_retries = int(default_wait_retries)
    plugin_config.rpc_url = str(rpc_url)
    plugin_config.network_name = network

    general_config = get_general_config()
    general_config.plugin_config = plugin_config
