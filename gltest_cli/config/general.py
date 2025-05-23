from gltest_cli.config.types import GeneralConfig


_general_config = GeneralConfig()


def get_general_config() -> GeneralConfig:
    global _general_config

    return _general_config
