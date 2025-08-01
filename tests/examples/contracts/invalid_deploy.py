# { "Depends": "py-genlayer:test" }

import genlayer as gl


class InvalidDeploy(gl.Contract):
    """Contract that always fails during deployment"""

    def __init__(self):
        raise Exception("This is an invalid deploy")
