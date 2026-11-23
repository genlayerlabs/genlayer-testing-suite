# v0.1.0
# { "Depends": "py-genlayer:latest" }

import genlayer as gl


class read_erc20(gl.contract.Contract):
    token_contract: gl.Address

    def __init__(self, token_contract: str):
        self.token_contract = gl.Address(token_contract)

    @gl.public.view
    def get_balance_of(self, account_address: str) -> int:
        return (
            gl.contract.get_at(self.token_contract)
            .view()
            .get_balance_of(account_address)
        )
