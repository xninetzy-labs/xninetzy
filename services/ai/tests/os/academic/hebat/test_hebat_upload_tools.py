from __future__ import annotations

import pytest

from app.xninetzy.os.academic.hebat import tools as hebat_tools


@pytest.mark.asyncio
async def test_hebat_upload_requests_approval_before_browser_upload(monkeypatch):
    submission = {
        "id": 9,
        "assignment_id": 42,
        "uploaded_filename": "tugas.pdf",
        "source_chat_id": "chat-owner",
        "upload_status": "pending_confirmation",
        "local_file_path": "/tmp/tugas.pdf",
    }

    async def unexpected_upload(**kwargs):
        raise AssertionError("browser upload must not start before approval")

    async def fake_notify(*args, **kwargs):
        return False

    monkeypatch.setattr(hebat_tools, "get_submission_by_token", lambda token: submission)
    monkeypatch.setattr(hebat_tools, "request_approval", lambda *args, **kwargs: 52)
    monkeypatch.setattr(hebat_tools, "notify_admin_approval", fake_notify)
    monkeypatch.setattr(hebat_tools, "upload_submission_via_playwright", unexpected_upload)

    result = await hebat_tools.hebat_upload_submission.ainvoke(
        {"chat_id": "chat-owner", "confirmation_token": "CONFIRM-9"}
    )

    assert "membutuhkan approval #52" in result
