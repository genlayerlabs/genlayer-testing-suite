import pytest
import yaml
from unittest.mock import patch, mock_open
from gltest_cli.config.user import (
    get_default_user_config,
    load_user_config,
    validate_raw_user_config,
    transform_raw_to_user_config_with_defaults,
    user_config_exists,
    VALID_ROOT_KEYS,
    DEFAULT_NETWORK,
    DEFAULT_ENVIRONMENT,
    DEFAULT_CONTRACTS_DIR,
    DEFAULT_ARTIFACTS_DIR,
)
from gltest_cli.config.constants import DEFAULT_RPC_URL
from gltest_cli.config.types import UserConfig, NetworkConfigData, PathConfig
from unittest.mock import MagicMock
from pathlib import Path

# Test data
VALID_CONFIG = {
    "networks": {
        "default": "localnet",
        "localnet": {
            "url": "http://localhost:8545",
            "accounts": ["0x123", "0x456"],
            "from": "0x123",
        },
        "testnet_asimov": {
            "id": 4221,
            "url": "http://34.32.169.58:9151",
            "accounts": ["0x123", "0x456"],
            "from": "0x123",
        },
    },
    "paths": {"contracts": "contracts", "artifacts": "artifacts"},
    "environment": ".env",
}

INVALID_CONFIG = {
    "networks": {
        "default": "invalid_network",
        "localnet": {
            "url": 123,  # Invalid type
            "accounts": "not_a_list",  # Invalid type
            "from": 456,  # Invalid type
        },
    },
    "paths": {"invalid_path": "value"},
    "environment": 123,  # Invalid type
}


def test_get_default_user_config():
    config = get_default_user_config()

    # Check root structure
    assert isinstance(config, UserConfig)
    assert all(key in config.__dict__ for key in VALID_ROOT_KEYS)

    # Check networks
    assert DEFAULT_NETWORK == config.default_network
    assert DEFAULT_NETWORK in config.networks

    # Check network configuration
    network = config.networks[DEFAULT_NETWORK]
    assert isinstance(network, NetworkConfigData)
    assert network.url == DEFAULT_RPC_URL
    assert isinstance(network.accounts, list)
    assert isinstance(network.from_account, str)
    assert network.from_account in network.accounts

    # Check paths
    assert isinstance(config.paths, PathConfig)
    assert config.paths.contracts == DEFAULT_CONTRACTS_DIR
    assert config.paths.artifacts == DEFAULT_ARTIFACTS_DIR

    # Check environment
    assert config.environment == DEFAULT_ENVIRONMENT


def test_validate_raw_user_config_valid():
    # Should not raise any exceptions
    validate_raw_user_config(VALID_CONFIG)


