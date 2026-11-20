import genlayer as gl


CHILD_CODE = """
import genlayer as gl


class Child(gl.contract.Contract):
    @gl.public.view
    def ping(self) -> str:
        return "pong"
"""


class DeterministicFactory(gl.contract.Contract):
    child_address: str

    def __init__(self):
        self.child_address = ""

    @gl.public.write
    def deploy_child(self, salt: int) -> str:
        child_address = gl.contract.deploy(
            code=CHILD_CODE.encode("utf-8"),
            args=[],
            kwargs={},
            salted=gl.contract.Salted(salt),
            on="decided",
        )
        self.child_address = child_address.as_hex
        return self.child_address

    @gl.public.view
    def predict_child(self, salt: int) -> str:
        return gl.contract.Salted(salt).resolve_hardcoded().as_hex

    @gl.public.view
    def get_child(self) -> str:
        return self.child_address
