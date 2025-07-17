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


def test_general_config_leader_only_default():
    """Test GeneralConfig leader_only with default values."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData()},
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return False by default
    assert general_config.get_leader_only() is False


def test_general_config_leader_only_network_config():
    """Test GeneralConfig leader_only from network configuration."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(leader_only=True)},
        default_network="localnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return True from network config
    assert general_config.get_leader_only() is True


def test_general_config_leader_only_plugin_precedence():
    """Test that plugin config takes precedence over network config for leader_only."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(leader_only=False)},
        default_network="localnet",
    )

    plugin_config = PluginConfig(leader_only=True)
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Plugin config should take precedence
    assert general_config.get_leader_only() is True


def test_general_config_leader_only_multiple_networks():
    """Test leader_only with multiple networks."""
    user_config = UserConfig(
        networks={
            "localnet": NetworkConfigData(leader_only=False),
            "testnet": NetworkConfigData(leader_only=True),
        },
        default_network="testnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should use the default network's leader_only value
    assert general_config.get_leader_only() is True

    # Change network via plugin config
    plugin_config.network_name = "localnet"
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)
    assert general_config.get_leader_only() is False


def test_general_config_leader_only_network_not_found():
    """Test leader_only when selected network is not found."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(leader_only=True)},
        default_network="localnet",
    )

    plugin_config = PluginConfig(network_name="nonexistent")
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Should return False when network is not found
    assert general_config.get_leader_only() is False


def test_check_local_rpc_with_localhost():
    """Test check_local_rpc with localhost URL."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="http://localhost:8545")},
        default_network="localnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    assert general_config.check_local_rpc() is True


def test_check_local_rpc_with_127_0_0_1():
    """Test check_local_rpc with 127.0.0.1 URL."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="http://127.0.0.1:8545")},
        default_network="localnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    assert general_config.check_local_rpc() is True


def test_check_local_rpc_with_external_url():
    """Test check_local_rpc with external URL."""
    user_config = UserConfig(
        networks={"testnet": NetworkConfigData(url="https://api.genlayer.com:8545")},
        default_network="testnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    assert general_config.check_local_rpc() is False


def test_check_local_rpc_with_plugin_override():
    """Test check_local_rpc with plugin config RPC URL override."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="https://external.com")},
        default_network="localnet",
    )

    plugin_config = PluginConfig(rpc_url="http://localhost:9000")
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Plugin config should take precedence
    assert general_config.check_local_rpc() is True


def test_check_studio_based_rpc_with_localhost():
    """Test check_studio_based_rpc with localhost URL."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="http://localhost:8545")},
        default_network="localnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    assert general_config.check_studio_based_rpc() is True


def test_check_studio_based_rpc_with_127_0_0_1():
    """Test check_studio_based_rpc with 127.0.0.1 URL."""
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="http://127.0.0.1:8545")},
        default_network="localnet",
    )

    plugin_config = PluginConfig()
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    assert general_config.check_studio_based_rpc() is True


def test_check_studio_based_rpc_with_genlayer_subdomain():
    """Test check_studio_based_rpc with .genlayer.com subdomains."""
    test_cases = [
        "https://api.genlayer.com:8545",
        "https://test.genlayer.com",
        "http://staging.api.genlayer.com:9000",
        "https://dev.test.genlayer.com",
    ]

    for url in test_cases:
        user_config = UserConfig(
            networks={"testnet": NetworkConfigData(url=url)},
            default_network="testnet",
        )

        plugin_config = PluginConfig()
        general_config = GeneralConfig(
            user_config=user_config, plugin_config=plugin_config
        )

        assert general_config.check_studio_based_rpc() is True, f"Failed for URL: {url}"


def test_check_studio_based_rpc_with_genlayerlabs_subdomain():
    """Test check_studio_based_rpc with .genlayerlabs.com subdomains."""
    test_cases = [
        "https://api.genlayerlabs.com:8545",
        "https://test.genlayerlabs.com",
        "http://staging.api.genlayerlabs.com:9000",
        "https://dev.test.genlayerlabs.com",
    ]

    for url in test_cases:
        user_config = UserConfig(
            networks={"testnet": NetworkConfigData(url=url)},
            default_network="testnet",
        )

        plugin_config = PluginConfig()
        general_config = GeneralConfig(
            user_config=user_config, plugin_config=plugin_config
        )

        assert general_config.check_studio_based_rpc() is True, f"Failed for URL: {url}"


def test_check_studio_based_rpc_with_non_genlayer_domain():
    """Test check_studio_based_rpc with non-GenLayer domains."""
    test_cases = [
        "https://api.example.com:8545",
        "https://test.otherdomain.com",
        "http://staging.api.random.org:9000",
        "https://genlayer.example.com",  # Not a subdomain of .genlayer.com
        "https://genlayerlabs.example.com",  # Not a subdomain of .genlayerlabs.com
    ]

    for url in test_cases:
        user_config = UserConfig(
            networks={"testnet": NetworkConfigData(url=url)},
            default_network="testnet",
        )

        plugin_config = PluginConfig()
        general_config = GeneralConfig(
            user_config=user_config, plugin_config=plugin_config
        )

        assert (
            general_config.check_studio_based_rpc() is False
        ), f"Failed for URL: {url}"


def test_check_studio_based_rpc_with_plugin_override():
    """Test check_studio_based_rpc with plugin config RPC URL override."""
    # User config has external URL, but plugin overrides with GenLayer domain
    user_config = UserConfig(
        networks={"localnet": NetworkConfigData(url="https://external.com")},
        default_network="localnet",
    )

    plugin_config = PluginConfig(rpc_url="https://api.genlayer.com:9000")
    general_config = GeneralConfig(user_config=user_config, plugin_config=plugin_config)

    # Plugin config should take precedence
    assert general_config.check_studio_based_rpc() is True

    # Test opposite case: user has GenLayer domain, plugin overrides with external
    user_config2 = UserConfig(
        networks={"localnet": NetworkConfigData(url="https://api.genlayer.com")},
        default_network="localnet",
    )

    plugin_config2 = PluginConfig(rpc_url="https://external.com:9000")
    general_config2 = GeneralConfig(
        user_config=user_config2, plugin_config=plugin_config2
    )

    # Plugin config should take precedence
    assert general_config2.check_studio_based_rpc() is False
