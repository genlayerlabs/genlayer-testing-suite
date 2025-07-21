from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from genlayer_py.chains import localnet, testnet_asimov
from genlayer_py.types import GenLayerChain
from urllib.parse import urlparse


class NetworkConfig(str, Enum):
    LOCALNET = "localnet"
    TESTNET_ASIMOV = "testnet_asimov"


@dataclass
class PluginConfig:
    contracts_dir: Optional[Path] = None
    artifacts_dir: Optional[Path] = None
    rpc_url: Optional[str] = None
    default_wait_interval: Optional[int] = None
    default_wait_retries: Optional[int] = None
    network_name: Optional[str] = None
    test_with_mocks: bool = False
    leader_only: bool = False


@dataclass
class NetworkConfigData:
    id: Optional[int] = None
    url: Optional[str] = None
    accounts: Optional[List[str]] = None
    from_account: Optional[str] = None
    leader_only: bool = False

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

    def get_rpc_url(self) -> str:
        if self.plugin_config.rpc_url is not None:
            return self.plugin_config.rpc_url
        network_name = self.get_network_name()
        return self.user_config.networks[network_name].url

    def get_default_account_key(self, network_name: Optional[str] = None) -> str:
        if network_name is not None:
            return self.user_config.networks[network_name].from_account
        return self.user_config.networks[self.user_config.default_network].from_account

    def get_accounts_keys(self, network_name: Optional[str] = None) -> List[str]:
        if network_name is not None:
            return self.user_config.networks[network_name].accounts
        return self.user_config.networks[self.user_config.default_network].accounts

    def get_chain(self) -> GenLayerChain:
        chain_map_by_id = {
            61999: localnet,
            4221: testnet_asimov,
        }
        network_name = self.get_network_name()
        network_id = self.user_config.networks[network_name].id
        if network_id not in chain_map_by_id:
            known = ", ".join(map(str, chain_map_by_id.keys()))
            raise ValueError(
                f"Unknown network: {network_name}, possible values: {known}"
            )
        return chain_map_by_id[network_id]

    def get_default_wait_interval(self) -> int:
        if self.plugin_config.default_wait_interval is not None:
            return self.plugin_config.default_wait_interval
        raise ValueError("default_wait_interval is not set")

    def get_default_wait_retries(self) -> int:
        if self.plugin_config.default_wait_retries is not None:
            return self.plugin_config.default_wait_retries
        raise ValueError("default_wait_retries is not set")

    def get_network_name(self) -> str:
        if self.plugin_config.network_name is not None:
            return self.plugin_config.network_name
        return self.user_config.default_network

    def get_test_with_mocks(self) -> bool:
        return self.plugin_config.test_with_mocks

    def get_leader_only(self) -> bool:
        if self.plugin_config.leader_only:
            return True
        network_name = self.get_network_name()
        if network_name in self.user_config.networks:
            network_config = self.user_config.networks[network_name]
            return network_config.leader_only
        return False

    def check_local_rpc(self) -> bool:
        SUPPORTED_RPC_DOMAINS = ["localhost", "127.0.0.1"]
        rpc_url = self.get_rpc_url()
        domain = urlparse(rpc_url).netloc.split(":")[0]  # Extract domain without port
        return domain in SUPPORTED_RPC_DOMAINS

    def check_studio_based_rpc(self) -> bool:
        SUPPORTED_RPC_DOMAINS = ["localhost", "127.0.0.1"]
        rpc_url = self.get_rpc_url()
        domain = urlparse(rpc_url).netloc.split(":")[0]  # Extract domain without port

        if domain in SUPPORTED_RPC_DOMAINS:
            return True

        # Check .genlayer.com or .genlayerlabs.com subdomains
        if domain.endswith(".genlayer.com") or domain.endswith(".genlayerlabs.com"):
            return True

        return False
