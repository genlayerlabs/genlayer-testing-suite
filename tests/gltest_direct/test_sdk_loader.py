"""Unit tests for direct-runner GenVM version resolution."""

import json

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

    def test_skips_releases_without_universal_asset(self, monkeypatch):
        releases = [
            {"tag_name": "v0.3.0-rc0", "prerelease": False, "assets": [
                {"name": "genvm-linux-amd64.tar.xz"},
            ]},
            {"tag_name": "v0.2.16", "prerelease": False, "assets": [
                {"name": sdk_loader.UNIVERSAL_ASSET},
            ]},
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_skips_prereleases(self, monkeypatch):
        releases = [
            {"tag_name": "v0.3.0-rc0", "prerelease": True, "assets": [
                {"name": sdk_loader.UNIVERSAL_ASSET},
            ]},
            {"tag_name": "v0.2.16", "prerelease": False, "assets": [
                {"name": sdk_loader.UNIVERSAL_ASSET},
            ]},
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_returns_fallback_when_api_unreachable(self, monkeypatch):
        def _boom(*a, **k):
            raise OSError("network down")

        monkeypatch.setattr("urllib.request.urlopen", _boom)

        assert sdk_loader.get_latest_version() == sdk_loader.FALLBACK_VERSION
