def test_help_message(pytester):
    result = pytester.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "gltest:",
            "  --contracts-dir=CONTRACTS_DIR",
            "                        Directory containing contract files",
            "  --default-wait-interval=DEFAULT_WAIT_INTERVAL",
            "                        Default wait interval for waiting transaction receipts",
            "  --default-wait-retries=DEFAULT_WAIT_RETRIES",
            "                        Default wait retries for waiting transaction receipts",
            "  --rpc-url=RPC_URL     RPC URL for the genlayer network",
            "  --network=NETWORK     The target network, possible values: localnet,",
            "                        testnet_asimov [default: localnet]",
        ]
    )


def test_default_wait_interval(pytester):

    pytester.makepyfile(
        """
        from gltest.plugin_config import get_default_wait_interval

        def test_default_wait_interval():
            assert get_default_wait_interval() == 5000
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
        from gltest.plugin_config import get_default_wait_retries

        def test_default_wait_retries():
            assert get_default_wait_retries() == 4000
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
        from gltest.plugin_config import get_rpc_url

        def test_rpc_url():
            assert get_rpc_url() == 'http://custom-rpc-url:8545' 
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
        from gltest.plugin_config import get_network
        from gltest.config import NetworkConfig

        def test_network():
            assert get_network() == NetworkConfig.LOCALNET
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
        from gltest.plugin_config import get_network
        from gltest.config import NetworkConfig

        def test_network():
            assert get_network() == NetworkConfig.TESTNET_ASIMOV
    """
    )

    result = pytester.runpytest("--network=testnet_asimov", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_network PASSED*",
        ]
    )
    assert result.ret == 0
