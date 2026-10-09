# { "Depends": "py-genlayer:latest" }

from genlayer import *


class MessageTime(gl.Contract):
    def __init__(self):
        pass

    @gl.public.view
    def get_raw_datetime(self) -> str:
        return gl.message_raw["datetime"]
