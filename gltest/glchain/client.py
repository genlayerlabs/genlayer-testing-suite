from genlayer_py.chains import localnet
from genlayer_py import create_client
from .account import default_account
from functools import lru_cache

# Create the client
gl_client = create_client(chain=localnet, account=default_account)


@lru_cache(maxsize=1)
def get_gl_client():
    """
    Get the GenLayer client instance.
    """
    return gl_client
