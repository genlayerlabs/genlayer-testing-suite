from unittest.mock import Mock

import pytest

from gltest.contracts.contract_factory import ContractFactory
from gltest.logging import logger


@pytest.fixture
def clients(monkeypatch):
    getters = []
    for name in ("get_gl_client", "get_gl_hosted_studio_client", "get_local_client"):
        getter = Mock()
        monkeypatch.setattr(f"gltest.contracts.contract_factory.{name}", getter)
        getters.append(getter)
    return getters


@pytest.mark.parametrize("successful_client", [0, 1, 2])
def test_schema_fallback_stops_at_first_success(clients, successful_client):
    factory = ContractFactory("Example", "class Example: pass")
    schema = {"methods": {}}
    for getter in clients:
        getter.return_value.get_contract_schema_for_code.side_effect = RuntimeError(
            "schema unavailable"
        )
    fetch = clients[successful_client].return_value.get_contract_schema_for_code
    fetch.side_effect = None
    fetch.return_value = schema

    assert factory._get_schema_with_fallback() is schema

    for getter in clients[: successful_client + 1]:
        getter.assert_called_once_with()
        getter.return_value.get_contract_schema_for_code.assert_called_once_with(
            contract_code=factory.contract_code
        )
    for getter in clients[successful_client + 1 :]:
        getter.assert_not_called()


def test_build_contract_reports_all_errors_without_logging(clients, monkeypatch):
    monkeypatch.setattr(logger, "disabled", True)
    errors = [
        RuntimeError("RPC method unavailable"),
        ValueError("invalid contract: missing annotation\nline 12"),
        ConnectionError("connection refused"),
    ]
    for getter, error in zip(clients, errors):
        getter.return_value.get_contract_schema_for_code.side_effect = error

    with pytest.raises(ValueError) as exc_info:
        ContractFactory("Example", "class Example: pass").build_contract("0x123")

    message = str(exc_info.value)
    assert "Failed to get schema from all clients" in message
    assert "contract 'Example'" in message
    for label, error in zip(("default", "hosted studio", "local"), errors):
        assert f"{label}: {type(error).__name__}: {error}" in message
    assert exc_info.value.__cause__ is errors[-1]


def test_client_initialization_and_missing_schema_allow_fallback(clients):
    clients[0].side_effect = RuntimeError("invalid configuration")
    clients[1].return_value.get_contract_schema_for_code.return_value = None
    schema = {"methods": {}}
    clients[2].return_value.get_contract_schema_for_code.return_value = schema

    assert ContractFactory("Example", "code")._get_schema_with_fallback() is schema


def test_initialization_and_missing_schema_errors_are_reported(clients):
    clients[0].side_effect = RuntimeError("invalid configuration")
    for getter in clients[1:]:
        getter.return_value.get_contract_schema_for_code.return_value = None

    with pytest.raises(ValueError) as exc_info:
        ContractFactory("Example", "code").build_contract("0x123")

    assert "default: RuntimeError: invalid configuration" in str(exc_info.value)
    for label in ("hosted studio", "local"):
        assert f"{label}: ValueError: Client returned no schema" in str(exc_info.value)
