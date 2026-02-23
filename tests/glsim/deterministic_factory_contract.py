import genlayer.gl as gl
from genlayer.py.types import u256


CHILD_CODE = """
import genlayer.gl as gl


class Child(gl.Contract):
    @gl.public.view
    def ping(self) -> str:
        return "pong"
"""


class DeterministicFactory(gl.Contract):
    child_address: str

    def __init__(self):
        self.child_address = ""

    @gl.public.write
    def deploy_child(self, salt: int) -> str:
        child_address = gl.deploy_contract(
            code=CHILD_CODE.encode("utf-8"),
            args=[],
            kwargs={},
            salt_nonce=u256(salt),
            on="accepted",
        )
        self.child_address = child_address.as_hex
        return self.child_address

    @gl.public.view
    def get_child(self) -> str:
        return self.child_address
