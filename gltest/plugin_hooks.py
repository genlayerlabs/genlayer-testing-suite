from gltest.plugin_config import set_contracts_dir
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--contracts-dir",
        action="store",
        default="contracts",
        help="Directory containing contract files",
    )


def pytest_configure(config):
    contracts_dir = config.getoption("--contracts-dir")
    set_contracts_dir(Path(contracts_dir))
