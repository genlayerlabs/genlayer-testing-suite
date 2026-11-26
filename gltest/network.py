"""
Runtime information about the network selected for the current test run.

The values are resolved lazily from the gltest configuration (``--network``,
``--chain-type`` and ``gltest.config.yaml``), so they reflect CLI overrides even
though the configuration is loaded after test modules are imported.
"""

from gltest_cli.config.general import get_general_config


def get_current_network() -> str:
    """Return the name of the selected network, e.g. ``"localnet"``.

    This is the key passed to ``--network`` (or the configured default
    network), so it can also be the name of a custom network from
    ``gltest.config.yaml``.
    """
    return get_general_config().get_network_name()


def get_current_chain_type() -> str:
    """Return the chain type of the selected network.

    One of ``localnet``, ``studio_devnet``, ``studionet`` or
    ``testnet_bradbury``. Honours ``--chain-type`` and the ``chain_type``
    of custom networks, so it is the safer value to branch on.
    """
    return get_general_config().get_chain_type()
