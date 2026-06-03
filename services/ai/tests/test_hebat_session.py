"""Unit tests for HEBAT session healing (redirect-loop / expired-cookie relogin).

These run fully offline — httpx, relogin and the rate-limit sleep are mocked, so
no live HEBAT account or browser is required.
"""

from __future__ import annotations

from collections import deque

import httpx
import pytest

from app.tools.hebat import moodle_client
from app.tools.hebat.parsers import is_login_redirect, looks_like_login_page


# ─── detection helpers ───────────────────────────────────────────────────────

def test_is_login_redirect_detects_login_and_loginredirect():
    assert is_login_redirect("https://hebat.elearning.unair.ac.id/login/index.php")
    assert is_login_redirect("/login/index.php?loginredirect=1")
    assert is_login_redirect("/login/index.php")
    assert not is_login_redirect("/course/view.php?id=10")
    assert not is_login_redirect("")
    assert not is_login_redirect(None)


def test_looks_like_login_page_requires_form_not_stray_link():
    login_html = '<form><input name="logintoken" value="x"><input name="username"></form>'
    assert looks_like_login_page(login_html)
    # A normal page that merely links to login must NOT be treated as logged out.
    normal = '<a href="/login/index.php">Log in</a><div class="course-content">Week 1</div>'
    assert not looks_like_login_page(normal)
    assert looks_like_login_page("") is False


# ─── _get harness ────────────────────────────────────────────────────────────

class _FakeResp:
    def __init__(self, status_code: int, *, location: str | None = None, text: str = ""):
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        if location is not None:
            self.headers["location"] = location
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)  # type: ignore[arg-type]


class _FakeClient:
    """Async-context httpx stand-in that serves a programmed response queue."""

    queue: deque = deque()
    constructed_kwargs: list[dict] = []
    get_calls: list[tuple[str, bool]] = []

    def __init__(self, **kwargs):
        _FakeClient.constructed_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, follow_redirects: bool = False):
        _FakeClient.get_calls.append((url, follow_redirects))
        item = _FakeClient.queue.popleft() if _FakeClient.queue else _FakeResp(
            302, location="/login/index.php?loginredirect=1"
        )
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def patched(monkeypatch):
    """Wire moodle_client to the fake client, fake cookies, fake relogin, no sleep."""
    _FakeClient.queue = deque()
    _FakeClient.constructed_kwargs = []
    _FakeClient.get_calls = []
    relogin_counter = {"n": 0, "result": True}

    async def fake_cookies(_chat_id):
        return [{"name": "MoodleSession", "value": "stale"}]

    async def fake_relogin(_chat_id):
        relogin_counter["n"] += 1
        return relogin_counter["result"]

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(moodle_client, "httpx", _make_httpx_module())
    monkeypatch.setattr(moodle_client, "get_cookies_for_httpx", fake_cookies)
    monkeypatch.setattr(moodle_client, "relogin_hebat", fake_relogin)
    monkeypatch.setattr(moodle_client.asyncio, "sleep", no_sleep)
    return relogin_counter


def _make_httpx_module():
    """A shim exposing AsyncClient=_FakeClient plus the real exception types."""
    import types

    shim = types.SimpleNamespace()
    shim.AsyncClient = _FakeClient
    shim.TooManyRedirects = httpx.TooManyRedirects
    shim.HTTPStatusError = httpx.HTTPStatusError
    return shim


@pytest.mark.asyncio
async def test_redirect_to_login_triggers_relogin_then_retries(patched):
    _FakeClient.queue = deque([
        _FakeResp(302, location="/login/index.php?loginredirect=1"),  # stale cookie
        _FakeResp(200, text="<div class='course-content'>Week 1</div>"),  # after relogin
    ])
    html = await moodle_client._get("628xxx", "https://h/course/view.php?id=10")
    assert html is not None and "course-content" in html
    assert patched["n"] == 1  # relogged in exactly once


@pytest.mark.asyncio
async def test_no_infinite_redirect_uses_follow_false(patched):
    _FakeClient.queue = deque([
        _FakeResp(302, location="/login/index.php"),
        _FakeResp(200, text="ok"),
    ])
    await moodle_client._get("628xxx", "https://h/mod/assign/view.php?id=1")
    # First request must NOT auto-follow redirects (that was the loop's cause).
    assert _FakeClient.constructed_kwargs[0]["follow_redirects"] is False


@pytest.mark.asyncio
async def test_relogin_capped_no_infinite_loop(patched):
    # Always bounce to login; relogin always "succeeds" but page stays expired.
    _FakeClient.queue = deque()  # empty → fake serves login redirect forever
    html = await moodle_client._get("628xxx", "https://h/mod/assign/view.php?id=1")
    assert html is None
    # HEBAT_SESSION_MAX_RELOGIN defaults to 2 → at most 2 relogin attempts.
    assert patched["n"] == 2


@pytest.mark.asyncio
async def test_too_many_redirects_is_treated_as_expired(patched):
    _FakeClient.queue = deque([
        httpx.TooManyRedirects("loop"),
        _FakeResp(200, text="recovered"),
    ])
    html = await moodle_client._get("628xxx", "https://h/course/view.php?id=10")
    assert html == "recovered"
    assert patched["n"] == 1


@pytest.mark.asyncio
async def test_login_form_in_body_triggers_relogin(patched):
    _FakeClient.queue = deque([
        _FakeResp(200, text='<form><input name="logintoken" value="x"></form>'),
        _FakeResp(200, text="<div>real page</div>"),
    ])
    html = await moodle_client._get("628xxx", "https://h/course/view.php?id=10")
    assert html == "<div>real page</div>"
    assert patched["n"] == 1


@pytest.mark.asyncio
async def test_relogin_failure_returns_none_not_silent_retry(patched):
    patched["result"] = False  # credentials missing / login rejected
    _FakeClient.queue = deque([_FakeResp(302, location="/login/index.php")])
    html = await moodle_client._get("628xxx", "https://h/course/view.php?id=10")
    assert html is None
    assert patched["n"] == 1
