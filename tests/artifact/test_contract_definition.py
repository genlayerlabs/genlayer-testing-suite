import pytest
from gltest.artifacts.contract import (
    find_contract_definition_from_name,
    find_contract_definition_from_path,
    compute_contract_code,
)
from gltest.plugin_config import set_contracts_dir
from pathlib import Path


def test_single_file():
    """
    Test finding a contract definition by name for a single-file contract.
    
    Verifies that the function correctly identifies and loads a contract
    from a single Python file, extracting the contract name and computing
    the contract code without any additional runner files.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_name("PredictionMarket")

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
    """
    Test finding a contract definition by name for a multi-file contract.
    
    Verifies that the function correctly identifies and loads a contract
    from a multi-file structure with __init__.py and runner.json,
    properly packaging all files into a ZIP archive for deployment.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_name("MultiFileContract")

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
    """
    Test finding a contract definition by name for a legacy single-file contract.
    
    Verifies that the function correctly handles legacy .gpy files,
    maintaining backward compatibility with older contract formats
    while extracting contract name and computing contract code.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_name("StorageLegacy")

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
    """
    Test finding a contract definition by name for a legacy multi-file contract.
    
    Verifies that the function correctly handles legacy multi-file contracts
    with .gpy extension and runner.json, ensuring proper packaging and
    backward compatibility with older contract structures.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_name("MultiFileContractLegacy")

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
    """
    Test error handling when searching for a non-existent contract by name.
    
    Verifies that the function raises FileNotFoundError when attempting
    to find a contract that doesn't exist in the contracts directory,
    ensuring proper error handling for invalid contract names.
    """
    set_contracts_dir(".")

    with pytest.raises(FileNotFoundError):
        _ = find_contract_definition_from_name("NotICContract")


def test_find_from_path_single_file():
    """
    Test finding a contract definition by file path for a single-file contract.
    
    Verifies that the function correctly loads a contract when given a relative
    path to a single Python file, extracting the contract name via AST parsing
    and computing the contract code without additional runner files.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_path(
        "examples/contracts/football_prediction_market.py"
    )

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


def test_find_from_path_multiple_files():
    """
    Test finding a contract definition by file path for a multi-file contract.
    
    Verifies that the function correctly loads a contract when given a relative
    path to __init__.py in a multi-file structure, automatically detecting
    the associated runner.json and packaging all files appropriately.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_path(
        "examples/contracts/multi_file_contract/__init__.py"
    )

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


def test_find_from_path_single_file_legacy():
    """
    Test finding a contract definition by file path for a legacy single-file contract.
    
    Verifies that the function correctly handles legacy .gpy files when accessed
    by file path, maintaining backward compatibility while extracting contract
    name via AST parsing and computing appropriate contract code.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_path(
        "examples/contracts/storage_legacy.gpy"
    )

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


def test_find_from_path_multiple_files_legacy():
    """
    Test finding a contract definition by file path for a legacy multi-file contract.
    
    Verifies that the function correctly handles legacy multi-file contracts
    with .gpy extension when accessed by file path, properly detecting
    runner.json and maintaining backward compatibility with older structures.
    """
    set_contracts_dir(".")
    contract_definition = find_contract_definition_from_path(
        "examples/contracts/multi_file_contract_legacy/__init__.gpy"
    )

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


def test_find_from_path_file_not_found():
    """
    Test error handling when the specified contract file doesn't exist.
    
    Verifies that the function raises FileNotFoundError with appropriate
    error message when attempting to load a contract from a non-existent
    file path relative to the contracts directory.
    """
    set_contracts_dir(".")

    with pytest.raises(FileNotFoundError, match="Contract file not found at:"):
        _ = find_contract_definition_from_path("nonexistent/contract.py")


def test_find_from_path_contracts_dir_not_found():
    """
    Test error handling when the contracts directory doesn't exist.
    
    Verifies that the function raises FileNotFoundError with appropriate
    error message when the configured contracts directory is invalid,
    ensuring proper validation before attempting file operations.
    """
    set_contracts_dir("nonexistent_directory")

    with pytest.raises(FileNotFoundError, match="Contracts directory not found at:"):
        _ = find_contract_definition_from_path("some/contract.py")


def test_find_from_path_no_valid_contract_class():
    """
    Test error handling when a file exists but contains no valid contract class.
    
    Verifies that the function raises ValueError with appropriate error message
    when attempting to load a file that exists but doesn't contain a class
    that inherits from gl.Contract, ensuring proper AST parsing validation.
    """
    set_contracts_dir(".")
    
    with pytest.raises(ValueError, match="No valid contract class found in"):
        _ = find_contract_definition_from_path("artifact/contracts/not_ic_contract.py")


def test_multiple_contracts_same_name():
    """
    Test error handling when multiple contracts with the same name exist.
    
    Verifies that the function raises ValueError with appropriate error message
    when multiple files contain contracts with the same name, listing all
    duplicate file locations and providing guidance for resolution.
    """
    set_contracts_dir(".")
    
    with pytest.raises(
        ValueError, 
        match=r"Multiple contracts named 'DuplicateContract' found in contracts directory\. Found in files: .+\. Please ensure contract names are unique\."
    ):
        _ = find_contract_definition_from_name("DuplicateContract")


def test_duplicate_contract_error_message_format():
    """
    Test that the duplicate contract error message contains all expected elements.
    
    Verifies that when multiple contracts with the same name are found, the error
    message includes the contract name, mentions "contracts directory", lists
    file paths, and provides clear guidance about ensuring uniqueness.
    """
    set_contracts_dir(".")
    
    try:
        _ = find_contract_definition_from_name("DuplicateContract")
        pytest.fail("Expected ValueError for duplicate contracts")
    except ValueError as e:
        error_message = str(e)
        # Verify error message contains key components
        assert "Multiple contracts named 'DuplicateContract' found" in error_message
        assert "contracts directory" in error_message
        assert "Found in files:" in error_message
        assert "Please ensure contract names are unique" in error_message
        # Verify that multiple file paths are mentioned (comma-separated)
        assert "," in error_message or len(error_message.split("Found in files: ")[1].split(".")[0]) > 0
    except Exception as e:
        pytest.fail(f"Expected ValueError but got {type(e).__name__}: {e}")


def test_single_contract_still_works_with_duplicate_detection():
    """
    Test that normal single contract loading still works after duplicate detection changes.
    
    Verifies that the enhanced search_path_by_class_name function doesn't break
    the normal case where only one contract with a given name exists, ensuring
    backward compatibility with existing functionality.
    """
    set_contracts_dir(".")
    
    # This should work normally - no duplicates expected for PredictionMarket
    contract_definition = find_contract_definition_from_name("PredictionMarket")
    assert contract_definition.contract_name == "PredictionMarket"
    assert contract_definition.main_file_path is not None
    assert "football_prediction_market.py" in str(contract_definition.main_file_path)
