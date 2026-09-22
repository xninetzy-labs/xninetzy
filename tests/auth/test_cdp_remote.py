from __future__ import annotations

from typing import Any

import pytest

from xninetzy.os.auth.browser.gateway import (
    BrowserGatewayUnavailable,
    CDPBackend,
    RemotePlaywrightBackend,
    _validate_endpoint,
    active_external_handles,
    close_external_browser,
)


def test_validate_endpoint_rejects_empty() -> None:
    with pytest.raises(BrowserGatewayUnavailable):
        _validate_endpoint("")


def test_validate_endpoint_rejects_javascript() -> None:
    with pytest.raises(Exception):
        _validate_endpoint("javascript:alert(1)")


def test_cdp_backend_unavailable_without_endpoint(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "xninetzy.os.auth.browser.gateway.get_settings",
        lambda: type("S", (), {"XNINETZY_BROWSER_CDP_ENDPOINT": ""})(),
    )
    backend = CDPBackend()
    assert backend.is_available() is False
    snap = backend.capability_snapshot()
    assert snap["backend"] == "cdp"


def test_remote_backend_unavailable_without_endpoint(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "xninetzy.os.auth.browser.gateway.get_settings",
        lambda: type("S", (), {"XNINETZY_BROWSER_REMOTE_ENDPOINT": ""})(),
    )
    backend = RemotePlaywrightBackend()
    assert backend.is_available() is False
    snap = backend.capability_snapshot()
    assert snap["backend"] == "remote"


def test_active_external_handles_returns_safe_summary() -> None:
    summary = active_external_handles()
    assert isinstance(summary, dict)


def test_close_external_browser_returns_false_for_unknown() -> None:
    import asyncio

    closed = asyncio.run(close_external_browser(session_id="nope"))
    assert closed is False
