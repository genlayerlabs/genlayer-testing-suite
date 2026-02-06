# v0.1.0
# { "Depends": "py-genlayer:latest" }

from genlayer import *
import json


class WebContract(gl.Contract):
    result: str

    def __init__(self):
        self.result = ""

    @gl.public.write
    def fetch_data(self, url: str) -> None:
        def leader_fn():
            resp = gl.nondet.web.get(url)
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            data = json.loads(resp.body.decode("utf-8"))
            return data.get("value", "")

        def validator_fn(leaders_res) -> bool:
            return True

        self.result = gl.vm.run_nondet(leader_fn, validator_fn)

    @gl.public.view
    def get_result(self) -> str:
        return self.result

    @gl.public.write
    def fail_always(self) -> None:
        raise ValueError("intentional failure")
