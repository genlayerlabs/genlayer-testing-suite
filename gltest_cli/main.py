import pytest
from gltest_cli.logging import logger
from gltest_cli.config.user import (
    user_config_exists,
    load_user_config,
    get_default_user_config,
)
from gltest_cli.config.general import get_general_config


def main():
    if not user_config_exists():
        logger.info(
            "gltest.config.yaml not found in the current directory, using default config"
        )
        user_config = get_default_user_config()
    else:
        logger.info("gltest.config.yaml found in the current directory, using it")
        user_config = load_user_config("gltest.config.yaml")

    general_config = get_general_config()
    general_config.user_config = user_config
    return pytest.main()
