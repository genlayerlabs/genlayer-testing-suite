# v0.1.0
# { "Depends": "py-genlayer:latest" }

import genlayer as gl


class multi_read_erc20(gl.contract.Contract):
    balances: gl.storage.TreeMap[gl.Address, gl.storage.TreeMap[gl.Address, gl.u256]]

    def __init__(self):
        pass

    @gl.public.write
    def update_token_balances(
        self, account_address: str, token_contracts: list[str]
    ) -> None:
        for token_contract in token_contracts:
            contract = gl.contract.get_at(gl.Address(token_contract))
            balance = contract.view().get_balance_of(account_address)
            self.balances.get_or_insert_default(gl.Address(account_address))[
                gl.Address(token_contract)
            ] = balance

    @gl.public.view
    def get_balances(self) -> dict[str, dict[str, int]]:
        return {
            k.as_hex: {k.as_hex: v for k, v in v.items()}
            for k, v in self.balances.items()
        }
