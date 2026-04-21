# v0.1.0
# { "Depends": "py-genlayer:latest" }

from genlayer import *


class UpgradableStorage(gl.Contract):
    storage: str

    def __init__(self, initial_storage: str):
        self.storage = initial_storage

        # make the deployer an upgrader
        root = gl.storage.Root.get()
        root.upgraders.get().append(gl.message.sender_address)

        # lock critical slots so only upgraders can modify them
        root.lock_default()

    @gl.public.view
    def get_storage(self) -> str:
        return self.storage

    @gl.public.write
    def update_storage(self, new_storage: str) -> None:
        self.storage = new_storage

    @gl.public.write
    def upgrade(self, new_code: bytes) -> None:
        root = gl.storage.Root.get()
        code = root.code.get()
        code.truncate()
        code.extend(new_code)
