from enum import Enum


class NetworkConfig(str, Enum):
    LOCALNET = "localnet"
    TESTNET_ASIMOV = "testnet_asimov"
