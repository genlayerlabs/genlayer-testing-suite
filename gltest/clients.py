from genlayer_py.chains import localnet
from genlayer_py import create_client
from gltest.accounts import get_default_account
from functools import lru_cache
from gltest_cli.config.general import get_general_config


@lru_cache(maxsize=1)
def get_gl_client():
    """
    Get the GenLayer client instance.
    """
    general_config = get_general_config()
    chain = general_config.get_chain()
    default_account = get_default_account()
    endpoint = general_config.get_rpc_url()
    return create_client(
        chain=chain,
        account=default_account,
        endpoint=endpoint,
    )


@lru_cache(maxsize=1)
def get_gl_hosted_studio_client():
    """
    Get the GenLayer hosted studio client instance.

    Note: This is a temporary solution to get contract schema.
    TODO: Remove this once we have a proper way to get contract schema from testnet.
    """
    return create_client(
        chain=localnet,
        account=get_default_account(),
        endpoint="https://studio.genlayer.com/api",
    )


@lru_cache(maxsize=1)
def get_local_client():
    """
    Get the GenLayer local client instance.

    Note: This is a temporary solution to get contract schema.
    TODO: Remove this once we have a proper way to get contract schema from testnet.
    """
    return create_client(
        chain=localnet,
        account=get_default_account(),
        endpoint="http://127.0.0.1:4000/api",
    )


def get_gl_provider():
    """
    Get the GenLayer provider instance.
    """
    client = get_gl_client()
    return client.provider
