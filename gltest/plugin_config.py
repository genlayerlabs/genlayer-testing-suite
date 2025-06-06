from pathlib import Path

_contracts_dir = None
_rpc_url = None
_default_wait_interval = None
_default_wait_retries = None


def set_contracts_dir(path: Path):
    global _contracts_dir
    _contracts_dir = path


def get_contracts_dir() -> Path:
    return Path(_contracts_dir)


def set_rpc_url(rpc_url: str):
    global _rpc_url
    _rpc_url = rpc_url


def get_rpc_url() -> str:
    return _rpc_url


def set_default_wait_interval(default_wait_interval: int):
    global _default_wait_interval
    _default_wait_interval = default_wait_interval


def get_default_wait_interval() -> int:
    return _default_wait_interval


def set_default_wait_retries(default_wait_retries: int):
    global _default_wait_retries
    _default_wait_retries = default_wait_retries


def get_default_wait_retries() -> int:
    return _default_wait_retries
