# { "Depends": "py-genlayer:latest" }

import genlayer as gl


class CurrentStyleContract(gl.contract.Contract):
    storage: str

    def __init__(self, initial_storage: str):
        self.storage = initial_storage

    @gl.public.view
    def get_storage(self) -> str:
        return self.storage

    @gl.public.write
    def update_storage(self, new_storage: str) -> None:
        self.storage = new_storage
