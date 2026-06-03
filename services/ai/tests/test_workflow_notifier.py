"""Offline tests for the WA workflow notifier (send + sleep mocked)."""

from __future__ import annotations

import pytest

from app.agent import workflow_notifier as wn
from app.agent.workflow_notifier import WorkflowNotifier
from app.agent.workflow_models import WorkflowAction, WorkflowActionType, WorkflowPlan


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    async def fast_sleep(_s):
        return None
    monkeypatch.setattr(wn, "_sleep", fast_sleep)


def _plan(n=2):
    actions = [
        WorkflowAction(id=f"a{i}", type=WorkflowActionType.DEEP_RESEARCH, title=f"Step {i}", goal="g")
        for i in range(1, n + 1)
    ]
    return WorkflowPlan(id="wf", chat_id="628", original_user_message="x", title="t",
                        actions=actions, final_goal="x", created_at="now")


def _capture():
    sent: list[str] = []

    async def send(chat_id, text):
        sent.append(text)

    return sent, send


@pytest.mark.asyncio
async def test_done_notification_format():
    sent, send = _capture()
    plan = _plan(2)
    notifier = WorkflowNotifier("628", enabled=True, send=send)
    plan.actions[1].result_summary = "Ditemukan 8 sumber"
    await notifier.notify_action_done(plan, plan.actions[1])
    assert sent and sent[0].startswith("✅ Step 2/2 selesai")
    assert "8 sumber" in sent[0]


@pytest.mark.asyncio
async def test_failed_notification_no_traceback():
    sent, send = _capture()
    plan = _plan(2)
    notifier = WorkflowNotifier("628", enabled=True, send=send)
    plan.actions[0].error = "link file tidak ditemukan"
    await notifier.notify_action_failed(plan, plan.actions[0])
    assert sent[0].startswith("⚠️ Step 1/2 gagal")
    assert "Traceback" not in sent[0]


@pytest.mark.asyncio
async def test_no_spam_when_notify_on_done_false():
    sent, send = _capture()
    plan = _plan(1)
    plan.actions[0].notify_on_done = False
    notifier = WorkflowNotifier("628", enabled=True, send=send)
    await notifier.notify_action_done(plan, plan.actions[0])
    assert sent == []


@pytest.mark.asyncio
async def test_disabled_notifier_sends_nothing():
    sent, send = _capture()
    plan = _plan(1)
    notifier = WorkflowNotifier("628", enabled=False, send=send)
    await notifier.notify_action_done(plan, plan.actions[0])
    await notifier.notify_final(plan, "selesai")
    assert sent == []


@pytest.mark.asyncio
async def test_message_length_capped(monkeypatch):
    sent, send = _capture()
    notifier = WorkflowNotifier("628", enabled=True, send=send)
    monkeypatch.setattr(notifier.settings, "WORKFLOW_NOTIFY_MAX_MESSAGE_LENGTH", 30, raising=False)
    plan = _plan(1)
    plan.actions[0].result_summary = "x" * 200
    await notifier.notify_action_done(plan, plan.actions[0])
    assert len(sent[0]) <= 30
