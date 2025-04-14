from genlayer_py import create_account


def create_accounts(n_accounts: int):
    """
    Create a list of accounts
    """
    accounts = []
    for _ in range(n_accounts):
        accounts.append(create_account())
    return accounts

# Accounts for testing
accounts = create_accounts(n_accounts=10)

# Default account to use for transaction handling, if not specified
default_account = accounts[0]
