import sys

from glsim import __main__ as cli_main
from glsim.state import DEFAULT_CHAIN_ID


def test_cli_chain_id_default(monkeypatch):
    import glsim.server as server

    captured = {}

    def fake_create_app(**kwargs):
        captured["kwargs"] = kwargs
        return "app"

    def fake_run_server(app, host, port):
        captured["run_server"] = {"app": app, "host": host, "port": port}

    monkeypatch.setattr(server, "create_app", fake_create_app)
    monkeypatch.setattr(server, "run_server", fake_run_server)
    monkeypatch.setattr(sys, "argv", ["glsim"])

    cli_main.main()

    assert captured["kwargs"]["chain_id"] == DEFAULT_CHAIN_ID


def test_cli_chain_id_override(monkeypatch):
    import glsim.server as server

    captured = {}

    def fake_create_app(**kwargs):
        captured["kwargs"] = kwargs
        return "app"

    def fake_run_server(app, host, port):
        captured["run_server"] = {"app": app, "host": host, "port": port}

    monkeypatch.setattr(server, "create_app", fake_create_app)
    monkeypatch.setattr(server, "run_server", fake_run_server)
    monkeypatch.setattr(sys, "argv", ["glsim", "--chain-id", "70001"])

    cli_main.main()

    assert captured["kwargs"]["chain_id"] == 70001
