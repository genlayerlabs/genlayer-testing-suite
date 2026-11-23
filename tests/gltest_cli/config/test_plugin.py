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
            "  --leader-only         Run contracts in leader-only mode",
            "  --chain-type=CHAIN_TYPE",
            "                        Chain type (possible values: localnet, studio_devnet,",
            "                        studionet, testnet_asimov, testnet_bradbury)",
            "  --fee-profile=FEE_PROFILE",
            "                        Path to write a JSON fee profile for observed deploys",
            "                        and writes",
            "  --fee-profile-headroom=FEE_PROFILE_HEADROOM",
            "                        Multiplier applied to observed fee maxima in --fee-",
            "                        profile output",
        ]
    )


def test_default_wait_interval(pytester):

    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_default_wait_interval():
            general_config = get_general_config()
            assert general_config.get_default_wait_interval() == 5000
    """)

    result = pytester.runpytest("--default-wait-interval=5000", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_default_wait_interval PASSED*",
        ]
    )
    assert result.ret == 0


def test_default_wait_retries(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_default_wait_retries():
            general_config = get_general_config()
            assert general_config.get_default_wait_retries() == 4000
    """)

    result = pytester.runpytest("--default-wait-retries=4000", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_default_wait_retries PASSED*",
        ]
    )
    assert result.ret == 0


def test_rpc_url(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_rpc_url():
            general_config = get_general_config()
            assert general_config.get_rpc_url() == 'http://custom-rpc-url:8545' 
    """)

    result = pytester.runpytest("--rpc-url=http://custom-rpc-url:8545", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_rpc_url PASSED*",
        ]
    )
    assert result.ret == 0


def test_network_localnet(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_network():
            general_config = get_general_config()
            assert general_config.get_network_name() == "localnet"
    """)

    result = pytester.runpytest("--network=localnet", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_network PASSED*",
        ]
    )
    assert result.ret == 0


def test_network_testnet(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_network():
            general_config = get_general_config()
            assert general_config.get_network_name() == "testnet_asimov"
    """)

    result = pytester.runpytest(
        "--network=testnet_asimov", "--rpc-url=http://test.example.com:9151", "-v"
    )

    # The test should exit with an error code when testnet_asimov is used without accounts
    assert result.ret != 0


def test_network_testnet_bradbury(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_network():
            general_config = get_general_config()
            assert general_config.get_network_name() == "testnet_bradbury"
    """)

    result = pytester.runpytest(
        "--network=testnet_bradbury", "--rpc-url=http://test.example.com:9151", "-v"
    )

    # The test should exit with an error code when testnet_bradbury is used without accounts
    assert result.ret != 0


def test_artifacts_dir(pytester):
    """Test that artifacts directory CLI parameter works correctly."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_artifacts_dir():
            general_config = get_general_config()
            assert general_config.get_artifacts_dir() == Path("custom/artifacts")
    """)

    result = pytester.runpytest("--artifacts-dir=custom/artifacts", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_artifacts_dir PASSED*",
        ]
    )
    assert result.ret == 0


def test_contracts_and_artifacts_dirs(pytester):
    """Test that both contracts and artifacts directories can be set via CLI."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_both_dirs():
            general_config = get_general_config()
            assert general_config.get_contracts_dir() == Path("src/contracts")
            assert general_config.get_artifacts_dir() == Path("build/artifacts")
    """)

    result = pytester.runpytest(
        "--contracts-dir=src/contracts", "--artifacts-dir=build/artifacts", "-v"
    )

    result.stdout.fnmatch_lines(
        [
            "*::test_both_dirs PASSED*",
        ]
    )
    assert result.ret == 0


def test_artifacts_dir_default_fallback(pytester):
    """Test that artifacts directory falls back to config file default when CLI not provided."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_artifacts_default():
            general_config = get_general_config()
            # Should use the default from config
            artifacts_dir = general_config.get_artifacts_dir()
            assert isinstance(artifacts_dir, Path)
            # Default should be 'artifacts' 
            assert str(artifacts_dir) == "artifacts"

    """)

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_artifacts_default PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_true(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_leader_only():
            general_config = get_general_config()
            assert general_config.get_leader_only() == True
    """)

    result = pytester.runpytest("--leader-only", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only PASSED*",
        ]
    )
    assert result.ret == 0


def test_leader_only_false(pytester):
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_leader_only():
            general_config = get_general_config()
            assert general_config.get_leader_only() == False
    """)

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_leader_only PASSED*",
        ]
    )
    assert result.ret == 0