def test_validate_raw_user_config_invalid():
    with pytest.raises(ValueError, match="Invalid configuration keys"):
        validate_raw_user_config({"invalid_key": "value"})

    with pytest.raises(ValueError, match="networks must be a dictionary"):
        validate_raw_user_config({"networks": "not_a_dict"})

    with pytest.raises(ValueError, match="default network invalid_network not found"):
        validate_raw_user_config(
            {
                "networks": {
                    "default": "invalid_network",
                    "localnet": {"url": "http://localhost:8545"},
                }
            }
        )

    with pytest.raises(ValueError, match="network localnet must be a dictionary"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": "not_a_dict"}}
        )

    with pytest.raises(ValueError, match="Invalid network key"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": {"invalid_key": "value"}}}
        )

    with pytest.raises(ValueError, match="url must be a string"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": {"url": 123}}}
        )

    with pytest.raises(ValueError, match="accounts must be a list"):
        validate_raw_user_config(
            {
                "networks": {
                    "default": "localnet",
                    "localnet": {"accounts": "not_a_list"},
                }
            }
        )

    with pytest.raises(ValueError, match="accounts must be strings"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": {"accounts": [123]}}}
        )

    with pytest.raises(ValueError, match="from must be a string"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": {"from": 123}}}
        )

    with pytest.raises(ValueError, match="leader_only must be a boolean"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "localnet": {"leader_only": "true"}}}
        )

    with pytest.raises(ValueError, match="paths must be a dictionary"):
        validate_raw_user_config({"paths": "not_a_dict"})

    with pytest.raises(ValueError, match="Invalid path keys"):
        validate_raw_user_config({"paths": {"invalid_path": "value"}})

    with pytest.raises(ValueError, match="environment must be a string"):
        validate_raw_user_config({"environment": 123})

    # Test validation for non-default networks
    with pytest.raises(ValueError, match="network testnet must be a dictionary"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": "not_a_dict"}}
        )

    with pytest.raises(ValueError, match="Invalid network key"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"invalid_key": "value"}}}
        )

    with pytest.raises(ValueError, match="url must be a string"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"url": 123}}}
        )

    with pytest.raises(ValueError, match="accounts must be a list"):
        validate_raw_user_config(
            {
                "networks": {
                    "default": "localnet",
                    "testnet": {"accounts": "not_a_list"},
                }
            }
        )

    with pytest.raises(ValueError, match="accounts must be strings"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"accounts": [123]}}}
        )

    with pytest.raises(ValueError, match="from must be a string"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"from": 123}}}
        )

    with pytest.raises(ValueError, match="leader_only must be a boolean"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"leader_only": "true"}}}
        )

    # Test required fields for non-default networks
    with pytest.raises(ValueError, match="network testnet must have an id"):
        validate_raw_user_config(
            {"networks": {"default": "localnet", "testnet": {"accounts": ["0x123"]}}}
        )

    with pytest.raises(ValueError, match="network testnet must have a url"):
        validate_raw_user_config(
            {
                "networks": {
                    "default": "localnet",
                    "testnet": {"id": 4221, "accounts": ["0x123"]},
                }
            }
        )

    with pytest.raises(ValueError, match="network testnet must have accounts"):
        validate_raw_user_config(
            {
                "networks": {
                    "default": "localnet",
                    "testnet": {"id": 4221, "url": "http://testnet:8545"},
                }
            }
        )

    # Test that 'from' is optional for non-default networks
    valid_config_without_from = {
        "networks": {
            "default": "localnet",
            "testnet": {
                "id": 4221,
                "url": "http://testnet:8545",
                "accounts": ["0x123", "0x456"],
            },
        }
    }
    # Should not raise any exception
    validate_raw_user_config(valid_config_without_from)


@patch("builtins.open", new_callable=mock_open, read_data=yaml.dump(VALID_CONFIG))
@patch("gltest_cli.config.user.load_dotenv")
def test_load_user_config(mock_load_dotenv, mock_file):
    config = load_user_config("dummy_path")

    # Check if file was opened
    mock_file.assert_called_once_with("dummy_path", "r")

    # Check if environment was loaded
    mock_load_dotenv.assert_called_once_with(
        dotenv_path=DEFAULT_ENVIRONMENT, override=True
    )

    # Check config structure
    assert isinstance(config, UserConfig)

    # Check default network
    assert config.default_network == "localnet"
    assert isinstance(config.networks["localnet"], NetworkConfigData)
    assert config.networks["localnet"].id == 61999
    assert config.networks["localnet"].url == "http://localhost:8545"
    assert config.networks["localnet"].accounts == ["0x123", "0x456"]
    assert config.networks["localnet"].from_account == "0x123"

    # Check testnet_asimov network
    assert isinstance(config.networks["testnet_asimov"], NetworkConfigData)
    assert config.networks["testnet_asimov"].id == 4221
    assert config.networks["testnet_asimov"].url == "http://34.32.169.58:9151"
    assert config.networks["testnet_asimov"].accounts == ["0x123", "0x456"]
    assert config.networks["testnet_asimov"].from_account == "0x123"

    # Check paths
    assert isinstance(config.paths, PathConfig)
    assert config.paths.contracts == Path("contracts")
    assert config.paths.artifacts == Path("artifacts")

    # Check environment
    assert config.environment == ".env"


