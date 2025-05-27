from gltest_cli.config.general import get_general_config
from genlayer_py import create_account


def create_accounts(n_accounts: int):
    return [create_account() for _ in range(n_accounts)]


def get_accounts():
    general_config = get_general_config()
    selected_network = general_config.get_network_name()
    accounts = general_config.get_accounts_keys(selected_network)
    return [create_account(account) for account in accounts]


def get_default_account():
    general_config = get_general_config()
    selected_network = general_config.get_network_name()
    default_account_key = general_config.get_default_account_key(selected_network)
    return create_account(default_account_key)
