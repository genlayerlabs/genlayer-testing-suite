import pytest
from pathlib import Path
from gltest_cli.config.types import (
    GeneralConfig,
    UserConfig,
    PluginConfig,
    PathConfig,
    NetworkConfigData,
)
from gltest_cli.config.constants import DEFAULT_ARTIFACTS_DIR, DEFAULT_CONTRACTS_DIR


def test_general_config_artifacts_methods():
    """Test GeneralConfig artifacts directory methods."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(contracts=Path("contracts"), artifacts=Path("user_artifacts")),
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Test get_artifacts_dir returns user config value when plugin config is not set
    assert general_config.get_artifacts_dir() == Path("user_artifacts")

    # Test set_artifacts_dir updates plugin config
    general_config.set_artifacts_dir(Path("plugin_artifacts"))
    assert general_config.get_artifacts_dir() == Path("plugin_artifacts")

    # Plugin config should take precedence
    assert general_config.plugin_config.artifacts_dir == Path("plugin_artifacts")


def test_general_config_artifacts_default():
    """Test GeneralConfig artifacts directory with default values."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(artifacts=DEFAULT_ARTIFACTS_DIR),
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return default artifacts directory
    assert general_config.get_artifacts_dir() == DEFAULT_ARTIFACTS_DIR


def test_general_config_artifacts_plugin_precedence():
    """Test that plugin config takes precedence over user config for artifacts."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(artifacts=Path("user_artifacts")),
    )

    plugin_config = PluginConfig(artifacts_dir=Path("plugin_artifacts"))
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Plugin config should take precedence
    assert general_config.get_artifacts_dir() == Path("plugin_artifacts")


def test_general_config_artifacts_none_values():
    """Test GeneralConfig behavior when artifacts paths are None."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()}, paths=PathConfig(artifacts=None)
    )

    plugin_config = PluginConfig(artifacts_dir=None)
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return None when both are None
    assert general_config.get_artifacts_dir() is None


def test_general_config_both_contracts_and_artifacts():
    """Test that both contracts and artifacts directories work together."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(
            contracts=Path("src/contracts"), artifacts=Path("build/artifacts")
        ),
    )

    plugin_config = PluginConfig(
        contracts_dir=Path("custom/contracts"), artifacts_dir=Path("custom/artifacts")
    )

    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Both should return plugin values (precedence)
    assert general_config.get_contracts_dir() == Path("custom/contracts")
    assert general_config.get_artifacts_dir() == Path("custom/artifacts")


def test_general_config_mixed_precedence():
    """Test mixed precedence where only one path is overridden in plugin."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(
            contracts=Path("user/contracts"), artifacts=Path("user/artifacts")
        ),
    )

    # Only override artifacts in plugin config
    plugin_config = PluginConfig(artifacts_dir=Path("plugin/artifacts"))
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Contracts should come from user config, artifacts from plugin config
    assert general_config.get_contracts_dir() == Path("user/contracts")
    assert general_config.get_artifacts_dir() == Path("plugin/artifacts")


def test_path_config_validation():
    """Test PathConfig validation for artifacts."""
    # Valid path configurations
    valid_config = PathConfig(contracts=Path("contracts"), artifacts=Path("artifacts"))
    assert valid_config.contracts == Path("contracts")
    assert valid_config.artifacts == Path("artifacts")

    # Test with string paths
    string_config = PathConfig(contracts="contracts", artifacts="artifacts")
    # PathConfig should handle string conversion in __post_init__
    assert string_config.contracts == "contracts"
    assert string_config.artifacts == "artifacts"


def test_path_config_invalid_types():
    """Test PathConfig validation with invalid types."""
    # Test invalid artifacts type
    with pytest.raises(ValueError, match="artifacts must be a string or Path"):
        PathConfig(artifacts=123)

    # Test invalid contracts type (existing validation)
    with pytest.raises(ValueError, match="contracts must be a string or Path"):
        PathConfig(contracts=123)


def test_general_config_contracts_default():
    """Test GeneralConfig contracts directory with default values."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
        paths=PathConfig(contracts=DEFAULT_CONTRACTS_DIR),
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return default contracts directory
    assert general_config.get_contracts_dir() == DEFAULT_CONTRACTS_DIR
