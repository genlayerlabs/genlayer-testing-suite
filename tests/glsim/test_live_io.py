from __future__ import annotations

import sys
from types import SimpleNamespace

from glsim.live_io import _normalize_local_runtime_url, create_web_handler


def test_normalize_local_runtime_url_rewrites_docker_host_alias():
    url = "http://host.docker.internal:3340/api/twitter?x=1"
    normalized = _normalize_local_runtime_url(url)
    assert normalized == "http://127.0.0.1:3340/api/twitter?x=1"


def test_create_web_handler_rewrites_docker_host_alias_for_httpx(monkeypatch):
    captured: dict[str, str] = {}

    class _FakeResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"ok":true}'

    class _FakeClient:
        def __init__(self, timeout: int, follow_redirects: bool):
            assert timeout == 30
            assert follow_redirects is True

        def request(self, method: str, url: str, headers: dict, content: bytes | None):
            captured["method"] = method
            captured["url"] = url
            return _FakeResponse()

    monkeypatch.setitem(sys.modules, "httpx", SimpleNamespace(Client=_FakeClient))

    handler = create_web_handler(use_browser=False)
    result = handler(
        {
            "url": "http://host.docker.internal:3340/api/twitter",
            "method": "GET",
            "headers": {},
            "body": None,
        }
    )

    assert captured["method"] == "GET"
    assert captured["url"] == "http://127.0.0.1:3340/api/twitter"
    assert result["ok"]["response"]["status"] == 200
