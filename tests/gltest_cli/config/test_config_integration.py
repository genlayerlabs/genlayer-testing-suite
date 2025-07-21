def test_leader_only_network_config_true(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only_network_config():
            general_config = get_general_config()
            assert general_config.get_leader_only() == True
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    leader_only: true

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only_network_config PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_network_config_false(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only_network_config():
            general_config = get_general_config()
            assert general_config.get_leader_only() == False
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    leader_only: false

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only_network_config PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_cli_overrides_network_config(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only_cli_overrides():
            general_config = get_general_config()
            assert general_config.get_leader_only() == True
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    leader_only: false

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    # CLI flag should override network config
    result = pytester.runpytest("--leader-only", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only_cli_overrides PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_network_config_default(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only_network_config_default():
            general_config = get_general_config()
            assert general_config.get_leader_only() == False
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only_network_config_default PASSED*",
        ]
    )
    assert result.ret == 0


def test_custom_accounts_config(pytester):
    """Test custom accounts configuration."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_custom_accounts():
            general_config = get_general_config()
            accounts = general_config.get_accounts_keys()
            assert len(accounts) == 3
            assert accounts[0] == "account1_private_key"
            assert accounts[1] == "account2_private_key"
            assert accounts[2] == "account3_private_key"
            from_account = general_config.get_default_account_key()
            assert from_account == "account1_private_key"
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    accounts:
      - "account1_private_key"
      - "account2_private_key"
      - "account3_private_key"

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_custom_accounts PASSED*",
        ]
    )
    assert result.ret == 0


def test_from_account_config(pytester):
    """Test 'from' account configuration."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_from_account():
            general_config = get_general_config()
            from_account = general_config.get_default_account_key()
            assert from_account == "account2_private_key"
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"
    accounts:
      - "account1_private_key"
      - "account2_private_key"
      - "account3_private_key"
    from: "account2_private_key"

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_from_account PASSED*",
        ]
    )
    assert result.ret == 0


def test_multiple_networks_config(pytester):
    """Test multiple networks configuration."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_multiple_networks():
            general_config = get_general_config()
            # Default should be testnet
            assert general_config.get_network_name() == "testnet"
            rpc_url = general_config.get_rpc_url()
            assert rpc_url == "https://testnet.example.com"
    """
    )

    config_content = """
networks:
  default: testnet
  localnet:
    id: 61999
    url: "http://127.0.0.1:4000/api"
    accounts:
      - "local_account1"
      - "local_account2"
  testnet:
    id: 5555
    url: "https://testnet.example.com"
    accounts:
      - "testnet_account1"
      - "testnet_account2"
    leader_only: true

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_multiple_networks PASSED*",
        ]
    )
    assert result.ret == 0


def test_custom_paths_config(pytester):
    """Test custom paths configuration."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_custom_paths():
            general_config = get_general_config()
            assert general_config.get_contracts_dir() == Path("src/contracts")
            assert general_config.get_artifacts_dir() == Path("build/artifacts")
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"

paths:
  contracts: "src/contracts"
  artifacts: "build/artifacts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_custom_paths PASSED*",
        ]
    )
    assert result.ret == 0


def test_custom_environment_file(pytester):
    """Test custom environment file configuration."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_custom_environment():
            general_config = get_general_config()
            assert general_config.user_config.environment == ".env.test"
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"

paths:
  contracts: "contracts"

environment: .env.test
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_custom_environment PASSED*",
        ]
    )
    assert result.ret == 0


def test_cli_network_override(pytester):
    """Test CLI network override of config file."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_network_override():
            general_config = get_general_config()
            assert general_config.get_network_name() == "testnet"
            rpc_url = general_config.get_rpc_url()
            assert rpc_url == "https://testnet.example.com"
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    id: 61999
    url: "http://127.0.0.1:4000/api"
    accounts:
      - "local_account1"
  testnet:
    id: 5555
    url: "https://testnet.example.com"
    accounts:
      - "testnet_account1"

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest("--network=testnet", "-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_network_override PASSED*",
        ]
    )
    assert result.ret == 0


def test_wait_interval_and_retries_config(pytester):
    """Test default wait interval and retries from CLI."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_wait_config():
            general_config = get_general_config()
            assert general_config.get_default_wait_interval() == 3000
            assert general_config.get_default_wait_retries() == 20
    """
    )

    config_content = """
networks:
  default: localnet
  localnet:
    url: "http://127.0.0.1:4000/api"

paths:
  contracts: "contracts"

environment: .env
"""

    pytester.makefile(".config.yaml", **{"gltest": config_content})

    result = pytester.runpytest(
        "--default-wait-interval=3000", "--default-wait-retries=20", "-v"
    )
    result.stdout.fnmatch_lines(
        [
            "*::test_wait_config PASSED*",
        ]
    )
    assert result.ret == 0
