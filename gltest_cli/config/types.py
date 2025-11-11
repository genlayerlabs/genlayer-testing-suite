from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from genlayer_py.chains import localnet, studionet, testnet_asimov
from genlayer_py.types import GenLayerChain
from gltest_cli.config.constants import PRECONFIGURED_NETWORKS
from gltest_cli.config.constants import (
    DEFAULT_WAIT_INTERVAL,
    DEFAULT_WAIT_RETRIES,
    DEFAULT_LEADER_ONLY,
    CHAINS,
)


@dataclass
class PluginConfig:
    contracts_dir: Optional[Path] = None
    artifacts_dir: Optional[Path] = None
    rpc_url: Optional[str] = None
    default_wait_interval: Optional[int] = None
    default_wait_retries: Optional[int] = None
    network_name: Optional[str] = None
    leader_only: bool = False
    chain_type: Optional[str] = None


@dataclass
class NetworkConfigData:
    id: Optional[int] = None
    url: Optional[str] = None
    accounts: Optional[List[str]] = None
    from_account: Optional[str] = None
    leader_only: bool = False
    default_wait_interval: Optional[int] = None
    default_wait_retries: Optional[int] = None
    chain_type: Optional[str] = None

    def __post_init__(self):
        if self.id is not None and not isinstance(self.id, int):
            raise ValueError("id must be an integer")
        if self.url is not None and not isinstance(self.url, str):
            raise ValueError("url must be a string")
        if self.accounts is not None:
            if not isinstance(self.accounts, list):
                raise ValueError("accounts must be a list")
            if not all(isinstance(acc, str) for acc in self.accounts):
                raise ValueError("accounts must be strings")
        if self.from_account is not None and not isinstance(self.from_account, str):
            raise ValueError("from_account must be a string")
        if not isinstance(self.leader_only, bool):
            raise TypeError("leader_only must be a boolean")
        if self.default_wait_interval is not None and not isinstance(
            self.default_wait_interval, int
        ):
            raise ValueError("default_wait_interval must be an integer")
        if self.default_wait_retries is not None and not isinstance(
            self.default_wait_retries, int
        ):
            raise ValueError("default_wait_retries must be an integer")
        if self.chain_type is not None and not isinstance(self.chain_type, str):
            raise ValueError("chain_type must be a string")


@dataclass
class PathConfig:
    contracts: Optional[Path] = None
    artifacts: Optional[Path] = None

    def __post_init__(self):
        if self.contracts is not None and not isinstance(self.contracts, (str, Path)):
            raise ValueError("contracts must be a string or Path")
        if self.artifacts is not None and not isinstance(self.artifacts, (str, Path)):
            raise ValueError("artifacts must be a string or Path")


@dataclass
class UserConfig:
    networks: Dict[str, NetworkConfigData] = field(default_factory=dict)
    paths: PathConfig = field(default_factory=PathConfig)
    environment: Optional[str] = None
    default_network: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.networks, dict):
            raise ValueError("networks must be a dictionary")

        if not isinstance(self.paths, PathConfig):
            raise ValueError("paths must be a PathConfig instance")

        if self.environment is not None and not isinstance(self.environment, str):
            raise ValueError("environment must be a string")

        if self.default_network is not None and not isinstance(
            self.default_network, str
        ):
            raise ValueError("default_network must be a string")

        # Validate network configurations
        for name, network_config in self.networks.items():
            if not isinstance(network_config, NetworkConfigData):
                raise ValueError(f"network {name} must be a NetworkConfigData instance")


