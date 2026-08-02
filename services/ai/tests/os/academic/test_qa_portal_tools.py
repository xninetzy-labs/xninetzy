from __future__ import annotations

import pytest

from app.xninetzy.os.academic.qa_portal import tools as qa_tools


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
        {"chat_id": "chat", "sender_id": "628123@s.whatsapp.net", "score": 10}
    )

    assert "membutuhkan approval #41" in result
