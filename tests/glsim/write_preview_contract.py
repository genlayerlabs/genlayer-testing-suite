import genlayer as gl


class WritePreview(gl.contract.Contract):
    value: gl.u256
    received: gl.u256

    def __init__(self):
        self.value = 0
        self.received = 0

    @gl.public.write.payable
    def send(self, target: str, fail: bool) -> int:
        self.value = int(gl.message.value)
        gl.contract.get_at(gl.Address(target)).emit(on="decided").receive(1)
        if fail:
            raise RuntimeError("preview failed after emit")
        return self.value

    @gl.public.write.payable
    def take_value(self) -> int:
        self.value = int(gl.message.value)
        return self.value

    @gl.public.write
    def receive(self, amount: int) -> None:
        self.received += amount

    @gl.public.view
    def get_received(self) -> int:
        return self.received

    @gl.public.view
    def get_value(self) -> int:
        return self.value