@dataclass
class GeneralConfig:
    user_config: UserConfig = field(default_factory=UserConfig)
    plugin_config: PluginConfig = field(default_factory=PluginConfig)

    def get_contracts_dir(self) -> Path:
        if self.plugin_config.contracts_dir is not None:
            return self.plugin_config.contracts_dir
        return self.user_config.paths.contracts

    def set_contracts_dir(self, contracts_dir: Path):
        self.plugin_config.contracts_dir = contracts_dir

    def get_artifacts_dir(self) -> Path:
        if self.plugin_config.artifacts_dir is not None:
            return self.plugin_config.artifacts_dir
        return self.user_config.paths.artifacts

    def set_artifacts_dir(self, artifacts_dir: Path):
        self.plugin_config.artifacts_dir = artifacts_dir

    def get_analysis_dir(self) -> Path:
        artifacts_dir = self.get_artifacts_dir()
        return artifacts_dir / "analysis"

    def get_networks_keys(self) -> List[str]:
        return list(self.user_config.networks.keys())

    def get_rpc_url(self) -> str:
        if self.plugin_config.rpc_url is not None:
            return self.plugin_config.rpc_url
        network_name = self.get_network_name()
        if network_name not in self.user_config.networks:
            raise ValueError(
                f"Unknown network: {network_name}, possible values: {self.get_networks_keys()}"
            )
        return self.user_config.networks[network_name].url

    def get_default_account_key(self, network_name: Optional[str] = None) -> str:
        if network_name is not None:
            return self.user_config.networks[network_name].from_account
        return self.user_config.networks[self.user_config.default_network].from_account

    def get_accounts_keys(self, network_name: Optional[str] = None) -> List[str]:
        if network_name is not None:
            return self.user_config.networks[network_name].accounts
        return self.user_config.networks[self.user_config.default_network].accounts

    def get_chain_type(self) -> str:
        # If chain_type is explicitly set via CLI, use it
        if self.plugin_config.chain_type is not None:
            if self.plugin_config.chain_type not in CHAINS:
                raise ValueError(
                    f"Unknown chain type: {self.plugin_config.chain_type}. "
                    f"Valid values: {', '.join(CHAINS)}"
                )
            return self.plugin_config.chain_type

        network_name = self.get_network_name()
        if network_name not in self.user_config.networks:
            raise ValueError(
                f"Unknown network: {network_name}, possible values: {self.get_networks_keys()}"
            )
        network_config = self.user_config.networks[network_name]
        # For preconfigured networks, use its chain type
        if network_name in PRECONFIGURED_NETWORKS:
            chain_type = network_config.chain_type
        else:
            # For custom networks, chain_type field is required
            chain_type = network_config.chain_type
            if not chain_type:
                raise ValueError(
                    f"Custom network {network_name} must specify a 'chain_type' field. "
                    f"Valid values: {', '.join(CHAINS)}"
                )

        if chain_type not in CHAINS:
            raise ValueError(
                f"Unknown chain type: {chain_type}. "
                f"Valid values: {', '.join(CHAINS)}"
            )
        return chain_type

    def get_chain(self) -> GenLayerChain:
        chain_map = {
            "localnet": localnet,
            "studionet": studionet,
            "testnet_asimov": testnet_asimov,
        }
        chain_type = self.get_chain_type()
        return chain_map[chain_type]

    def get_default_wait_interval(self) -> int:
        if self.plugin_config.default_wait_interval is not None:
            return self.plugin_config.default_wait_interval
        network_name = self.get_network_name()
        if network_name in self.user_config.networks:
            network_config = self.user_config.networks[network_name]
            if network_config.default_wait_interval is not None:
                return network_config.default_wait_interval
        return DEFAULT_WAIT_INTERVAL

    def get_default_wait_retries(self) -> int:
        if self.plugin_config.default_wait_retries is not None:
            return self.plugin_config.default_wait_retries
        network_name = self.get_network_name()
        if network_name in self.user_config.networks:
            network_config = self.user_config.networks[network_name]
            if network_config.default_wait_retries is not None:
                return network_config.default_wait_retries
        return DEFAULT_WAIT_RETRIES

    def get_network_name(self) -> str:
        if self.plugin_config.network_name is not None:
            return self.plugin_config.network_name
        return self.user_config.default_network

    def get_leader_only(self) -> bool:
        if self.plugin_config.leader_only:
            return True
        network_name = self.get_network_name()
        if network_name in self.user_config.networks:
            network_config = self.user_config.networks[network_name]
            return network_config.leader_only
        return DEFAULT_LEADER_ONLY

    def check_local_rpc(self) -> bool:
        return self.get_chain_type() == "localnet"

    def check_studio_based_rpc(self) -> bool:
        return self.get_chain_type() in ("studionet", "localnet")
