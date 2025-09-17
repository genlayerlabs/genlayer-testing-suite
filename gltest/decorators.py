import pytest
from typing import Any, List, Union
from gltest_cli.config.general import get_general_config
from .types import ChainType


def gl_only_on_chains(chains: List[Union[ChainType, str]]):
    """Skip test unless current chain is in the specified list."""

    def decorator(func_or_class: Any) -> Any:
        chain_values = []
        for c in chains:
            if hasattr(c, "value"):
                chain_values.append(getattr(c, "value"))
            else:
                chain_values.append(str(c))
        current_chain = get_general_config().get_chain_type()
        skip = current_chain not in chain_values
        reason = (
            f"Test only runs on: {', '.join(chain_values)}. Current: {current_chain}"
        )
        return pytest.mark.skipif(skip, reason=reason)(func_or_class)

    return decorator


def gl_skip_on_chains(chains: List[Union[ChainType, str]]):
    """Skip test if current chain is in the specified list."""

    def decorator(func_or_class: Any) -> Any:
        chain_values = []
        for c in chains:
            if hasattr(c, "value"):
                chain_values.append(getattr(c, "value"))
            else:
                chain_values.append(str(c))
        current_chain = get_general_config().get_chain_type()
        skip = current_chain in chain_values
        reason = f"Test skipped on: {', '.join(chain_values)}. Current: {current_chain}"
        return pytest.mark.skipif(skip, reason=reason)(func_or_class)

    return decorator


gl_only_localnet = gl_only_on_chains([ChainType.LOCALNET])
gl_only_studionet = gl_only_on_chains([ChainType.STUDIONET])
gl_only_testnet_asimov = gl_only_on_chains([ChainType.TESTNET_ASIMOV])

gl_skip_localnet = gl_skip_on_chains([ChainType.LOCALNET])
gl_skip_studionet = gl_skip_on_chains([ChainType.STUDIONET])
gl_skip_testnet_asimov = gl_skip_on_chains([ChainType.TESTNET_ASIMOV])
