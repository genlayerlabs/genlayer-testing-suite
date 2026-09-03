import pytest
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
from gltest_cli.config.constants import (
    DEFAULT_LEADER_ONLY,
    CHAINS,
)
from gltest.fees import get_fee_profile_collector, reset_fee_profile_collector


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
        default=None,
        help="Default interval (ms) between transaction receipt checks",
    )

    group.addoption(
        "--default-wait-retries",
        action="store",
        default=None,
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
        "--leader-only",
        action="store_true",
        default=DEFAULT_LEADER_ONLY,
        help="Run contracts in leader-only mode",
    )

    group.addoption(
        "--chain-type",
        action="store",
        default=None,
        help=f"Chain type (possible values: {', '.join(CHAINS)})",
    )
    group.addoption(
        "--fee-profile",
        action="store",
        default=None,
        help="Path to write a JSON fee profile for observed deploys and writes",
    )
    group.addoption(
        "--fee-profile-headroom",
        action="store",
        default=None,
        help="Multiplier applied to observed fee maxima in --fee-profile output",
    )


def pytest_configure(config):
    try:
        general_config = get_general_config()

        network_name = config.getoption("--network")

        if not user_config_exists():
            logger.warning(
                "File `gltest.config.yaml` not found in the current directory, using default config, create a `gltest.config.yaml` file to manage multiple networks"
            )
            user_config = get_default_user_config()

            # Special handling for remote testnets - check if accounts are configured
            if network_name in ("testnet_asimov", "testnet_bradbury"):
                logger.error(
                    f"For {network_name}, you need to configure accounts in gltest.config.yaml, see https://docs.genlayer.com/api-references/genlayer-test"
                )
                pytest.exit("gltest configuration error")
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
        leader_only = config.getoption("--leader-only")
        chain_type = config.getoption("--chain-type")
        fee_profile = config.getoption("--fee-profile")
        fee_profile_headroom = config.getoption("--fee-profile-headroom")

        plugin_config = PluginConfig()
        plugin_config.contracts_dir = (
            Path(contracts_dir) if contracts_dir is not None else None
        )
        plugin_config.artifacts_dir = (
            Path(artifacts_dir) if artifacts_dir is not None else None
        )
        plugin_config.default_wait_interval = (
            int(default_wait_interval) if default_wait_interval is not None else None
        )
        plugin_config.default_wait_retries = (
            int(default_wait_retries) if default_wait_retries is not None else None
        )
        plugin_config.rpc_url = rpc_url
        plugin_config.network_name = network
        plugin_config.leader_only = leader_only
        plugin_config.chain_type = chain_type
        plugin_config.fee_profile_path = (
            Path(fee_profile) if fee_profile is not None else None
        )
        if fee_profile_headroom is not None:
            parsed_headroom = float(fee_profile_headroom)
            if parsed_headroom <= 0:
                raise ValueError("--fee-profile-headroom must be greater than 0")
            plugin_config.fee_profile_headroom = parsed_headroom

        general_config.plugin_config = plugin_config
    except Exception as e:
        logger.error(f"Gltest configure error: {e}")
        pytest.exit("gltest configuration error")


def pytest_sessionstart(session):
    try:
        reset_fee_profile_collector()
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
        # Show available networks including preconfigured ones
        all_networks = general_config.get_networks_keys()
        logger.info(f"  Available networks: {all_networks}")
        logger.info(f"  Selected chain type: {general_config.get_chain_type()}")
        logger.info(f"  Available chains: {', '.join(CHAINS)}")
        logger.info(f"  Contracts directory: {general_config.get_contracts_dir()}")
        logger.info(f"  Artifacts directory: {general_config.get_artifacts_dir()}")
        logger.info(f"  Environment: {general_config.user_config.environment}")
        logger.info(
            f"  Default wait interval: {general_config.get_default_wait_interval()} ms"
        )
        logger.info(
            f"  Default wait retries: {general_config.get_default_wait_retries()}"
        )
        if general_config.get_fee_profile_path() is not None:
            logger.info(
                f"  Fee profile output: {general_config.get_fee_profile_path()}"
            )

        if (
            general_config.get_leader_only()
            and not general_config.check_studio_based_rpc()
        ):
            logger.warning(
                "Leader only mode: True (enabled on non-studio network - will have no effect)"
            )
        else:
            logger.info(f"  Leader only mode: {general_config.get_leader_only()}")
    except Exception as e:
        logger.error(f"Gltest session start error: {e}")
        pytest.exit("gltest session start error")


def pytest_sessionfinish(session, exitstatus):
    try:
        general_config = get_general_config()
        fee_profile_path = general_config.get_fee_profile_path()
        if fee_profile_path is None:
            return

        collector = get_fee_profile_collector()
        profile = collector.write(
            path=fee_profile_path,
            network=general_config.get_network_name(),
            headroom=general_config.get_fee_profile_headroom(),
            chain_id=general_config.get_chain().id,
        )
        logger.info(f"Wrote fee profile to {fee_profile_path}")
        if not collector.has_observations():
            logger.warning(
                "Fee profile is empty; this backend may not expose consumed fee data on receipts yet"
            )
        elif "deploy" not in profile and not profile["methods"]:
            logger.warning("Fee profile contains no deploy or method observations")
    except Exception as e:
        logger.error(f"Failed to write fee profile: {e}")


def pytest_runtest_setup(item):
    _pytest_context.current_item = item


def pytest_runtest_teardown(item):
    try:
        del _pytest_context.current_item
    except AttributeError:
        pass


pytest_plugins = ["gltest.fixtures"]
