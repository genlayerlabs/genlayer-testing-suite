import pytest

from gltest.decorators import (
    ONLY_ON_CHAINS_MARKER,
    SKIP_ON_CHAINS_MARKER,
    get_chain_skip_reason,
    only_on_chains,
    skip_on_chains,
)


def test_only_on_chains_builds_marker():
    mark = only_on_chains("localnet", "studionet")
    assert mark.name == ONLY_ON_CHAINS_MARKER
    assert mark.args == ("localnet", "studionet")


def test_skip_on_chains_accepts_list():
    mark = skip_on_chains(["testnet_asimov", "testnet_bradbury"])
    assert mark.name == SKIP_ON_CHAINS_MARKER
    assert mark.args == ("testnet_asimov", "testnet_bradbury")


@pytest.mark.parametrize("factory", [only_on_chains, skip_on_chains])
def test_unknown_chain_rejected(factory):
    with pytest.raises(ValueError, match="Unknown chain type"):
        factory("mainnet")


@pytest.mark.parametrize("factory", [only_on_chains, skip_on_chains])
def test_empty_chains_rejected(factory):
    with pytest.raises(ValueError, match="At least one chain"):
        factory()


def test_skip_reason_no_markers():
    assert get_chain_skip_reason("localnet") is None


def test_skip_reason_only_on():
    assert get_chain_skip_reason("localnet", only_on=[("localnet",)]) is None
    assert "only runs on" in get_chain_skip_reason("studionet", only_on=[("localnet",)])


def test_skip_reason_only_on_markers_intersect():
    only_on = [("localnet", "studionet"), ("studionet",)]
    assert get_chain_skip_reason("studionet", only_on=only_on) is None
    assert get_chain_skip_reason("localnet", only_on=only_on) is not None


def test_skip_reason_skip_on():
    assert get_chain_skip_reason("localnet", skip_on=[("studionet",)]) is None
    assert "skipped on chain localnet" in get_chain_skip_reason(
        "localnet", skip_on=[("localnet",)]
    )
