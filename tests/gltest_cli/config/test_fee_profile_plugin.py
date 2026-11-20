from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from gltest_cli.config import plugin


def test_session_profile_uses_the_selected_runtime_chain_id(monkeypatch, tmp_path):
    output_path = tmp_path / "fees.json"
    general_config = SimpleNamespace(
        get_fee_profile_path=Mock(return_value=output_path),
        get_network_name=Mock(return_value="preview"),
        get_fee_profile_headroom=Mock(return_value=1.25),
        get_chain=Mock(return_value=SimpleNamespace(id=61997)),
    )
    collector = SimpleNamespace(
        write=Mock(return_value={"methods": {"create_bet": {}}}),
        has_observations=Mock(return_value=True),
    )
    monkeypatch.setattr(plugin, "get_general_config", lambda: general_config)
    monkeypatch.setattr(plugin, "get_fee_profile_collector", lambda: collector)

    plugin.pytest_sessionfinish(session=None, exitstatus=0)

    collector.write.assert_called_once_with(
        path=Path(output_path),
        network="preview",
        headroom=1.25,
        chain_id=61997,
    )
