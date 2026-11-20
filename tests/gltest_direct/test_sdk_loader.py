"""Unit tests for direct-runner GenVM version and artifact resolution."""

import io
import json
import urllib.error
import zipfile

import pytest

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
    """resolve_version() precedence: explicit > current release > cache fallback."""

    def test_env_var_takes_precedence(self, monkeypatch):
        monkeypatch.setenv(sdk_loader.GENVM_VERSION_ENV, "v1.2.3")
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.2.16"])
        monkeypatch.setattr(sdk_loader, "_query_latest_version", lambda: "v0.9.9")

        assert sdk_loader.resolve_version() == "v1.2.3"

    def test_current_release_wins_over_stale_cached_version(self, monkeypatch):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.2.16"])
        monkeypatch.setattr(sdk_loader, "_query_latest_version", lambda: "v0.6.0-rc3")

        assert sdk_loader.resolve_version() == "v0.6.0-rc3"

    def test_offline_falls_back_to_newest_cached_version(self, monkeypatch, capsys):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.6.0-rc0"])

        def _offline():
            raise OSError("network down")

        monkeypatch.setattr(sdk_loader, "_query_latest_version", _offline)

        assert sdk_loader.resolve_version() == "v0.6.0-rc0"
        assert "checking the local cache" in capsys.readouterr().err

    def test_offline_without_cache_uses_current_fallback(self, monkeypatch):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: [])
        monkeypatch.setattr(sdk_loader, "_query_latest_version", lambda: None)

        assert sdk_loader.resolve_version() == "v0.6.0-rc3"

    def test_falls_back_to_latest_when_no_cache(self, monkeypatch):
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: [])
        monkeypatch.setattr(sdk_loader, "_query_latest_version", lambda: "v0.9.9")

        assert sdk_loader.resolve_version() == "v0.9.9"


class TestQueryLatestVersionAuth:
    """The release lookup authenticates when a token is present."""

    def _capture(self, monkeypatch):
        seen = {}

        def fake_urlopen(req, *a, **k):
            seen["headers"] = dict(req.header_items())
            return _FakeResponse([])

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        return seen

    def test_sends_bearer_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        seen = self._capture(monkeypatch)
        sdk_loader._query_latest_version()
        assert seen["headers"]["Authorization"] == "Bearer tok"

    def test_falls_back_to_gh_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "ghtok")
        seen = self._capture(monkeypatch)
        sdk_loader._query_latest_version()
        assert seen["headers"]["Authorization"] == "Bearer ghtok"

    def test_anonymous_without_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        seen = self._capture(monkeypatch)
        sdk_loader._query_latest_version()
        assert "Authorization" not in seen["headers"]


class TestQueryLatestVersionTokenSafety:
    def test_token_not_forwarded_on_redirect(self, monkeypatch):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        seen = {}

        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                seen["target"] = self.headers.get("Authorization")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"[]")

            def log_message(self, *a):
                pass

        target = HTTPServer(("127.0.0.1", 0), Target)

        class Origin(BaseHTTPRequestHandler):
            def do_GET(self):
                seen["origin"] = self.headers.get("Authorization")
                self.send_response(302)
                self.send_header(
                    "Location", f"http://127.0.0.1:{target.server_port}/x"
                )
                self.end_headers()

            def log_message(self, *a):
                pass

        origin = HTTPServer(("127.0.0.1", 0), Origin)
        threads = [
            threading.Thread(target=s.serve_forever, daemon=True)
            for s in (origin, target)
        ]
        for t in threads:
            t.start()
        try:
            monkeypatch.setenv("GITHUB_TOKEN", "secret")
            monkeypatch.setattr(
                sdk_loader,
                "GITHUB_API_RELEASES",
                f"http://127.0.0.1:{origin.server_port}/releases",
            )
            sdk_loader._query_latest_version()
        finally:
            origin.shutdown()
            target.shutdown()
        assert seen["origin"] == "Bearer secret"
        assert seen["target"] is None


