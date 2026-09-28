"""Tests for resolving SDK modules from the active GenVM layout.

The SDK relocated its Python-side modules under ``genlayer.py``. These helpers
feed the fd-0 message injection and address coercion in the direct runner, so a
stale import path there fails at contract-load time with an opaque
``DecodingError: unexpected end of memory`` rather than an ImportError.
"""

import pytest

from gltest.direct import sdk_compat

CONTRACT = (
    '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }\n'
    "from genlayer import *\n"
    "\n"
    "\n"
    "class NoArgContract(gl.Contract):\n"
    "    def __init__(self):\n"
    "        self.value: u256 = 1\n"
)


@pytest.fixture
def sdk_on_path(direct_deploy, tmp_path):
    """Deploy once so the SDK is on sys.path, as it is for real test runs."""
    contract = tmp_path / "NoArgContract.py"
    contract.write_text(CONTRACT)
    assert direct_deploy(str(contract)) is not None


class TestSdkModuleResolution:
    """import_calldata / import_types must find the modules the SDK ships."""

    def test_import_calldata_resolves(self, sdk_on_path):
        calldata = sdk_compat.import_calldata()
        assert hasattr(calldata, "encode")
        assert hasattr(calldata, "decode")

    def test_import_types_resolves(self, sdk_on_path):
        types = sdk_compat.import_types()
        assert hasattr(types, "Address")

    def test_import_address_is_a_type(self, sdk_on_path):
        address = sdk_compat.import_address()
        assert isinstance(address, type)
        assert address.SIZE == 20

    def test_import_address_u256_pair(self, sdk_on_path):
        address, u256 = sdk_compat.import_address_u256()
        assert isinstance(address, type)
        assert u256 is not None

    def test_modules_come_from_same_package(self, sdk_on_path):
        assert sdk_compat.import_calldata().__name__.startswith("genlayer")
        assert sdk_compat.import_types().__name__.startswith("genlayer")


def test_deploy_no_arg_contract(direct_deploy, tmp_path):
    """A no-argument contract must load; this is the import-time failure mode."""
    contract = tmp_path / "NoArgContract.py"
    contract.write_text(CONTRACT)
    assert direct_deploy(str(contract)) is not None
