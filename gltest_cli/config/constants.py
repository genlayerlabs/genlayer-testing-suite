from genlayer_py.chains.localnet import SIMULATOR_JSON_RPC_URL
from pathlib import Path


GLTEST_CONFIG_FILE = "gltest.config.yaml"
DEFAULT_NETWORK = "localnet"
PRECONFIGURED_NETWORKS = ["localnet", "studionet", "testnet_asimov"]
CHAINS = ["localnet", "studionet", "testnet_asimov"]
DEFAULT_RPC_URL = SIMULATOR_JSON_RPC_URL
DEFAULT_ENVIRONMENT = ".env"
DEFAULT_CONTRACTS_DIR = Path("contracts")
DEFAULT_ARTIFACTS_DIR = Path("artifacts")
DEFAULT_NETWORK_ID = 61999

# Defaults per network
DEFAULT_WAIT_INTERVAL = 3000
DEFAULT_WAIT_RETRIES = 50
DEFAULT_LEADER_ONLY = False