class TestQueryLatestVersionRejectedToken:
    def _urlopen(self, calls):
        releases = [
            {
                "tag_name": "v0.9.9",
                "prerelease": False,
                "assets": [{"name": "genvm-universal.tar.xz"}],
            }
        ]

        def fake(req, *a, **k):
            auth = dict(req.header_items()).get("Authorization")
            calls.append(auth)
            if auth:
                raise urllib.error.HTTPError(
                    req.full_url, 401, "Bad credentials", {}, None
                )
            return _FakeResponse(releases)

        return fake

    def test_retries_anonymously_on_401(self, monkeypatch):
        calls = []
        monkeypatch.setenv("GITHUB_TOKEN", "bad")
        monkeypatch.setattr("urllib.request.urlopen", self._urlopen(calls))
        assert sdk_loader._query_latest_version() == "v0.9.9"
        assert calls == ["Bearer bad", None]

    def test_resolve_prefers_release_over_cache_on_401(self, monkeypatch):
        calls = []
        monkeypatch.delenv(sdk_loader.GENVM_VERSION_ENV, raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "bad")
        monkeypatch.setattr(sdk_loader, "list_cached_versions", lambda: ["v0.6.0-rc0"])
        monkeypatch.setattr("urllib.request.urlopen", self._urlopen(calls))
        assert sdk_loader.resolve_version() == "v0.9.9"

    def test_non_401_errors_are_not_retried(self, monkeypatch):
        calls = []
        monkeypatch.setenv("GITHUB_TOKEN", "tok")

        def fake(req, *a, **k):
            calls.append(1)
            raise urllib.error.HTTPError(req.full_url, 403, "rate limit", {}, None)

        monkeypatch.setattr("urllib.request.urlopen", fake)
        with pytest.raises(urllib.error.HTTPError):
            sdk_loader._query_latest_version()
        assert len(calls) == 1


