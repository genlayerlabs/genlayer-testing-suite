import genlayer as gl


class MultiFileContract(gl.contract.Contract):
    other_addr: gl.Address

    def __init__(self):
        with open("/contract/other.py", "rt") as f:
            text = f.read()
        self.other_addr = gl.contract.deploy(
            code=text.encode("utf-8"),
            args=["123"],
            salt_nonce=gl.u256(1),
            value=gl.u256(0),
            on="accepted",
        )

    @gl.public.write
    def wait(self) -> None:
        pass

    @gl.public.view
    def test(self) -> str:
        return gl.contract.get_at(self.other_addr).view().test()
