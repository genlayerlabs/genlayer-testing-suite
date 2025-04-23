import ast
from typing import Optional
from dataclasses import dataclass
from gltest.plugin_config import get_contracts_dir


@dataclass
class ContractDefinition:
    """Class that represents a contract definition from a .gpy file."""

    contract_name: str
    contract_code: str
    source_file: str
    ast_node: ast.ClassDef


def find_contract_definition(contract_name: str) -> Optional[ContractDefinition]:
    """
    Search in the contracts directory for a contract definition.
    TODO: Make this more robust to handle imports and other files.
    """
    contracts_dir = get_contracts_dir()

    if not contracts_dir.exists():
        raise FileNotFoundError(f"Contracts directory not found at: {contracts_dir}")

    # Search through all .gpy files in the contracts directory
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
                    return ContractDefinition(
                        contract_name=contract_name,
                        source_file=str(file_path),
                        contract_code=content,
                        ast_node=node,
                    )
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
    return None