class TestGetLatestVersion:
    """get_latest_version() selects current RCs and skips unusable releases."""

    def test_skips_releases_without_a_bundle_asset(self, monkeypatch):
        releases = [
            {
                "tag_name": "v0.6.0-rc3",
                "prerelease": True,
                "assets": [{"name": sdk_loader.RUNNER_BUNDLE_ASSETS[0]}],
            },
            {
                "tag_name": "v0.2.16",
                "prerelease": False,
                "assets": [{"name": "genvm-universal.tar.xz"}],
            },
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_accepts_renamed_runners_all_asset(self, monkeypatch):
        releases = [
            {
                "tag_name": "v0.3.0",
                "prerelease": False,
                "assets": [{"name": "genvm-runners-all.tar.xz"}],
            },
            {
                "tag_name": "v0.2.16",
                "prerelease": False,
                "assets": [{"name": "genvm-universal.tar.xz"}],
            },
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.3.0"

    def test_skips_drafts_and_assetless_releases(self, monkeypatch):
        releases = [
            {
                "tag_name": "v0.6.0-rc4",
                "prerelease": True,
                "draft": True,
                "assets": [{"name": sdk_loader.RUNNER_BUNDLE_ASSETS[0]}],
            },
            {
                "tag_name": "v0.6.0-rc3",
                "prerelease": True,
                "assets": [],
            },
            {
                "tag_name": "v0.2.16",
                "prerelease": False,
                "assets": [{"name": "genvm-universal.tar.xz"}],
            },
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )

        assert sdk_loader.get_latest_version() == "v0.2.16"

    def test_uses_rc_when_no_stable_bundle_exists(self, monkeypatch):
        releases = [
            {
                "tag_name": "v0.6.0-rc3",
                "prerelease": True,
                "assets": [{"name": sdk_loader.RUNNER_BUNDLE_ASSETS[0]}],
            }
        ]
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **k: _FakeResponse(releases)
        )
        assert sdk_loader.get_latest_version() == "v0.6.0-rc3"

    def test_returns_fallback_when_api_unreachable(self, monkeypatch, capsys):
        def _boom(*a, **k):
            raise OSError("network down")

        monkeypatch.setattr("urllib.request.urlopen", _boom)

        assert sdk_loader.get_latest_version() == sdk_loader.FALLBACK_VERSION
        assert "could not resolve latest GenVM version" in capsys.readouterr().err


class TestListCachedVersions:
    """list_cached_versions() orders versions numerically, newest first."""

    def test_orders_versions_numerically(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path / "bundles-v2")
        sdk_loader.BUNDLE_CACHE_DIR.mkdir()
        for version in ("v0.2.9", "v0.2.16", "v0.10.0"):
            (
                sdk_loader.BUNDLE_CACHE_DIR / f"genvm-universal-{version}.tar.xz"
            ).write_bytes(b"")

        assert sdk_loader.list_cached_versions() == ["v0.10.0", "v0.2.16", "v0.2.9"]

    def test_ignores_legacy_root_cache(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path / "bundles-v2")
        sdk_loader.BUNDLE_CACHE_DIR.mkdir()
        (tmp_path / "genvm-universal-v0.6.0-rc0.tar.xz").write_bytes(b"legacy")
        (sdk_loader.BUNDLE_CACHE_DIR / "genvm-universal-v0.6.0-rc3.tar.xz").write_bytes(
            b"current"
        )

        assert sdk_loader.list_cached_versions() == ["v0.6.0-rc3"]


class TestDownloadArtifacts:
    """download_artifacts() resolves whichever bundle asset a release ships."""

    @staticmethod
    def _http_404(url):
        return urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    def test_returns_cached_tarball_without_downloading(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path)
        cached = tmp_path / "genvm-universal-v0.2.16.tar.xz"
        cached.write_bytes(b"cached")

        def _fail(*a, **k):
            raise AssertionError("should not download a cached tarball")

        monkeypatch.setattr(sdk_loader, "_download_to", _fail)

        assert sdk_loader.download_artifacts("v0.2.16") == cached

    def test_uses_first_available_asset(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path)
        tried = []

        def _download(url, dest):
            tried.append(url)
            dest.write_bytes(b"bundle")

        monkeypatch.setattr(sdk_loader, "_download_to", _download)

        result = sdk_loader.download_artifacts("v0.3.0")

        assert result == tmp_path / "genvm-universal-v0.3.0.tar.xz"
        assert result.read_bytes() == b"bundle"
        assert tried == [
            f"{sdk_loader.GITHUB_RELEASES_URL}/download/v0.3.0/{sdk_loader.RUNNER_BUNDLE_ASSETS[0]}"
        ]

    def test_falls_back_to_old_asset_on_404(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path)
        tried = []

        def _download(url, dest):
            tried.append(url)
            # 404 every asset except the last so the loop walks the full list.
            if not url.endswith(sdk_loader.RUNNER_BUNDLE_ASSETS[-1]):
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
        monkeypatch.setattr(sdk_loader, "BUNDLE_CACHE_DIR", tmp_path)

        def _download(url, dest):
            raise self._http_404(url)

        monkeypatch.setattr(sdk_loader, "_download_to", _download)

        try:
            sdk_loader.download_artifacts("v9.9.9")
        except FileNotFoundError as e:
            assert "v9.9.9" in str(e)
        else:
            raise AssertionError("expected FileNotFoundError")


class TestExtractLocalRunner:
    """Runner ZIP extraction cannot escape or poison the local cache."""

    @staticmethod
    def _runner_zip(root, members):
        archive = root / "runners" / "py-genlayer" / "ab" / "cd.zip"
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, mode="w") as bundle:
            for name, content in members.items():
                bundle.writestr(name, content)
        return archive

    def test_extracts_safe_runner_zip(self, monkeypatch, tmp_path):
        root = tmp_path / "prebuilt"
        self._runner_zip(root, {"runner.json": '{"Seq": []}'})
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", tmp_path / "cache")

        extracted = sdk_loader._extract_local_runner(root, "py-genlayer", "abcd")

        assert (extracted / "runner.json").read_text() == '{"Seq": []}'

    def test_rejects_zip_traversal_and_removes_partial_cache(
        self, monkeypatch, tmp_path
    ):
        root = tmp_path / "prebuilt"
        self._runner_zip(root, {"../escape.py": "unsafe"})
        cache = tmp_path / "cache"
        monkeypatch.setattr(sdk_loader, "CACHE_DIR", cache)

        with pytest.raises(ValueError, match="unsafe runner zip member"):
            sdk_loader._extract_local_runner(root, "py-genlayer", "abcd")

        assert not (cache / "extracted" / "local" / "py-genlayer" / "abcd").exists()
        assert not (
            cache / "extracted" / "local" / "py-genlayer" / "escape.py"
        ).exists()