def test_chain_localnet(pytester):
    """Test that --chain=localnet sets the chain correctly."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_chain():
            general_config = get_general_config()
            assert general_config.get_chain_type() == "localnet"
    """)

    result = pytester.runpytest("--chain-type=localnet", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_chain PASSED*",
        ]
    )
    assert result.ret == 0


def test_chain_studionet(pytester):
    """Test that --chain=studionet sets the chain correctly."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_chain():
            general_config = get_general_config()
            assert general_config.get_chain_type() == "studionet"
    """)

    result = pytester.runpytest("--chain-type=studionet", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_chain PASSED*",
        ]
    )
    assert result.ret == 0


def test_chain_testnet_asimov(pytester):
    """Test that --chain=testnet_asimov sets the chain correctly."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_chain_type():
            general_config = get_general_config()
            assert general_config.get_chain_type() == "testnet_asimov"
    """)

    result = pytester.runpytest("--chain-type=testnet_asimov", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_chain_type PASSED*",
        ]
    )
    assert result.ret == 0


def test_chain_invalid(pytester):
    """Test that an invalid chain name raises an error."""
    pytester.makepyfile("""
        import pytest
        from gltest_cli.config.general import get_general_config

        def test_chain_type():
            general_config = get_general_config()
            with pytest.raises(ValueError, match="Unknown chain type"):
                general_config.get_chain_type()
    """)

    result = pytester.runpytest("--chain-type=invalid_chain", "-v")

    # The test should fail because of the invalid chain
    assert result.ret != 0


def test_chain_none_default(pytester):
    """Test that when --chain is not provided, it defaults to None."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_chain_type():
            general_config = get_general_config()
            # Should use network's default chain
            assert general_config.plugin_config.chain_type is None
            # get_chain_type should still work using network config
            chain_type = general_config.get_chain_type()
            assert chain_type in ["localnet", "studionet", "testnet_asimov", "testnet_bradbury"]
    """)

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_chain_type PASSED*",
        ]
    )
    assert result.ret == 0


def test_chain_overrides_network_config(pytester):
    """Test that --chain overrides the network's configured chain."""
    pytester.makepyfile("""
        from gltest_cli.config.general import get_general_config

        def test_chain_override():
            general_config = get_general_config()
            # Even though network is localnet, chain should be studionet
            assert general_config.get_network_name() == "localnet"
            assert general_config.get_chain_type() == "studionet"
    """)

    result = pytester.runpytest("--network=localnet", "--chain-type=studionet", "-v")

    result.stdout.fnmatch_lines(
        [
            "*::test_chain_override PASSED*",
        ]
    )
    assert result.ret == 0


def test_fee_profile_options(pytester, tmp_path):
    from gltest_cli.config.general import get_general_config

    profile_path = tmp_path / "fees.json"
    pytester.makepyfile(f"""
        from gltest_cli.config.general import get_general_config
        from pathlib import Path

        def test_fee_profile_options():
            general_config = get_general_config()
            assert general_config.get_fee_profile_path() == Path({str(profile_path)!r})
            assert general_config.get_fee_profile_headroom() == 1.5
    """)

    try:
        result = pytester.runpytest(
            f"--fee-profile={profile_path}",
            "--fee-profile-headroom=1.5",
            "-v",
        )
    finally:
        # The in-process run mutates the shared config singleton; reset it so
        # the outer gltest session does not write a fee profile of its own.
        general_config = get_general_config()
        general_config.plugin_config.fee_profile_path = None
        general_config.plugin_config.fee_profile_headroom = None

    result.stdout.fnmatch_lines(
        [
            "*::test_fee_profile_options PASSED*",
        ]
    )
    assert result.ret == 0
    assert profile_path.exists()


def test_fee_profile_headroom_must_be_positive(pytester):
    from gltest_cli.config.general import get_general_config

    pytester.makepyfile("""
        def test_placeholder():
            assert True
    """)

    try:
        result = pytester.runpytest("--fee-profile-headroom=0", "-v")
    finally:
        general_config = get_general_config()
        general_config.plugin_config.fee_profile_path = None
        general_config.plugin_config.fee_profile_headroom = None

    assert result.ret != 0


