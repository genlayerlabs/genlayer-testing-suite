"""Unit tests for direct-runner GenVM version and artifact resolution."""

import json
import urllib.error

from gltest.direct import sdk_loader


class _FakeResponse:
    """Minimal context-manager stand-in for urllib's HTTP response."""

    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class TestResolveVersion:
    """resolve_version() precedence: env var > cache > latest release."""

    def test_env_var_takes_precedence(self, monkeypatch):
        monkeypatch.setenv(sdk_loader.GENVM_VERSION_ENV, "v1.2.3")
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.2.16"])
        monkeypatch.setattr(sdk_loader, "get_latest_version", lambda: "v0.9.9")

        assert sdk_loader.resolve_version() == "v1.2.3"

    def test_falls_back_to_newest_cached_version(self, monkeypatch):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.2.16"])
        monkeypatch.setattr(sdk_loader, "get_latest_version", lambda: "v0.9.9")

        assert sdk_loader.resolve_version() == "v0.2.16"

    def test_falls_back_to_latest_when_no_cache(self, monkeypatch):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: [])
        monkeypatch.setattr(sdk_loader, "get_latest_version", lambda: "v0.9.9")

        assert sdk_loader.resolve_version() == "v0.9.9"


class TestGetLatestVersion:
    """get_latest_version() skips pre-releases and assetless releases."""

    def test_skips_releases_without_a_bundle_asset(self, monkeypatch):
        releases = [
            {"tag_name": "v0.9.9", "prerelease": False, "assets": [
                {"name": "genvm-linux-amd64.tar.xz"},
            ]},
            {"tag_name": "v0.2.16", "prerelease": False, "assets": [
                {"name": "genvm-universal.tar.xz"},
            ]},
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_accepts_renamed_runners_all_asset(self, monkeypatch):
        releases = [
            {"tag_name": "v0.3.0", "prerelease": False, "assets": [
                {"name": "genvm-runners-all.tar.xz"},
            ]},
            {"tag_name": "v0.2.16", "prerelease": False, "assets": [
                {"name": "genvm-universal.tar.xz"},
            ]},
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.3.0"

    def test_skips_prereleases(self, monkeypatch):
        releases = [
            {"tag_name": "v0.3.0-rc0", "prerelease": True, "assets": [
                {"name": "genvm-runners-all.tar.xz"},
            ]},
            {"tag_name": "v0.2.16", "prerelease": False, "assets": [
                {"name": "genvm-universal.tar.xz"},
            ]},
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_returns_fallback_when_api_unreachable(self, monkeypatch, capsys):
        def _boom(*a, **k):
            raise OSError("network down")

        monkeypatch.setattr("urllib.request.urlopen", _boom)

        assert sdk_loader.get_latest_version() == sdk_loader.FALLBACK_VERSION
        assert "could not resolve latest GenVM version" in capsys.readouterr().err


class TestListCachedVersions:
    """list_cached_versions() orders versions numerically, newest first."""

    def test_orders_versions_numerically(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        for version in ("v0.2.9", "v0.2.16", "v0.10.0"):
            (tmp_path / f"genvm-universal-{version}.tar.xz").write_bytes(b"")

        assert sdk_loader.list_cached_versions() == ["v0.10.0", "v0.2.16", "v0.2.9"]


class TestDownloadArtifacts:
    """download_artifacts() resolves whichever bundle asset a release ships."""

    @staticmethod
    def _http_404(url):
        return urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    def test_returns_cached_tarball_without_downloading(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        cached = tmp_path / "genvm-universal-v0.2.16.tar.xz"
        cached.write_bytes(b"cached")

        def _fail(*a, **k):
            raise AssertionError("should not download a cached tarball")

        monkeypatch.setattr(sdk_loader, "_download_to", _fail)

        assert sdk_loader.download_artifacts("v0.2.16") == cached

    def test_uses_first_available_asset(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        tried = []

        def _download(url, dest):
            tried.append(url)
            dest.write_bytes(b"bundle")

        monkeypatch.setattr(sdk_loader, "_download_to", _download)

        result = sdk_loader.download_artifacts("v0.3.0")

        assert result == tmp_path / "genvm-universal-v0.3.0.tar.xz"
        assert result.read_bytes() == b"bundle"
        assert tried == [
            f"{sdk_loader.GITHUB_RELEASES_URL}/download/v0.3.0/genvm-runners-all.tar.xz"
        ]

    def test_falls_back_to_old_asset_on_404(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        tried = []

        def _download(url, dest):
            tried.append(url)
            if url.endswith("genvm-runners-all.tar.xz"):
                raise self._http_404(url)
            dest.write_bytes(b"bundle")

        monkeypatch.setattr(sdk_loader, "_download_to", _download)

        result = sdk_loader.download_artifacts("v0.2.16")

        assert result.read_bytes() == b"bundle"
        assert [u.rsplit("/", 1)[-1] for u in tried] == list(
            sdk_loader.RUNNER_BUNDLE_ASSETS
        )

    def test_raises_when_no_asset_found(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)

        def _download(url, dest):
            raise self._http_404(url)

        monkeypatch.setattr(sdk_loader, "_download_to", _download)

        try:
            sdk_loader.download_artifacts("v9.9.9")
        except FileNotFoundError as e:
            assert "v9.9.9" in str(e)
        else:
            raise AssertionError("expected FileNotFoundError")
