def test_help_message(pytester):
    result = pytester.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "gltest:",
            "  --contracts-dir=CONTRACTS_DIR",
            "                        Path to directory containing contract files",
            "  --artifacts-dir=ARTIFACTS_DIR",
            "                        Path to directory for storing contract artifacts",
            "  --default-wait-interval=DEFAULT_WAIT_INTERVAL",
            "                        Default interval (ms) between transaction receipt checks",
            "  --default-wait-retries=DEFAULT_WAIT_RETRIES",
            "                        Default number of retries for transaction receipt checks",
            "  --rpc-url=RPC_URL     RPC endpoint URL for the GenLayer network",
            "  --network=NETWORK     Target network (defaults to 'localnet' if no config",
            "                        file)",
            "  --test-with-mocks     Test with mocks",
            "  --leader-only         Run contracts in leader-only mode",
        ]
    )


def test_default_wait_interval(pytester):

    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_default_wait_interval():
            general_config = get_general_config()
            assert general_config.get_default_wait_interval() == 5000
    """
    )

    result = pytester.runpytest("--default-wait-interval=5000", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_default_wait_interval PASSED*",
        ]
    )
    assert result.ret == 0


def test_default_wait_retries(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_default_wait_retries():
            general_config = get_general_config()
            assert general_config.get_default_wait_retries() == 4000
    """
    )

    result = pytester.runpytest("--default-wait-retries=4000", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_default_wait_retries PASSED*",
        ]
    )
    assert result.ret == 0


def test_rpc_url(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_rpc_url():
            general_config = get_general_config()
            assert general_config.get_rpc_url() == 'http://custom-rpc-url:8545' 
    """
    )

    result = pytester.runpytest("--rpc-url=http://custom-rpc-url:8545", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_rpc_url PASSED*",
        ]
    )
    assert result.ret == 0


def test_network_localnet(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_network():
            general_config = get_general_config()
            assert general_config.get_network_name() == "localnet"
    """
    )

    result = pytester.runpytest("--network=localnet", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_network PASSED*",
        ]
    )
    assert result.ret == 0


def test_network_testnet(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_network():
            general_config = get_general_config()
            assert general_config.get_network_name() == "testnet_asimov"
    """
    )

    result = pytester.runpytest(
        "--network=testnet_asimov", "--rpc-url=http://test.example.com:9151", "-v"
    )

    result.stdout.fnmatch_lines(
        [
            "*::test_network PASSED*",
        ]
    )
    assert result.ret == 0


def test_artifacts_dir(pytester):
    """Test that artifacts directory CLI parameter works correctly."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_artifacts_dir():
            general_config = get_general_config()
            assert general_config.get_artifacts_dir() == Path("custom/artifacts")
    """
    )

    result = pytester.runpytest("--artifacts-dir=custom/artifacts", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_artifacts_dir PASSED*",
        ]
    )
    assert result.ret == 0


def test_contracts_and_artifacts_dirs(pytester):
    """Test that both contracts and artifacts directories can be set via CLI."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_both_dirs():
            general_config = get_general_config()
            assert general_config.get_contracts_dir() == Path("src/contracts")
            assert general_config.get_artifacts_dir() == Path("build/artifacts")
    """
    )

    result = pytester.runpytest(
        "--contracts-dir=src/contracts", "--artifacts-dir=build/artifacts", "-v"
    )

    result.stdout.fnmatch_lines(
        [
            "*::test_both_dirs PASSED*",
        ]
    )
    assert result.ret == 0


def test_test_with_mocks_true(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_test_with_mocks():
            general_config = get_general_config()
            assert general_config.get_test_with_mocks() == True
    """
    )

    result = pytester.runpytest("--test-with-mocks", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_test_with_mocks PASSED*",
        ]
    )
    assert result.ret == 0


def test_test_with_mocks_false(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_test_with_mocks():
            general_config = get_general_config()
            assert general_config.get_test_with_mocks() == False
            "*::test_test_with_mocks PASSED*",

    """
    )

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_test_with_mocks PASSED*",
        ]
    )
    assert result.ret == 0


def test_artifacts_dir_default_fallback(pytester):
    """Test that artifacts directory falls back to config file default when CLI not provided."""
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_artifacts_default():
            general_config = get_general_config()
            # Should use the default from config
            artifacts_dir = general_config.get_artifacts_dir()
            assert isinstance(artifacts_dir, Path)
            # Default should be 'artifacts' 
            assert str(artifacts_dir) == "artifacts"

    """
    )

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_artifacts_default PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_true(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only():
            general_config = get_general_config()
            assert general_config.get_leader_only() == True
    """
    )

    result = pytester.runpytest("--leader-only", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_false(pytester):
    pytester.makepyfile(
        """
        from gltest_cli.config.general import get_general_config

        def test_leader_only():
            general_config = get_general_config()
            assert general_config.get_leader_only() == False
    """
    )

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only PASSED*",
        ]
    )
    assert result.ret == 0
