"""Regression tests for high-confidence defects found on v0.30-dev.

These tests are intentionally red until the corresponding production defects
are fixed.
"""

from __future__ import annotations

import io
import json
import sys
import tarfile
from pathlib import Path

import pytest
import rlp

from genlayer_py.abi import calldata
from gltest.direct import sdk_loader


STORAGE_CONTRACT = str(
    Path(__file__).parent / "examples" / "contracts" / "storage.py"
)


@pytest.fixture
def glsim_client():
    from glsim.server import create_app
    from starlette.testclient import TestClient

    app = create_app(
        num_validators=1,
        llm_provider=None,
        use_browser=False,
        verbose=True,
    )
    with TestClient(app) as client:
        yield client


def _rpc(client, method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "id": 1}
    if params is not None:
        payload["params"] = params
    response = client.post("/api", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "error" not in body, body.get("error")
    return body["result"]


def _deploy_storage(client, initial_value):
    return _rpc(
        client,
        "sim_deploy",
        {"code_path": STORAGE_CONTRACT, "args": [initial_value]},
    )["contract_address"]


def _sdk_write_request(address, value):
    encoded_call = calldata.encode(
        {"method": "update_storage", "args": [value], "kwargs": {}}
    )
    return {
        "to": address,
        "from": "0x1111111111111111111111111111111111111111",
        "data": "0x" + rlp.encode([encoded_call, b"\x00"]).hex(),
    }


def test_fee_estimation_does_not_persist_the_simulated_write(glsim_client):
    address = _deploy_storage(glsim_client, "before")

    _rpc(
        glsim_client,
        "sim_estimateTransactionFees",
        [_sdk_write_request(address, "simulated")],
    )

    read = _rpc(
        glsim_client,
        "sim_read",
        {"to": address, "method": "get_storage"},
    )
    assert read["result"] == "before"


def test_restore_snapshot_reverts_existing_contract_storage(glsim_client):
    address = _deploy_storage(glsim_client, "before")
    snapshot_id = _rpc(glsim_client, "sim_createSnapshot")

    _rpc(
        glsim_client,
        "sim_call",
        {
            "to": address,
            "method": "update_storage",
            "args": ["after"],
        },
    )
    _rpc(glsim_client, "sim_restoreSnapshot", [snapshot_id])

    read = _rpc(
        glsim_client,
        "sim_read",
        {"to": address, "method": "get_storage"},
    )
    assert read["result"] == "before"


def test_setup_sdk_paths_loads_protobuf_from_embeddings_manifest(
    monkeypatch, tmp_path
):
    contract = tmp_path / "contract.py"
    contract.write_text(
        '# {"Depends": "py-lib-genlayer-embeddings:embedhash"}\n',
        encoding="utf-8",
    )
    runner_dir = tmp_path / "runner"
    std_dir = tmp_path / "std"
    embeddings_dir = tmp_path / "embeddings"
    protobuf_dir = tmp_path / "protobuf"
    for path in (runner_dir, std_dir, embeddings_dir, protobuf_dir):
        path.mkdir()

    directories = {
        sdk_loader.RUNNER_TYPE: runner_dir,
        sdk_loader.STD_LIB_TYPE: std_dir,
        sdk_loader.EMBEDDINGS_TYPE: embeddings_dir,
        sdk_loader.PROTOBUF_TYPE: protobuf_dir,
    }

    def fake_extract(_tarball, runner_type, runner_hash=None, version=None):
        return directories[runner_type]

    def fake_manifest(path):
        if path == runner_dir:
            return {sdk_loader.STD_LIB_TYPE: "stdhash"}
        if path == embeddings_dir:
            return {sdk_loader.PROTOBUF_TYPE: "protohash"}
        return {}

    monkeypatch.setenv("GENVM_PREBUILT_DIR", str(tmp_path / "prebuilt"))
    monkeypatch.setattr(sdk_loader, "extract_runner", fake_extract)
    monkeypatch.setattr(sdk_loader, "parse_runner_manifest", fake_manifest)
    monkeypatch.setattr(sys, "path", list(sys.path))

    added = sdk_loader.setup_sdk_paths(contract)

    assert protobuf_dir in added


def test_release_tree_recovers_from_an_incomplete_cached_extraction(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path / "cache")
    version = "v0.6.0"
    stale_tree = sdk_loader.CACHE_DIR / "trees" / version
    stale_tree.mkdir(parents=True)
    (stale_tree / "partial-download").write_text("incomplete", encoding="utf-8")

    tarball = tmp_path / "bundle.tar.xz"
    payload = b"complete"
    with tarfile.open(tarball, "w:xz") as archive:
        info = tarfile.TarInfo("payload")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    tree = sdk_loader._extract_release_tree(tarball, version)

    assert (tree / ".extracted").is_file()
    assert (tree / "payload").read_bytes() == payload
    assert not (tree / "partial-download").exists()
