"""
SDK version loader for direct test runner.

Handles downloading and extracting the correct genlayer-py-std version
based on contract header dependencies, similar to genvm-linter.
"""

import os
import re
import sys
import json
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List

CACHE_DIR = Path.home() / ".cache" / "gltest-direct"
GITHUB_RELEASES_URL = "https://github.com/genlayerlabs/genvm/releases"

RUNNER_TYPE = "py-genlayer"
STD_LIB_TYPE = "py-lib-genlayer-std"
EMBEDDINGS_TYPE = "py-lib-genlayer-embeddings"
PROTOBUF_TYPE = "py-lib-protobuf"


def parse_contract_header(contract_path: Path) -> Dict[str, str]:
    """
    Parse contract file header to extract dependency hashes.

    Returns dict mapping dependency name to hash.
    """
    deps = {}
    with open(contract_path, "r") as f:
        content = f.read(2000)

    pattern = r'"Depends":\s*"([^:]+):([^"]+)"'
    for match in re.finditer(pattern, content):
        name, hash_val = match.groups()
        deps[name] = hash_val

    return deps


def get_latest_version() -> str:
    """Get latest genvm release version from GitHub."""
    try:
        req = urllib.request.Request(
            f"{GITHUB_RELEASES_URL}/latest",
            method="HEAD",
        )
        req.add_header("User-Agent", "gltest-direct")
        with urllib.request.urlopen(req, timeout=10) as resp:
            final_url = resp.url
            version = final_url.split("/")[-1]
            return version
    except Exception:
        return "v0.2.12"


def list_cached_versions() -> List[str]:
    """List all cached genvm versions."""
    if not CACHE_DIR.exists():
        return []

    versions = []
    for f in CACHE_DIR.glob("genvm-universal-*.tar.xz"):
        match = re.search(r"genvm-universal-(.+)\.tar\.xz", f.name)
        if match:
            versions.append(match.group(1))
    return sorted(versions, reverse=True)


def download_artifacts(version: str) -> Path:
    """Download genvm release tarball if not cached."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    tarball_name = f"genvm-universal-{version}.tar.xz"
    tarball_path = CACHE_DIR / tarball_name

    if tarball_path.exists():
        return tarball_path

    url = f"{GITHUB_RELEASES_URL}/download/{version}/genvm-universal.tar.xz"
    print(f"Downloading {url}...")

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "gltest-direct")

    with urllib.request.urlopen(req, timeout=300) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0

        with tempfile.NamedTemporaryFile(delete=False, dir=CACHE_DIR) as tmp:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded // 1024 // 1024}MB)", end="", flush=True)

            tmp_path = tmp.name

    print()
    os.rename(tmp_path, tarball_path)
    return tarball_path


def extract_runner(
    tarball_path: Path,
    runner_type: str,
    runner_hash: Optional[str] = None,
    version: Optional[str] = None,
) -> Path:
    """Extract a runner from the tarball."""
    if version is None:
        match = re.search(r"genvm-universal-(.+)\.tar\.xz", tarball_path.name)
        version = match.group(1) if match else "unknown"

    extract_base = CACHE_DIR / "extracted" / version / runner_type

    # Fast path: if hash specified and already extracted, skip tarball entirely
    if runner_hash and runner_hash.lower() != "latest":
        extract_dir = extract_base / runner_hash
        if extract_dir.exists():
            return extract_dir

    # Check if any version already extracted (for "latest" case)
    if extract_base.exists():
        existing = sorted(extract_base.iterdir(), reverse=True)
        if existing and (not runner_hash or runner_hash.lower() == "latest"):
            return existing[0]

    # Need to open tarball - this is slow (~13s for xz)
    with tarfile.open(tarball_path, "r:xz") as outer_tar:
        prefix = f"runners/{runner_type}/"
        runner_tars = [
            m.name for m in outer_tar.getmembers()
            if m.name.startswith(prefix) and m.name.endswith(".tar")
        ]

        if not runner_tars:
            raise ValueError(f"No {runner_type} runners found in tarball")

        # Treat "latest" as no specific hash
        if runner_hash and runner_hash.lower() != "latest":
            target = f"runners/{runner_type}/{runner_hash[:2]}/{runner_hash[2:]}.tar"
            if target not in runner_tars:
                raise ValueError(f"Runner hash {runner_hash} not found")
            runner_tar_name = target
            extract_dir = extract_base / runner_hash
        else:
            runner_tar_name = sorted(runner_tars)[-1]
            parts = runner_tar_name.split("/")
            runner_hash = parts[-2] + parts[-1].replace(".tar", "")
            extract_dir = extract_base / runner_hash

        if extract_dir.exists():
            return extract_dir

        inner_tar_file = outer_tar.extractfile(runner_tar_name)
        if inner_tar_file is None:
            raise ValueError(f"Failed to read {runner_tar_name}")

        extract_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(fileobj=inner_tar_file, mode="r:") as inner_tar:
            inner_tar.extractall(extract_dir, filter='data')

        return extract_dir


def parse_runner_manifest(runner_dir: Path) -> Dict[str, str]:
    """Parse runner.json to get transitive dependencies."""
    manifest_path = runner_dir / "runner.json"
    if not manifest_path.exists():
        return {}

    with open(manifest_path) as f:
        manifest = json.load(f)

    deps = {}
    seq = manifest.get("Seq", [])
    for item in seq:
        if "Depends" in item:
            dep = item["Depends"]
            if ":" in dep:
                name, hash_val = dep.split(":", 1)
                deps[name] = hash_val

    return deps


def setup_sdk_paths(
    contract_path: Optional[Path] = None,
    version: Optional[str] = None,
) -> List[Path]:
    """
    Setup sys.path with correct SDK versions for a contract.

    Returns list of paths added to sys.path.
    """
    contract_deps = {}
    if contract_path and contract_path.exists():
        contract_deps = parse_contract_header(contract_path)

    if version is None:
        cached = list_cached_versions()
        version = cached[0] if cached else get_latest_version()

    tarball = download_artifacts(version)

    runner_hash = contract_deps.get(RUNNER_TYPE)
    runner_dir = extract_runner(tarball, RUNNER_TYPE, runner_hash, version)

    runner_deps = parse_runner_manifest(runner_dir)

    std_hash = runner_deps.get(STD_LIB_TYPE)
    std_dir: Optional[Path] = None
    if std_hash:
        std_dir = extract_runner(tarball, STD_LIB_TYPE, std_hash, version)

    embeddings_hash = contract_deps.get(EMBEDDINGS_TYPE)
    embeddings_dir: Optional[Path] = None
    proto_dir: Optional[Path] = None
    if embeddings_hash:
        embeddings_dir = extract_runner(tarball, EMBEDDINGS_TYPE, embeddings_hash, version)
        proto_hash = runner_deps.get(PROTOBUF_TYPE)
        if proto_hash:
            proto_dir = extract_runner(tarball, PROTOBUF_TYPE, proto_hash, version)

    added_paths = []

    # Helper to add path - tries both 'src' subdirectory and direct directory
    def add_sdk_path(sdk_dir: Path) -> None:
        src_path = sdk_dir / "src"
        if src_path.exists():
            path_to_add = src_path
        else:
            path_to_add = sdk_dir

        if str(path_to_add) not in sys.path:
            sys.path.insert(0, str(path_to_add))
            added_paths.append(path_to_add)

    add_sdk_path(runner_dir)

    if std_dir:
        add_sdk_path(std_dir)

    if embeddings_dir:
        add_sdk_path(embeddings_dir)

    if proto_dir:
        add_sdk_path(proto_dir)

    return added_paths
