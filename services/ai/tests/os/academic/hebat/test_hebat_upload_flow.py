from __future__ import annotations

import pytest

from app.xninetzy.os.academic.hebat import browser_session, submission
from app.xninetzy.os.academic.hebat.submission import (
    _classify_removal,
    _classify_upload,
    _open_healed_page,
)

LOGGED_OUT_HTML = '<html><a href="/login/index.php">Log in</a></html>'
VALID_HTML = '<html><div class="course-content">Week 1</div></html>'


class _FakePage:
    def __init__(self, html: str):
        self.html = html
        self.gotos: list[str] = []

    async def goto(self, url, **kwargs):
        self.gotos.append(url)

    async def content(self) -> str:
        return self.html


class _FakeCtx:
    def __init__(self, page: _FakePage):
        self.page = page

    async def new_page(self) -> _FakePage:
        return self.page

    async def close(self):
        pass


class _FakeBrowser:
    def __init__(self, pages: list[_FakePage]):
        self._pages = list(pages)
        self.context_count = 0

    async def new_context(self, storage_state=None) -> _FakeCtx:
        self.context_count += 1
        page = self._pages.pop(0) if self._pages else _FakePage(VALID_HTML)
        return _FakeCtx(page)


def test_classify_upload_success_only_when_submitted():
    ok, text = _classify_upload(
        {"submission_status": "Submitted for grading", "last_modified": "Monday, 24 August 2026"}
    )
    assert ok is True
    assert "Submitted for grading" in text


def test_classify_upload_rejects_no_submission():
    ok, text = _classify_upload({"submission_status": "No submissions have been made yet"})
    assert ok is False
    assert "belum terkirim" in text


def test_classify_upload_rejects_draft():
    ok, _ = _classify_upload({"submission_status": "Draft (not submitted)"})
    assert ok is False


def test_classify_upload_rejects_unverifiable_page():
    ok, text = _classify_upload({})
    assert ok is False
    assert "memverifikasi" in text


def test_classify_removal_requires_explicit_no_submission():
    ok, _ = _classify_removal({"submission_status": "No submissions have been made yet"})
    assert ok is True


def test_classify_removal_never_treats_parse_failure_as_removed():
    ok, text = _classify_removal({"submission_status": None})
    assert ok is False
    assert "tidak terbaca" in text


def test_classify_removal_rejects_still_submitted():
    ok, _ = _classify_removal({"submission_status": "Submitted for grading"})
    assert ok is False


def _patch_session_env(monkeypatch, tmp_path, relogin_results: list[bool]):
    state_file = tmp_path / "storage_state.json"
    state_file.write_text("{}")
    monkeypatch.setattr(browser_session, "_storage_state_path", lambda chat_id: state_file)
    calls = {"n": 0}

    async def fake_relogin(_chat_id):
        result = relogin_results[min(calls["n"], len(relogin_results) - 1)]
        calls["n"] += 1
        return result

    monkeypatch.setattr(browser_session, "relogin_hebat", fake_relogin)
    return calls


@pytest.mark.asyncio
async def test_open_page_valid_on_first_attempt(monkeypatch, tmp_path):
    _patch_session_env(monkeypatch, tmp_path, [])
    browser = _FakeBrowser([_FakePage(VALID_HTML)])
    page, err = await _open_healed_page(browser, "chat", "https://h/mod/assign/view.php?id=1")
    assert err is None
    assert page.gotos == ["https://h/mod/assign/view.php?id=1"]
    assert browser.context_count == 1


@pytest.mark.asyncio
async def test_open_page_heals_expired_session_once(monkeypatch, tmp_path):
    calls = _patch_session_env(monkeypatch, tmp_path, [True])
    browser = _FakeBrowser([_FakePage(LOGGED_OUT_HTML), _FakePage(VALID_HTML)])
    page, err = await _open_healed_page(browser, "chat", "https://h/mod/assign/view.php?id=1")
    assert err is None
    assert calls["n"] == 1
    assert browser.context_count == 2


@pytest.mark.asyncio
async def test_open_page_reports_permanent_expiry(monkeypatch, tmp_path):
    calls = _patch_session_env(monkeypatch, tmp_path, [True])
    browser = _FakeBrowser([_FakePage(LOGGED_OUT_HTML), _FakePage(LOGGED_OUT_HTML)])
    page, err = await _open_healed_page(browser, "chat", "https://h/mod/assign/view.php?id=1")
    assert page is None
    assert "kedaluwarsa" in err
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_open_page_reports_failed_relogin(monkeypatch, tmp_path):
    _patch_session_env(monkeypatch, tmp_path, [False])
    browser = _FakeBrowser([_FakePage(LOGGED_OUT_HTML)])
    page, err = await _open_healed_page(browser, "chat", "https://h/mod/assign/view.php?id=1")
    assert page is None
    assert "relogin gagal" in err


@pytest.mark.asyncio
async def test_open_page_without_storage_state(monkeypatch, tmp_path):
    monkeypatch.setattr(
        browser_session, "_storage_state_path", lambda chat_id: tmp_path / "missing.json"
    )
    browser = _FakeBrowser([])
    page, err = await _open_healed_page(browser, "chat", "https://h/mod/assign/view.php?id=1")
    assert page is None
    assert "Session tidak ditemukan" in err


@pytest.mark.asyncio
async def test_failed_submission_token_can_retry_upload(monkeypatch):
    from app.xninetzy.os.academic.hebat import tools as hebat_tools

    submission_row = {
        "id": 9,
        "assignment_id": 42,
        "uploaded_filename": "tugas.pdf",
        "source_chat_id": "chat-owner",
        "upload_status": "failed",
        "local_file_path": "/tmp/tugas.pdf",
    }
    captured: dict = {}

    async def fake_upload(**kwargs):
        captured.update(kwargs)
        return {"status": "uploaded", "verification_text": "ok", "error": None}

    monkeypatch.setattr(hebat_tools, "get_submission_by_token", lambda token: submission_row)
    monkeypatch.setattr(hebat_tools, "_is_owner_chat", lambda *args: True)
    monkeypatch.setattr(
        hebat_tools,
        "list_assignments",
        lambda: [
            {
                "activity_id": 42,
                "title": "Tugas 1",
                "cmid": "7",
                "activity_url": "https://h/mod/assign/view.php?id=7",
            }
        ],
    )
    monkeypatch.setattr(hebat_tools, "upload_submission_via_playwright", fake_upload)

    result = await hebat_tools.hebat_upload_submission.ainvoke(
        {"chat_id": "chat-owner", "confirmation_token": "HBT-ABC123"}
    )

    assert "Berhasil upload" in result
    assert captured["token"] == "HBT-ABC123"


def test_submission_module_exports_classifier_contract():
    assert callable(submission.upload_submission_via_playwright)
    assert callable(submission.remove_submission_via_playwright)