def test_current_network_and_chain_type(pytester):
    pytester.makepyfile("""
        from gltest import get_current_network, get_current_chain_type

        def test_runtime_network(current_network, current_chain_type):
            assert current_network == "my_testnet"
            assert current_chain_type == "testnet_asimov"
            assert get_current_network() == current_network
            assert get_current_chain_type() == current_chain_type
    """)

    pytester.makefile(
        ".config.yaml",
        **{
            "gltest": """
networks:
  default: my_testnet
  my_testnet:
    id: 55554
    url: "https://testnet.example.com"
    accounts:
      - "0x1111111111111111111111111111111111111111111111111111111111111111"
    chain_type: "testnet_asimov"
"""
        },
    )

    result = pytester.runpytest("-v")

    result.stdout.fnmatch_lines(["*::test_runtime_network PASSED*"])
    assert result.ret == 0


def test_current_chain_type_follows_chain_type_flag(pytester):
    pytester.makepyfile("""
        def test_runtime_chain(current_network, current_chain_type):
            assert current_network == "localnet"
            assert current_chain_type == "studionet"
    """)

    result = pytester.runpytest("--network=localnet", "--chain-type=studionet", "-v")

    result.stdout.fnmatch_lines(["*::test_runtime_chain PASSED*"])
    assert result.ret == 0


def test_network_time_is_reset_between_tests(pytester):
    pytester.makeconftest("""
        import pytest
        from gltest.helpers import network_time

        class FakeProvider:
            offset = 86400  # clock already shifted before the session starts
            calls = []

            def make_request(self, method, params):
                FakeProvider.calls.append(method)
                if method == "sim_increaseTime":
                    FakeProvider.offset += params[0]
                return {"result": {
                    "total_offset_seconds": FakeProvider.offset,
                    "effective_datetime": "2030-01-01T00:00:00+00:00",
                }}

        network_time.get_gl_provider = lambda: FakeProvider()
    """)
    pytester.makepyfile("""
        from conftest import FakeProvider
        from gltest.helpers import increase_time, get_network_time

        def test_a_shifts_clock():
            assert get_network_time().offset_seconds == 0
            increase_time(86400)
            assert get_network_time().offset_seconds == 86400

        def test_b_sees_reset_clock():
            assert get_network_time().offset_seconds == 0
            FakeProvider.offset += 60  # raw RPC-style shift, not via helpers

        def test_b2_raw_shift_does_not_leak():
            assert get_network_time().offset_seconds == 0

        def test_c_clear():
            FakeProvider.calls.clear()
    """)

    # Subprocess: the fake provider must not leak into this pytest process.
    result = pytester.runpytest_subprocess("-v", "-p", "no:randomly")

    result.stdout.fnmatch_lines(
        [
            "*::test_a_shifts_clock PASSED*",
            "*::test_b_sees_reset_clock PASSED*",
            "*::test_b2_raw_shift_does_not_leak PASSED*",
            "*::test_c_clear PASSED*",
        ]
    )
    assert result.ret == 0


def test_network_time_not_touched_on_hosted_studio(pytester):
    pytester.makeconftest("""
        from gltest.helpers import network_time

        class FakeProvider:
            calls = []

            def make_request(self, method, params):
                FakeProvider.calls.append(method)
                return {"result": {
                    "total_offset_seconds": 60,
                    "effective_datetime": "2030-01-01T00:00:00+00:00",
                }}

        network_time.get_gl_provider = lambda: FakeProvider()
    """)
    pytester.makepyfile("""
        from conftest import FakeProvider

        def test_one():
            pass

        def test_two_no_clock_rpc():
            assert FakeProvider.calls == []
    """)

    result = pytester.runpytest_subprocess(
        "-v", "-p", "no:randomly", "--network=studionet"
    )

    result.stdout.fnmatch_lines(["*::test_two_no_clock_rpc PASSED*"])
    assert result.ret == 0


