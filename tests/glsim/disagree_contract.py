# v0.1.0
# { "Depends": "py-genlayer:latest" }

from genlayer import *
import json


class DisagreeContract(gl.Contract):
    result: str

    def __init__(self):
        self.result = ""

    @gl.public.write
    def always_disagree(self, value: str) -> None:
        def leader_fn():
            return value

        def validator_fn(leaders_res) -> bool:
            return False  # Always disagree

        self.result = gl.vm.run_nondet(leader_fn, validator_fn)

    @gl.public.view
    def get_result(self) -> str:
        return self.result
