from genlayer_py.chains import (
    localnet,
    studio_devnet,
    studionet,
    testnet_bradbury,
    testnet_clarke,
)
from genlayer_py.chains.localnet import SIMULATOR_JSON_RPC_URL
from genlayer_py.types import GenLayerChain
from pathlib import Path

GLTEST_CONFIG_FILE = "gltest.config.yaml"
DEFAULT_NETWORK = "localnet"
STUDIO_CHAINS: dict[str, GenLayerChain] = {
    "localnet": localnet,
    "studio_devnet": studio_devnet,
    "studionet": studionet,
}
# Public testnets ship no default accounts: gltest.config.yaml must provide them
TESTNET_CHAINS: dict[str, GenLayerChain] = {
    "testnet_bradbury": testnet_bradbury,
    "testnet_clarke": testnet_clarke,
}
PRESET_CHAINS: dict[str, GenLayerChain] = {**STUDIO_CHAINS, **TESTNET_CHAINS}
PRECONFIGURED_NETWORKS = list(PRESET_CHAINS)
CHAINS = PRECONFIGURED_NETWORKS.copy()
DEFAULT_RPC_URL = SIMULATOR_JSON_RPC_URL
DEFAULT_ENVIRONMENT = ".env"
DEFAULT_CONTRACTS_DIR = Path("contracts")
DEFAULT_ARTIFACTS_DIR = Path("artifacts")
DEFAULT_NETWORK_ID = 61127

# Defaults per network
DEFAULT_WAIT_INTERVAL = 3000
DEFAULT_WAIT_RETRIES = 50
DEFAULT_LEADER_ONLY = False
DEFAULT_FEE_PROFILE_HEADROOM = 1.25
