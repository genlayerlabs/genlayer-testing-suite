from genlayer_py.chains import localnet, testnet_asimov
from genlayer_py import create_client
from .account import default_account
from functools import lru_cache
from gltest_cli.config.general import get_general_config


@lru_cache(maxsize=1)
def get_gl_client():
    """
    Get the GenLayer client instance.
    """
    general_config = get_general_config()
    selected_network = general_config.get_network_name()
    chain = general_config.get_chain(selected_network)

    return create_client(
        chain=chain,
        account=default_account,
        endpoint=general_config.get_rpc_url(selected_network),
    )


def get_gl_provider():
    """
    Get the GenLayer provider instance.
    """
    client = get_gl_client()
    return client.provider
