"""
Decorators to run or skip tests depending on the selected chain type.

The selected chain type is resolved at test setup time (after the gltest
plugin has loaded the CLI options and ``gltest.config.yaml``), so it honours
``--network`` and ``--chain-type``.

Usage::

    from gltest import only_on_chains, skip_on_chains, only_localnet

    @only_on_chains("localnet", "studionet")
    def test_uses_studio_only_rpc(): ...

    @skip_on_chains("testnet_asimov")
    class TestSlowFlows: ...

    pytestmark = only_localnet  # whole module
"""

from typing import Iterable, Optional, Tuple

import pytest

from gltest_cli.config.constants import CHAINS

ONLY_ON_CHAINS_MARKER = "gltest_only_on_chains"
SKIP_ON_CHAINS_MARKER = "gltest_skip_on_chains"


def _normalize_chains(chains: Tuple) -> Tuple[str, ...]:
    flat = []
    for chain in chains:
        if isinstance(chain, (list, tuple, set, frozenset)):
            flat.extend(chain)
        else:
            flat.append(chain)
    if not flat:
        raise ValueError("At least one chain type must be provided")
    for chain in flat:
        if chain not in CHAINS:
            raise ValueError(
                f"Unknown chain type: {chain!r}. Valid values: {', '.join(CHAINS)}"
            )
    return tuple(flat)


def only_on_chains(*chains) -> pytest.MarkDecorator:
    """Run the decorated test (function, class or module) only on the given chain types."""
    return getattr(pytest.mark, ONLY_ON_CHAINS_MARKER)(*_normalize_chains(chains))


def skip_on_chains(*chains) -> pytest.MarkDecorator:
    """Skip the decorated test (function, class or module) on the given chain types."""
    return getattr(pytest.mark, SKIP_ON_CHAINS_MARKER)(*_normalize_chains(chains))


def get_chain_skip_reason(
    chain_type: str,
    only_on: Iterable[Iterable[str]] = (),
    skip_on: Iterable[Iterable[str]] = (),
) -> Optional[str]:
    """Return a skip reason if a test must not run on ``chain_type``, else None.

    ``only_on`` / ``skip_on`` hold the chain lists of every applied marker.
    Multiple ``only_on`` markers are intersected (all must allow the chain).
    """
    for allowed in only_on:
        allowed = tuple(allowed)
        if chain_type not in allowed:
            return (
                f"test only runs on chain(s) {', '.join(allowed)}; "
                f"selected chain is {chain_type}"
            )
    for skipped in skip_on:
        if chain_type in skipped:
            return f"test is skipped on chain {chain_type}"
    return None


# Convenience shortcuts
only_localnet = only_on_chains("localnet")
only_studio_devnet = only_on_chains("studio_devnet")
only_studionet = only_on_chains("studionet")
only_testnet_asimov = only_on_chains("testnet_asimov")
only_testnet_bradbury = only_on_chains("testnet_bradbury")
skip_localnet = skip_on_chains("localnet")
skip_studio_devnet = skip_on_chains("studio_devnet")
skip_studionet = skip_on_chains("studionet")
skip_testnet_asimov = skip_on_chains("testnet_asimov")
skip_testnet_bradbury = skip_on_chains("testnet_bradbury")


__all__ = [
    "only_on_chains",
    "skip_on_chains",
    "get_chain_skip_reason",
    "only_localnet",
    "only_studio_devnet",
    "only_studionet",
    "only_testnet_asimov",
    "only_testnet_bradbury",
    "skip_localnet",
    "skip_studio_devnet",
    "skip_studionet",
    "skip_testnet_asimov",
    "skip_testnet_bradbury",
]