def test_network_time_cleanup_on_non_loopback_localnet(pytester):
    """A Compose-style URL is only touched after a helper changed the clock."""
    pytester.makeconftest("""
        from gltest.helpers import network_time

        class FakeProvider:
            offset = 0
            calls = []

            def make_request(self, method, params):
                FakeProvider.calls.append(method)
                if method == "sim_increaseTime":
                    FakeProvider.offset += params[0]
                return {"result": {
                    "total_offset_seconds": FakeProvider.offset,
                    "effective_datetime": "2030-01-01T00:00:00+00:00",
                }}

        network_time.get_gl_provider = lambda: FakeProvider()
    """)
    pytester.makepyfile("""
        from conftest import FakeProvider
        from gltest.helpers import increase_time, get_network_time

        def test_a_untouched_sends_no_rpc():
            assert FakeProvider.calls == []

        def test_b_helper_shift():
            increase_time(86400)
            assert FakeProvider.offset == 86400

        def test_c_shift_was_cleaned_up():
            assert FakeProvider.offset == 0
    """)
    result = pytester.runpytest_subprocess(
        "-v", "-p", "no:randomly", "--network=localnet", "--rpc-url=http://glsim:4000/api"
    )
    result.stdout.fnmatch_lines(
        ["*::test_a_untouched_sends_no_rpc PASSED*", "*::test_c_shift_was_cleaned_up PASSED*"]
    )
    assert result.ret == 0


def test_timed_out_write_blocks_next_test_on_non_loopback_localnet(pytester):
    pytester.makeconftest("""
        import threading
        from gltest.helpers import network_time

        release = threading.Event()

        class SlowProvider:
            offset = 0

            def make_request(self, method, params):
                if method == "sim_increaseTime":
                    release.wait(10)
                    SlowProvider.offset += params[0]
                return {"result": {
                    "total_offset_seconds": SlowProvider.offset,
                    "effective_datetime": "2030-01-01T00:00:00+00:00",
                }}

        network_time.get_gl_provider = lambda: SlowProvider()
        network_time.REQUEST_TIMEOUT_SECONDS = 0.2

        def pytest_sessionfinish(session, exitstatus):
            release.set()
    """)
    pytester.makepyfile("""
        import pytest
        from gltest.helpers import increase_time

        def test_a_write_times_out():
            with pytest.raises(Exception):
                increase_time(60)

        def test_b_must_not_run():
            raise AssertionError("body executed with a pending clock write")
    """)
    result = pytester.runpytest_subprocess(
        "-v", "-p", "no:randomly", "--network=localnet", "--rpc-url=http://glsim:4000/api"
    )
    result.stdout.fnmatch_lines(["*unknown outcome*"])
    out = result.stdout.str()
    assert "body executed with a pending clock write" not in out
    assert result.ret != 0


def test_interrupted_teardown_does_not_leak_shift_on_non_loopback_localnet(pytester):
    pytester.makepyfile("""
        import pytest
        from conftest import Provider
        from gltest.helpers import increase_time

        def test_a_shift_then_outage():
            increase_time(60)
            Provider.down = True  # refused during teardown

        def test_b_still_down_is_blocked():
            raise AssertionError("ran while clock cleanup was pending")

        def test_c_recovered():
            assert Provider.offset == 0
    """)
    pytester.makeconftest("""
        import pytest
        from gltest.helpers import network_time

        class Provider:
            offset = 0
            down = False

            def make_request(self, method, params):
                if Provider.down:
                    raise ConnectionRefusedError("[Errno 111] Connection refused")
                if method == "sim_increaseTime":
                    Provider.offset += params[0]
                return {"result": {
                    "total_offset_seconds": Provider.offset,
                    "effective_datetime": "2030-01-01T00:00:00+00:00",
                }}

        network_time.get_gl_provider = lambda: Provider()

        def pytest_runtest_logreport(report):
            # The outage ends once test_b was blocked in setup.
            if "test_b" in report.nodeid and report.when == "setup" and report.failed:
                Provider.down = False
    """)
    result = pytester.runpytest_subprocess(
        "-v", "-p", "no:randomly", "--network=localnet", "--rpc-url=http://glsim:4000/api"
    )
    out = result.stdout.str()
    assert "ran while clock cleanup was pending" not in out
    result.stdout.fnmatch_lines(["*::test_c_recovered PASSED*"])
    result.stdout.fnmatch_lines(["*test_b_still_down_is_blocked ERROR*"])
