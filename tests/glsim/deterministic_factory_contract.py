# v0.1.0
# Pinned to the GenVM runner whose std lib still exposes
# gl.contract.deploy(salt_nonce=...), the API glsim's deploy handler implements.
# Newer std libs (GenVM v0.6.0-rc15+) replace it with `salted=`.
# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }
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
            salt_nonce=salt,
            on="decided",
        )
        self.child_address = child_address.as_hex
        return self.child_address

    @gl.public.view
    def get_child(self) -> str:
        return self.child_address
