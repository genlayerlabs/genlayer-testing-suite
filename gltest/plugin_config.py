from pathlib import Path

_contracts_dir = None


def set_contracts_dir(path: Path):
    global _contracts_dir
    _contracts_dir = path


def get_contracts_dir() -> Path:
    return Path(_contracts_dir)
