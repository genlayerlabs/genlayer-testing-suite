import ast
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from gltest.plugin_config import get_contracts_dir
import io
import zipfile
from typing import Union


@dataclass
class ContractDefinition:
    """Class that represents a contract definition from a .gpy file."""

    contract_name: str
    contract_code: Union[str, bytes]
    main_file_path: Path
    runner_file_path: Optional[Path]


def search_path_by_class_name(contracts_dir: Path, contract_name: str) -> Path:
    """Search for a file by class name in the contracts directory."""
    for file_path in contracts_dir.rglob("*.gpy"):
        try:
            # Read the file content
            with open(file_path, "r") as f:
                content = f.read()
            # Parse the content into an AST
            tree = ast.parse(content)
            # Search for class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == contract_name:
                    # Found the contract class
                    return file_path
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
    raise FileNotFoundError(f"Contract {contract_name} not found at: {contracts_dir}")


def compute_contract_code(
    main_file_path: Path,
    runner_file_path: Optional[Path] = None,
) -> str:
    """Compute the contract code."""
    # Single file contract
    if runner_file_path is None:
        return main_file_path.read_text()

    # Multifile contract
    main_file_dir = main_file_path.parent
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, mode="w") as zip:
        zip.write(main_file_path, "contract/__init__.py")
        for file_path in main_file_dir.rglob("*"):
            if file_path.name in ["runner.json", "__init__.gpy"]:
                continue
            rel_path = file_path.relative_to(main_file_dir)
            zip.write(file_path, f"contract/{rel_path}")
        zip.write(runner_file_path, "runner.json")
    buffer.flush()
    return buffer.getvalue()


def find_contract_definition(contract_name: str) -> Optional[ContractDefinition]:
    """
    Search in the contracts directory for a contract definition.
    """
    contracts_dir = get_contracts_dir()
    if not contracts_dir.exists():
        raise FileNotFoundError(f"Contracts directory not found at: {contracts_dir}")
    main_file_path = search_path_by_class_name(contracts_dir, contract_name)
    main_file_dir = main_file_path.parent
    runner_file_path = None
    if main_file_path.name == "__init__.gpy":
        # Likely a multifile contract
        runner_file_path = main_file_dir.joinpath("runner.json")
        if not runner_file_path.exists():
            # No runner file, so it's a single file contract
            runner_file_path = None
    return ContractDefinition(
        contract_name=contract_name,
        contract_code=compute_contract_code(main_file_path, runner_file_path),
        main_file_path=main_file_path,
        runner_file_path=runner_file_path,
    )
