import os
import yaml
import re
from dotenv import load_dotenv
from pathlib import Path
from functools import lru_cache
from gltest.accounts import create_accounts
from gltest_cli.config.constants import (
    GLTEST_CONFIG_FILE,
    DEFAULT_NETWORK,
    DEFAULT_RPC_URL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_CONTRACTS_DIR,
    DEFAULT_ARTIFACTS_DIR,
    DEFAULT_NETWORK_ID,
)
from gltest_cli.config.types import UserConfig, NetworkConfigData, PathConfig

VALID_ROOT_KEYS = ["networks", "paths", "environment"]
VALID_NETWORK_KEYS = ["id", "url", "accounts", "from", "leader_only"]
VALID_PATHS_KEYS = ["contracts", "artifacts"]


@lru_cache(maxsize=1)
def get_default_user_config() -> UserConfig:
    accounts = create_accounts(n_accounts=10)
    accounts_private_keys = [account.key.hex() for account in accounts]

    return UserConfig(
        networks={
            DEFAULT_NETWORK: NetworkConfigData(
                id=DEFAULT_NETWORK_ID,
                url=DEFAULT_RPC_URL,
                accounts=accounts_private_keys,
                from_account=accounts_private_keys[0],
                leader_only=False,
            ),
        },
        paths=PathConfig(
            contracts=DEFAULT_CONTRACTS_DIR, artifacts=DEFAULT_ARTIFACTS_DIR
        ),
        environment=DEFAULT_ENVIRONMENT,
        default_network=DEFAULT_NETWORK,
    )


def resolve_env_vars(obj):
    if isinstance(obj, str):
        return re.sub(
            r"\${(\w+)}",
            lambda m: os.getenv(m.group(1), f"<UNSET:{m.group(1)}>"),
            obj,
        )
    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(i) for i in obj]
    return obj


def validate_network_config(network_name: str, network_config: dict):
    if not isinstance(network_config, dict):
        raise ValueError(f"network {network_name} must be a dictionary")

    for key in network_config:
        if key not in VALID_NETWORK_KEYS:
            raise ValueError(
                f"Invalid network key: {key}, valid keys are: {VALID_NETWORK_KEYS}"
            )

    if "id" in network_config and not isinstance(network_config["id"], int):
        raise ValueError(f"network {network_name} id must be an integer")

    if "url" in network_config and not isinstance(network_config["url"], str):
        raise ValueError(f"network {network_name} url must be a string")

    if "accounts" in network_config and not isinstance(
        network_config["accounts"], list
    ):
        raise ValueError(f"network {network_name} accounts must be a list")
    if "accounts" in network_config and not all(
        isinstance(acc, str) for acc in network_config["accounts"]
    ):
        raise ValueError(f"network {network_name} accounts must be strings")

    if "from" in network_config and not isinstance(network_config["from"], str):
        raise ValueError(f"network {network_name} from must be a string")
    if "leader_only" in network_config and not isinstance(
        network_config["leader_only"], bool
    ):
        raise ValueError(f"network {network_name} leader_only must be a boolean")

    # For non-default networks, url and accounts are required
    if network_name != DEFAULT_NETWORK:
        if "id" not in network_config:
            raise ValueError(f"network {network_name} must have an id")
        if "url" not in network_config:
            raise ValueError(f"network {network_name} must have a url")
        if "accounts" not in network_config:
            raise ValueError(f"network {network_name} must have accounts")


