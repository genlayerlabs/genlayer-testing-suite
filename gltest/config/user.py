import os
import yaml
import re
from dotenv import load_dotenv
from pathlib import Path

GLTEST_CONFIG_FILE = "gltest.config.yaml"


def load_user_config(path: str) -> dict:
    with open(path, "r") as f:
        raw_config = yaml.safe_load(f)

    dotenv_path = raw_config.get("dotenv", ".env")
    load_dotenv(dotenv_path=dotenv_path, override=True)

    def resolve_env_vars(obj):
        if isinstance(obj, str):
            return re.sub(
                r"\${(\w+)}",
                lambda m: os.getenv(m.group(1), f"<UNSET:{m.group(1)}>"),
                obj,
            )
        elif isinstance(obj, dict):
            return {k: resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_env_vars(i) for i in obj]
        return obj

    return resolve_env_vars(raw_config)


def check_user_config() -> bool:
    if any(p.name == GLTEST_CONFIG_FILE for p in Path.cwd().iterdir() if p.is_file()):
        return True
    return False
