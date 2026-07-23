"""
SDK version loader for direct test runner.

Handles downloading and extracting the correct genlayer-py-std version
based on contract header dependencies, similar to genvm-linter.
"""

import os
import re
import sys
import json
import shutil
import tarfile
import platform
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List

CACHE_DIR = Path.home() / ".cache" / "gltest-direct"
GITHUB_RELEASES_URL = "https://github.com/genlayerlabs/genvm-manager/releases"
GITHUB_API_RELEASES = "https://api.github.com/repos/genlayerlabs/genvm-manager/releases"


def _host_release_asset() -> str:
    """genvm-manager (v0.6+) ships a whole-tree tarball per platform, named
    genvm-<arch>-<os>.tar.xz — pick the one matching this host."""
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
    os_name = "macos" if platform.system().lower() == "darwin" else "linux"
    return f"genvm-{arch}-{os_name}.tar.xz"


# Download candidates, newest-scheme first: the genvm-manager per-platform whole
# tree, then the pre-v0.6 runner-only bundles (genvm-runners-all → genvm-universal).
RUNNER_BUNDLE_ASSETS = (
    _host_release_asset(),
    "genvm-runners-all.tar.xz",
    "genvm-universal.tar.xz",
)
GENVM_VERSION_ENV = "GENVM_VERSION"
FALLBACK_VERSION = "v0.6.0-rc0"

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
    """Newest non-prerelease GenVM release that ships a known runner bundle."""
    try:
        req = urllib.request.Request(
            f"{GITHUB_API_RELEASES}?per_page=100",
            headers={
                "User-Agent": "gltest-direct",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            releases = json.loads(resp.read().decode("utf-8"))
        for release in releases:
            if release.get("prerelease") or release.get("draft"):
                continue
            asset_names = {asset.get("name") for asset in release.get("assets", [])}
            if asset_names.intersection(RUNNER_BUNDLE_ASSETS):
                return release["tag_name"]
    except Exception as exc:
        print(
            f"Warning: could not resolve latest GenVM version ({exc}); "
            f"falling back to {FALLBACK_VERSION}",
            file=sys.stderr,
        )
    return FALLBACK_VERSION


def resolve_version() -> str:
    """GenVM version to use: GENVM_VERSION env var > newest cached > latest release."""
    pinned = os.environ.get(GENVM_VERSION_ENV)
    if pinned:
        return pinned
    cached = list_cached_versions()
    if cached:
        return cached[0]
    return get_latest_version()


def _version_sort_key(version: str) -> tuple:
    """Numeric-component sort key so v0.2.16 ranks above v0.2.9."""
    return tuple(int(n) for n in re.findall(r"\d+", version))


def list_cached_versions() -> List[str]:
    """List all cached genvm versions, newest first."""
    if not CACHE_DIR.exists():
        return []

    versions = []
    for f in CACHE_DIR.glob("genvm-universal-*.tar.xz"):
        match = re.search(r"genvm-universal-(.+)\.tar\.xz", f.name)
        if match:
            versions.append(match.group(1))
    return sorted(versions, key=_version_sort_key, reverse=True)


def _download_to(url: str, dest: Path) -> None:
    """Stream url to dest, replacing it atomically on success."""
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
    os.rename(tmp_path, dest)


def download_artifacts(version: str) -> Path:
    """Download the GenVM runner bundle for version if not cached."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    tarball_path = CACHE_DIR / f"genvm-universal-{version}.tar.xz"
    if tarball_path.exists():
        return tarball_path

    last_error: Optional[Exception] = None
    for asset in RUNNER_BUNDLE_ASSETS:
        url = f"{GITHUB_RELEASES_URL}/download/{version}/{asset}"
        try:
            _download_to(url, tarball_path)
            return tarball_path
        except urllib.error.HTTPError as e:
            if e.code == 404:
                last_error = e
                continue
            raise

    raise FileNotFoundError(
        f"No GenVM runner bundle for {version}; tried {', '.join(RUNNER_BUNDLE_ASSETS)}"
    ) from last_error


def _extract_local_runner(
    root: Path, runner_type: str, runner_hash: Optional[str]
) -> Path:
    """Extract a runner from a local prebuilt GenVM tree (GENVM_PREBUILT_DIR); globs
    any *runners* dir so runners/ and executor/<ver>/legacy-runners/ both match."""
    sub = (
        f"{runner_hash[:2]}/{runner_hash[2:]}.tar"
        if runner_hash and runner_hash.lower() != "latest"
        else "*/*.tar"
    )
    hits = sorted(root.glob(f"**/*runners*/{runner_type}/{sub}"))
    if not hits:
        raise FileNotFoundError(f"runner {runner_type}:{runner_hash} not under {root}")
    tar = hits[-1]
    dest = CACHE_DIR / "extracted" / "local" / runner_type / (tar.parent.name + tar.stem)
    if not dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar, "r:") as inner:
            inner.extractall(dest, filter="data")
    return dest


def _extract_release_tree(tarball_path: Path, version: str) -> Path:
    """Unpack a downloaded GenVM release tarball once (cached) into a local tree.

    genvm-manager ships the whole tree (bin/ lib/ runners/ executor/…), not a
    runner-only bundle, so we unpack it to a directory that looks exactly like a
    GENVM_PREBUILT_DIR and then resolve runners through the same globbing path.
    """
    tree = CACHE_DIR / "trees" / version
    if (tree / ".extracted").exists():
        return tree
    trees = CACHE_DIR / "trees"
    trees.mkdir(parents=True, exist_ok=True)
    # Extract into a process-unique dir, mark it complete, then publish with an
    # atomic rename. Concurrent cold-cache extractions each use their own tmp and
    # race only on the final rename; the loser sees the winner's finished tree.
    tmp = Path(tempfile.mkdtemp(dir=trees, prefix=f".{version}."))
    try:
        with tarfile.open(tarball_path, "r:xz") as outer:
            outer.extractall(tmp, filter="data")
        (tmp / ".extracted").touch()
        os.replace(tmp, tree)
    except OSError:
        shutil.rmtree(tmp, ignore_errors=True)
        if (tree / ".extracted").exists():
            return tree  # another extraction published first
        raise
    return tree


def extract_runner(
    tarball_path: Path,
    runner_type: str,
    runner_hash: Optional[str] = None,
    version: Optional[str] = None,
) -> Path:
    """Resolve a runner dir from a local prebuilt tree or a downloaded release."""
    prebuilt = os.environ.get("GENVM_PREBUILT_DIR")
    if prebuilt:
        return _extract_local_runner(Path(prebuilt), runner_type, runner_hash)
    if version is None:
        match = re.search(r"genvm-universal-(.+)\.tar\.xz", tarball_path.name)
        version = match.group(1) if match else "unknown"
    tree = _extract_release_tree(tarball_path, version)
    return _extract_local_runner(tree, runner_type, runner_hash)


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

    prebuilt = os.environ.get("GENVM_PREBUILT_DIR")
    if version is None and not prebuilt:
        version = resolve_version()

    tarball = None if prebuilt else download_artifacts(version)

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
