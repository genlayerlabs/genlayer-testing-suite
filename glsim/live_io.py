"""Live I/O handlers for glsim.

Provides real web and LLM handlers that replace mocks when running
contracts in simulator mode.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional


def create_web_handler(use_browser: bool = True) -> Callable:
    """Create a handler that makes real HTTP/browser requests.

    Args:
        use_browser: If True, use Playwright for browser-rendered pages.
                     Falls back to httpx if Playwright is not installed.

    Returns:
        A callable that takes web_data dict and returns wasi-format response.
    """
    # Lazy-init state shared across calls
    state: Dict[str, Any] = {"browser": None, "context": None, "httpx_client": None}

    _has_playwright = True
    if use_browser:
        try:
            import playwright.sync_api  # noqa: F401
        except ImportError:
            _has_playwright = False

    def _get_httpx():
        if state["httpx_client"] is None:
            import httpx
            state["httpx_client"] = httpx.Client(timeout=30, follow_redirects=True)
        return state["httpx_client"]

    def _get_browser():
        if state["browser"] is None:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            state["_pw"] = pw
            state["browser"] = pw.chromium.launch(headless=True)
            state["context"] = state["browser"].new_context()
        return state["context"]

    def _browser_fetch(url: str) -> Dict:
        ctx = _get_browser()
        page = ctx.new_page()
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            status = resp.status if resp else 200
            body = page.inner_text("body")
            return {
                "status": status,
                "headers": {},
                "body": body.encode("utf-8"),
            }
        finally:
            page.close()

    def _httpx_fetch(url: str, method: str, headers: dict, body: bytes | None) -> Dict:
        client = _get_httpx()
        resp = client.request(method, url, headers=headers, content=body)
        return {
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.content,
        }

    def handler(data: Any) -> Dict:
        url = data.get("url", "")
        method = data.get("method", "GET")
        headers = data.get("headers", {})
        req_body = data.get("body")
        if isinstance(req_body, str):
            req_body = req_body.encode("utf-8")

        try:
            if use_browser and _has_playwright and method.upper() == "GET":
                resp = _browser_fetch(url)
            else:
                resp = _httpx_fetch(url, method, headers, req_body)

            return {"ok": {"response": resp}}
        except Exception as exc:
            # Return error as a failed HTTP response rather than crashing
            return {"ok": {"response": {
                "status": 502,
                "headers": {},
                "body": f"live_io web error: {exc}".encode("utf-8"),
            }}}

    return handler


def create_llm_handler(provider_config: str | None = None) -> Callable:
    """Create a handler that calls real LLM APIs.

    Args:
        provider_config: Format "provider:model", e.g. "openai:gpt-4o".
                         Defaults to "openai:gpt-4o-mini".

    Returns:
        A callable that takes prompt_data dict and returns wasi-format response.
    """
    config = provider_config or "openai:gpt-4o-mini"
    parts = config.split(":", 1)
    provider = parts[0]
    model = parts[1] if len(parts) > 1 else "gpt-4o-mini"

    # Lazy-init httpx client
    state: Dict[str, Any] = {"client": None}

    def _get_client():
        if state["client"] is None:
            import httpx
            state["client"] = httpx.Client(timeout=120)
        return state["client"]

    def _call_openai(prompt: str, response_format: Optional[str] = None) -> Any:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        client = _get_client()
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        resp = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]

        if response_format == "json":
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                pass
        return text

    def _call_anthropic(prompt: str, response_format: Optional[str] = None) -> Any:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        client = _get_client()
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        resp = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["content"][0]["text"]

        if response_format == "json":
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                pass
        return text

    callers = {
        "openai": _call_openai,
        "anthropic": _call_anthropic,
    }

    def handler(data: Any) -> Dict:
        prompt = data.get("prompt", "")
        config_data = data.get("config", {}) or {}
        response_format = config_data.get("response_format")

        caller = callers.get(provider)
        if caller is None:
            return {"ok": f"Unsupported LLM provider: {provider}"}

        try:
            result = caller(prompt, response_format)
            return {"ok": result}
        except Exception as exc:
            return {"ok": f"live_io LLM error: {exc}"}

    return handler
