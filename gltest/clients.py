from genlayer_py.chains import localnet
from genlayer_py import create_client
from gltest.accounts import get_default_account
from functools import lru_cache
from gltest_cli.config.general import get_general_config
from gltest.exceptions import GenLayerRPCError


def _keep_rpc_error_details(client):
    """Make the client's provider raise ``GenLayerRPCError`` on RPC errors.

    The SDK provider only keeps ``error.message``, which for failed contract
    executions on Studio is just "execution failed"; the GenVM stderr lives in
    ``error.data``. ``GenLayerRPCError`` subclasses ``GenLayerError``, so
    callers catching the SDK error keep working.
    """
    provider = getattr(client, "provider", None)
    if provider is None or not hasattr(provider, "_raise_on_error"):
        return client

    def _raise_on_error(resp, ctx):
        err = resp.get("error") if isinstance(resp, dict) else None
        if not err:
            return
        if not isinstance(err, dict):
            err = {"message": str(err)}
        raise GenLayerRPCError(
            method=ctx,
            code=err.get("code", "unknown"),
            message=err.get("message", "unknown error"),
            data=err.get("data"),
        )

    provider._raise_on_error = _raise_on_error
    return client


@lru_cache(maxsize=1)
def get_gl_client():
    """
    Get the GenLayer client instance.
    """
    general_config = get_general_config()
    chain = general_config.get_chain()
    default_account = get_default_account()
    endpoint = general_config.get_rpc_url()
    client = create_client(
        chain=chain,
        account=default_account,
        endpoint=endpoint,
    )
    return _keep_rpc_error_details(client)


@lru_cache(maxsize=1)
def get_gl_hosted_studio_client():
    """
    Get the GenLayer hosted studio client instance.

    Note: This is a temporary solution to get contract schema.
    TODO: Remove this once we have a proper way to get contract schema from testnet.
    """
    client = create_client(
        chain=localnet,
        account=get_default_account(),
        endpoint="https://studio.genlayer.com/api",
    )
    return _keep_rpc_error_details(client)


@lru_cache(maxsize=1)
def get_local_client():
    """
    Get the GenLayer local client instance.

    Note: This is a temporary solution to get contract schema.
    TODO: Remove this once we have a proper way to get contract schema from testnet.
    """
    client = create_client(
        chain=localnet,
        account=get_default_account(),
        endpoint="http://127.0.0.1:4000/api",
    )
    return _keep_rpc_error_details(client)


def get_gl_provider():
    """
    Get the GenLayer provider instance.
    """
    client = get_gl_client()
    return client.provider
