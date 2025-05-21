import pytest
from gltest.logging import logger
from gltest.config import check_user_config, load_user_config


def main():
    if not check_user_config():
        logger.error("gltest.config.yaml not found in the current directory")
        return

    config = load_user_config("gltest.config.yaml")
    print(config)
    # return pytest.main()