def validate_raw_user_config(config: dict):
    # Validate root keys
    if not all(key in VALID_ROOT_KEYS for key in config):
        raise ValueError(
            f"Invalid configuration keys. Valid keys are: {VALID_ROOT_KEYS}"
        )

    # Validate networks
    if "networks" in config:
        networks = config["networks"]
        if not isinstance(networks, dict):
            raise ValueError("networks must be a dictionary")

        default_network = networks.get("default", DEFAULT_NETWORK)
        if default_network != DEFAULT_NETWORK and default_network not in networks:
            raise ValueError(f"default network {default_network} not found in networks")

        for name, network_config in networks.items():
            if name == "default" or (
                name == DEFAULT_NETWORK and network_config is None
            ):
                continue
            validate_network_config(name, network_config)

    # Validate paths
    if "paths" in config:
        if not isinstance(config["paths"], dict):
            raise ValueError("paths must be a dictionary")
        if not all(key in VALID_PATHS_KEYS for key in config["paths"]):
            raise ValueError(f"Invalid path keys. Valid keys are: {VALID_PATHS_KEYS}")

    # Validate environment
    if "environment" in config and not isinstance(config["environment"], str):
        raise ValueError("environment must be a string")


def load_user_config(path: str) -> UserConfig:
    with open(path, "r") as f:
        raw_config = yaml.safe_load(f) or {}

    validate_raw_user_config(raw_config)
    load_dotenv(
        dotenv_path=raw_config.get("environment", DEFAULT_ENVIRONMENT), override=True
    )
    resolved_config = resolve_env_vars(raw_config)
    user_config = transform_raw_to_user_config_with_defaults(resolved_config)
    return user_config


def transform_raw_to_user_config_with_defaults(raw_config: dict) -> UserConfig:
    networks_config, user_default_network = _get_overridden_networks(raw_config)
    return UserConfig(
        networks=networks_config,
        paths=_get_overridden_paths(raw_config),
        environment=_get_overridden_environment(raw_config),
        default_network=user_default_network,
    )


def _get_overridden_networks(raw_config: dict) -> tuple[dict, str]:
    default_config = get_default_user_config()
    if "networks" not in raw_config:
        return default_config.networks, default_config.default_network

    networks = dict(raw_config["networks"])
    user_default_network = networks.pop("default")
    if user_default_network is None and DEFAULT_NETWORK in set(networks.keys()):
        user_default_network = DEFAULT_NETWORK

    if user_default_network is None:
        raise ValueError(
            "'networks.default' is required in config since you don't have 'localnet' network in 'networks'"
        )

    networks_config = {}
    for network_name, network_config in networks.items():
        if network_name == DEFAULT_NETWORK:
            networks_config[network_name] = default_config.networks[DEFAULT_NETWORK]
            if network_config is None:
                continue

            if "url" in network_config:
                networks_config[network_name].url = network_config["url"]
            if "accounts" in network_config:
                networks_config[network_name].accounts = network_config["accounts"]
                networks_config[network_name].from_account = network_config["accounts"][
                    0
                ]
            if "from" in network_config:
                networks_config[network_name].from_account = network_config["from"]
            if "leader_only" in network_config:
                networks_config[network_name].leader_only = network_config[
                    "leader_only"
                ]
            continue

        url = network_config["url"]
        accounts = network_config["accounts"]
        from_account = network_config.get("from", accounts[0])
        network_id = network_config.get("id")
        leader_only = network_config.get("leader_only", False)
        networks_config[network_name] = NetworkConfigData(
            id=network_id,
            url=url,
            accounts=accounts,
            from_account=from_account,
            leader_only=leader_only,
        )
    return networks_config, user_default_network


def _get_overridden_environment(raw_config: dict) -> str:
    default_config = get_default_user_config()
    if "environment" in raw_config:
        return raw_config["environment"]
    return default_config.environment


def _get_overridden_paths(raw_config: dict) -> PathConfig:
    default_config = get_default_user_config()
    if "paths" in raw_config:
        paths_config = raw_config.get("paths", {})
        return PathConfig(
            contracts=Path(paths_config.get("contracts", DEFAULT_CONTRACTS_DIR)),
            artifacts=Path(paths_config.get("artifacts", DEFAULT_ARTIFACTS_DIR)),
        )
    return default_config.paths


def user_config_exists() -> bool:
    return any(
        p.name == GLTEST_CONFIG_FILE for p in Path.cwd().iterdir() if p.is_file()
    )