def test_transform_raw_to_user_config_with_defaults():
    # Test with empty config
    config = transform_raw_to_user_config_with_defaults({})
    assert isinstance(config, UserConfig)
    assert all(key in config.__dict__ for key in VALID_ROOT_KEYS)

    # Test with partial config
    partial_config = {
        "networks": {"default": "localnet", "localnet": {"url": "custom_url"}}
    }
    config = transform_raw_to_user_config_with_defaults(partial_config)
    assert isinstance(config.networks["localnet"], NetworkConfigData)
    assert config.networks["localnet"].url == "custom_url"
    assert config.networks["localnet"].accounts is not None
    assert config.networks["localnet"].from_account is not None

    # Test with None network config
    config = transform_raw_to_user_config_with_defaults(
        {"networks": {"default": "localnet", "localnet": None}}
    )
    assert config.networks["localnet"] is not None
    assert isinstance(config.networks["localnet"], NetworkConfigData)

    # Test setting 'from' for non-default networks
    test_config = {
        "networks": {
            "default": "localnet",
            "localnet": {"url": "http://localhost:8545"},
            "testnet": {"url": "http://testnet:8545", "accounts": ["0x123", "0x456"]},
            "mainnet": {
                "url": "http://mainnet:8545",
                "accounts": ["0xabc", "0x789"],
                "from": "0x789",  # Already set
            },
        }
    }
    config = transform_raw_to_user_config_with_defaults(test_config)

    # Verify testnet got 'from' set to first account
    assert config.networks["testnet"].from_account == "0x123"

    # Verify mainnet kept its existing 'from' value
    assert config.networks["mainnet"].from_account == "0x789"

    # Verify localnet (default network) behavior remains unchanged
    assert config.networks["localnet"].from_account is not None
    assert (
        config.networks["localnet"].from_account in config.networks["localnet"].accounts
    )

    # Test with custom paths
    custom_paths_config = {
        "networks": {"default": "localnet"},
        "paths": {"contracts": "custom/contracts/path"},
    }
    config = transform_raw_to_user_config_with_defaults(custom_paths_config)
    assert config.paths.contracts == Path("custom/contracts/path")

    # Test with custom environment
    custom_env_config = {
        "networks": {"default": "localnet"},
        "environment": "custom.env",
    }
    config = transform_raw_to_user_config_with_defaults(custom_env_config)
    assert config.environment == "custom.env"


@patch("pathlib.Path.cwd")
def test_user_config_exists(mock_cwd):
    mock_path = MagicMock()
    mock_cwd.return_value = mock_path

    # Test when config exists
    config_file = MagicMock()
    config_file.name = "gltest.config.yaml"
    config_file.is_file.return_value = True
    mock_path.iterdir.return_value = [config_file]
    assert user_config_exists() is True

    # Test when config doesn't exist
    other_file = MagicMock()
    other_file.name = "other_file.txt"
    other_file.is_file.return_value = True
    mock_path.iterdir.return_value = [other_file]
    assert user_config_exists() is False

    # Test with no files
    mock_path.iterdir.return_value = []
    assert user_config_exists() is False


# Tests for artifacts directory functionality
def test_artifacts_path_in_config():
    """Test that artifacts path is properly handled in configuration."""
    config_with_artifacts = {
        "networks": {"default": "localnet"},
        "paths": {"contracts": "contracts", "artifacts": "build/artifacts"},
    }

    config = transform_raw_to_user_config_with_defaults(config_with_artifacts)
    assert config.paths.artifacts == Path("build/artifacts")


def test_artifacts_path_defaults():
    """Test that artifacts path defaults to DEFAULT_ARTIFACTS_DIR when not specified."""
    config_without_artifacts = {
        "networks": {"default": "localnet"},
        "paths": {"contracts": "contracts"},
    }

    config = transform_raw_to_user_config_with_defaults(config_without_artifacts)
    assert config.paths.artifacts == DEFAULT_ARTIFACTS_DIR


def test_artifacts_path_validation():
    """Test validation of artifacts path configuration."""
    # Valid config with artifacts
    valid_config = {"paths": {"artifacts": "custom/artifacts"}}
    validate_raw_user_config(valid_config)  # Should not raise

    # Test that artifacts is included in valid path keys
    from gltest_cli.config.user import VALID_PATHS_KEYS

    assert "artifacts" in VALID_PATHS_KEYS


def test_artifacts_path_only_config():
    """Test configuration with only artifacts path specified."""
    config_artifacts_only = {
        "networks": {"default": "localnet"},
        "paths": {"artifacts": "my_artifacts"},
    }

    config = transform_raw_to_user_config_with_defaults(config_artifacts_only)
    assert config.paths.contracts == DEFAULT_CONTRACTS_DIR
    assert config.paths.artifacts == Path("my_artifacts")
