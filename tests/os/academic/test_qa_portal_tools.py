from __future__ import annotations

import pytest

from xninetzy.os.academic.qa_portal import tools as qa_tools


@pytest.mark.asyncio
async def test_qa_fill_requests_approval_before_mutation(monkeypatch):
    async def fake_list_questionnaires():
        return [{"code": "QA-101", "title": "Evaluasi"}]

    async def unexpected_fill_all_questionnaires(score: int):
        raise AssertionError("questionnaires must not be filled before approval")

    async def fake_notify(*args, **kwargs):
        return False

    monkeypatch.setattr(qa_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(qa_tools, "list_questionnaires", fake_list_questionnaires)
    monkeypatch.setattr(qa_tools, "fill_all_questionnaires", unexpected_fill_all_questionnaires)
    monkeypatch.setattr(qa_tools, "request_approval", lambda *args, **kwargs: 41)
    monkeypatch.setattr(qa_tools, "notify_admin_approval", fake_notify)

    result = await qa_tools.qa_fill_kuesioner.ainvoke(
        {"chat_id": "chat", "sender_id": "628123@chat.local", "score": 10}
    )

    assert "membutuhkan approval #41" in result


@pytest.mark.asyncio
async def test_legacy_approved_row_cannot_submit_qa(monkeypatch, tmp_path):
    from xninetzy.core.config import get_settings
    from xninetzy.db.sqlite import connect, init_db
    from xninetzy.db.migrations import run_migrations
    from xninetzy.os.hitl.approval_service import request_approval

    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "qa-approval.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    effects = []

    async def list_entries():
        return [{"code": "QA-fixture", "title": "Fixture"}]

    async def submit(**kwargs):
        effects.append(True)
        raise AssertionError("No external effect is authorized")

    monkeypatch.setattr(qa_tools, "is_owner_admin", lambda *args: True)
    monkeypatch.setattr(qa_tools, "list_questionnaires", list_entries)
    monkeypatch.setattr(qa_tools, "fill_all_questionnaires", submit)
    identifier = request_approval("fixture-chat", "fixture-owner", "qa_submit_kuesioner", "Fixture", "Fixture", {"score": 10, "questionnaire_codes": ["QA-fixture"]})
    with connect() as conn:
        conn.execute("UPDATE approval_requests SET status='approved' WHERE id=?", (identifier,))
    try:
        result = await qa_tools.qa_fill_kuesioner.ainvoke({"approval_id": identifier})
        assert "approval_channel_unverified" in result
        assert effects == []
    finally:
        get_settings.cache_clear()
