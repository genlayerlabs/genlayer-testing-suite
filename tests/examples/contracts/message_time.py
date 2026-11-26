# { "Depends": "py-genlayer:latest" }

import genlayer as gl


class MessageTime(gl.contract.Contract):
    def __init__(self):
        pass

    @gl.public.view
    def get_message_datetime(self) -> str:
        return gl.message.datetime

    @gl.public.view
    def get_raw_datetime(self) -> str:
        return gl.message.raw["datetime"]
