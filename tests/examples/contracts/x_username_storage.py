# {
#   "Seq": [
#     { "Depends": "py-lib-genlayer-embeddings:09h0i209wrzh4xzq86f79c60x0ifs7xcjwl53ysrnw06i54ddxyi" },
#     { "Depends": "py-genlayer:1j12s63yfjpva9ik2xgnffgrs6v44y1f52jvj9w7xvdn7qckd379" }
#   ]
# }

from genlayer import *

import json
import typing
import urllib.parse


class XUsernameStorage(gl.Contract):
    username: str
    tweet_api_url: str

    def __init__(self):
        self.tweet_api_url = "https://domain.com/api/twitter"
        self.username = ""

    @gl.public.view
    def get_username(self) -> str:
        return self.username

    @gl.public.write
    def update_username(self, username: str):
        user_data = self.request_to_x(
            f"users/by/username/{username}", {"user.fields": "public_metrics,verified"}
        )
        self.username = user_data["username"]

    def request_to_x(
        self, endpoint: str, params: dict[typing.Any, typing.Any]
    ) -> dict[str, typing.Any]:
        proxy_url = self.tweet_api_url
        base_url = f"{proxy_url}/{endpoint}"

        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        def call_x_api() -> dict[str, typing.Any]:
            print(f"Requesting {url}")
            web_data_res = gl.nondet.web.get(url)
            print(f"Response status: {web_data_res.status}")

            if web_data_res.status != 200 or not web_data_res.body:
                raise ValueError(
                    f"Failed to fetch data from X API: {web_data_res.body}"
                )

            web_data = web_data_res.body.decode("utf-8")

            return json.loads(web_data)

        return gl.eq_principle.strict_eq(call_x_api)
