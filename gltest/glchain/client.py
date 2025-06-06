from genlayer_py.chains import localnet
from genlayer_py import create_client
from .account import default_account
from functools import lru_cache
from gltest.plugin_config import get_rpc_url


@lru_cache(maxsize=1)
def get_gl_client():
    """
    Get the GenLayer client instance.
    """
    return create_client(
        chain=localnet, account=default_account, endpoint=get_rpc_url()
    )


def get_gl_provider():
    """
    Get the GenLayer provider instance.
    """
    client = get_gl_client()
    return client.provider
