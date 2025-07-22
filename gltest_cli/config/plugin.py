from pathlib import Path
import shutil
from gltest_cli.logging import logger
from gltest_cli.config.user import (
    user_config_exists,
    load_user_config,
    get_default_user_config,
)
from gltest_cli.config.general import (
    get_general_config,
)
from gltest_cli.config.types import PluginConfig
from gltest_cli.config.pytest_context import _pytest_context


def pytest_addoption(parser):
    group = parser.getgroup("gltest")
    group.addoption(
        "--contracts-dir",
        action="store",
        default=None,
        help="Path to directory containing contract files",
    )

    group.addoption(
        "--artifacts-dir",
        action="store",
        default=None,
        help="Path to directory for storing contract artifacts",
    )

    group.addoption(
        "--default-wait-interval",
        action="store",
        default=3000,
        help="Default interval (ms) between transaction receipt checks",
    )

    group.addoption(
        "--default-wait-retries",
        action="store",
        default=50,
        help="Default number of retries for transaction receipt checks",
    )

    group.addoption(
        "--rpc-url",
        action="store",
        default=None,
        help="RPC endpoint URL for the GenLayer network",
    )

    group.addoption(
        "--network",
        action="store",
        default=None,
        help="Target network (defaults to 'localnet' if no config file)",
    )

    group.addoption(
        "--test-with-mocks",
        action="store_true",
        default=False,
        help="Test with mocks",
    )

    group.addoption(
        "--leader-only",
        action="store_true",
        default=False,
        help="Run contracts in leader-only mode",
    )


def pytest_configure(config):
    general_config = get_general_config()

    # Handle user config from gltest.config.yaml
    if not user_config_exists():
        logger.warning(
            "File `gltest.config.yaml` not found in the current directory, using default config"
        )
        logger.info("Create a `gltest.config.yaml` file to manage multiple networks")
        user_config = get_default_user_config()
    else:
        logger.info(
            "File `gltest.config.yaml` found in the current directory, using it"
        )
        user_config = load_user_config("gltest.config.yaml")

    general_config.user_config = user_config

    # Handle plugin config from command line
    contracts_dir = config.getoption("--contracts-dir")
    artifacts_dir = config.getoption("--artifacts-dir")
    default_wait_interval = config.getoption("--default-wait-interval")
    default_wait_retries = config.getoption("--default-wait-retries")
    rpc_url = config.getoption("--rpc-url")
    network = config.getoption("--network")
    test_with_mocks = config.getoption("--test-with-mocks")
    leader_only = config.getoption("--leader-only")

    plugin_config = PluginConfig()
    plugin_config.contracts_dir = (
        Path(contracts_dir) if contracts_dir is not None else None
    )
    plugin_config.artifacts_dir = (
        Path(artifacts_dir) if artifacts_dir is not None else None
    )
    plugin_config.default_wait_interval = int(default_wait_interval)
    plugin_config.default_wait_retries = int(default_wait_retries)
    plugin_config.rpc_url = rpc_url
    plugin_config.network_name = network
    plugin_config.test_with_mocks = test_with_mocks
    plugin_config.leader_only = leader_only

    general_config.plugin_config = plugin_config


def pytest_sessionstart(session):
    general_config = get_general_config()

    artifacts_dir = general_config.get_artifacts_dir()
    if artifacts_dir and artifacts_dir.exists():
        logger.info(f"Clearing artifacts directory: {artifacts_dir}")
        try:
            shutil.rmtree(artifacts_dir)
            artifacts_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to clear artifacts directory: {e}")
    elif artifacts_dir:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Using the following configuration:")
    logger.info(f"  RPC URL: {general_config.get_rpc_url()}")
    logger.info(f"  Selected Network: {general_config.get_network_name()}")
    logger.info(
        f"  Available networks: {list(general_config.user_config.networks.keys())}"
    )
    logger.info(f"  Contracts directory: {general_config.get_contracts_dir()}")
    logger.info(f"  Artifacts directory: {general_config.get_artifacts_dir()}")
    logger.info(f"  Environment: {general_config.user_config.environment}")
    logger.info(
        f"  Default wait interval: {general_config.get_default_wait_interval()} ms"
    )
    logger.info(f"  Default wait retries: {general_config.get_default_wait_retries()}")
    logger.info(f"  Test with mocks: {general_config.get_test_with_mocks()}")

    if general_config.get_leader_only() and not general_config.check_studio_based_rpc():
        logger.warning(
            "Leader only mode: True (enabled on non-studio network - will have no effect)"
        )
    else:
        logger.info(f"  Leader only mode: {general_config.get_leader_only()}")


def pytest_runtest_setup(item):
    _pytest_context.current_item = item


def pytest_runtest_teardown(item):
    try:
        del _pytest_context.current_item
    except AttributeError:
        pass


pytest_plugins = ["gltest.fixtures"]
