# v0.1.0
# { "Depends": "py-genlayer:latest" }

from genlayer import *


class UpgradableStorage(gl.Contract):
    # storage layout must remain compatible with v1
    storage: str

    def __init__(self):
        pass

    @gl.public.view
    def get_storage(self) -> str:
        return self.storage

    @gl.public.write
    def update_storage(self, new_storage: str) -> None:
        self.storage = new_storage

    # new method added in v2
    @gl.public.view
    def get_storage_length(self) -> int:
        return len(self.storage)

    @gl.public.write
    def upgrade(self, new_code: bytes) -> None:
        root = gl.storage.Root.get()
        code = root.code.get()
        code.truncate()
        code.extend(new_code)
