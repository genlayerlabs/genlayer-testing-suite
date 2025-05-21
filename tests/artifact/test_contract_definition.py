import pytest
from gltest.artifacts.contract import (
    find_contract_definition,
    compute_contract_code,
)
from gltest.plugin_config import set_contracts_dir
from pathlib import Path


def test_single_file():
    set_contracts_dir(".")
    contract_definition = find_contract_definition("PredictionMarket")

    assert contract_definition.contract_name == "PredictionMarket"

    # Assert complete contract definition
    expected_main_file_path = Path("examples/contracts/football_prediction_market.py")
    expected_runner_file_path = None
    contract_code = compute_contract_code(
        expected_main_file_path, expected_runner_file_path
    )
    assert contract_definition.contract_code == contract_code
    assert (
        str(contract_definition.main_file_path)
        == "examples/contracts/football_prediction_market.py"
    )
    assert contract_definition.runner_file_path is None


def test_multiple_files():
    set_contracts_dir(".")
    contract_definition = find_contract_definition("MultiFileContract")

    assert contract_definition.contract_name == "MultiFileContract"

    # Assert complete contract definition
    expected_main_file_path = Path("examples/contracts/multi_file_contract/__init__.py")
    expected_runner_file_path = Path(
        "examples/contracts/multi_file_contract/runner.json"
    )
    assert contract_definition.main_file_path == expected_main_file_path
    assert contract_definition.runner_file_path == expected_runner_file_path
    contract_code = compute_contract_code(
        expected_main_file_path, expected_runner_file_path
    )
    assert contract_definition.contract_code == contract_code


def test_single_file_legacy():
    set_contracts_dir(".")
    contract_definition = find_contract_definition("StorageLegacy")

    # Assert complete contract definition
    assert contract_definition.contract_name == "StorageLegacy"
    expected_main_file_path = Path("examples/contracts/storage_legacy.gpy")
    expected_runner_file_path = None
    contract_code = compute_contract_code(
        expected_main_file_path, expected_runner_file_path
    )
    assert contract_definition.contract_code == contract_code
    assert (
        str(contract_definition.main_file_path)
        == "examples/contracts/storage_legacy.gpy"
    )
    assert contract_definition.runner_file_path is None


def test_multiple_files_legacy():
    set_contracts_dir(".")
    contract_definition = find_contract_definition("MultiFileContractLegacy")

    # Assert complete contract definition
    assert contract_definition.contract_name == "MultiFileContractLegacy"
    expected_main_file_path = Path(
        "examples/contracts/multi_file_contract_legacy/__init__.gpy"
    )
    expected_runner_file_path = Path(
        "examples/contracts/multi_file_contract_legacy/runner.json"
    )
    assert contract_definition.main_file_path == expected_main_file_path
    assert contract_definition.runner_file_path == expected_runner_file_path
    contract_code = compute_contract_code(
        expected_main_file_path, expected_runner_file_path
    )
    assert contract_definition.contract_code == contract_code


def test_class_is_not_intelligent_contract():
    set_contracts_dir(".")

    with pytest.raises(FileNotFoundError):
        _ = find_contract_definition("NotICContract")
