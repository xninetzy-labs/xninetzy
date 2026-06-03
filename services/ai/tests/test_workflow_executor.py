"""Offline tests for the workflow executor control flow (stub handlers)."""

from __future__ import annotations

import pytest

from app.agent.workflow_executor import WorkflowExecutor
from app.agent.workflow_models import (
    WorkflowAction, WorkflowActionResult, WorkflowActionStatus, WorkflowActionType,
    WorkflowPlan, WorkflowState,
)


def _plan(actions):
    return WorkflowPlan(
        id="wf1", chat_id="628", original_user_message="x", title="t",
        actions=actions, final_goal="x", created_at="now",
    )


def _action(aid, atype, depends=None, critical=False):
    return WorkflowAction(
        id=aid, type=atype, title=f"step {aid}", goal="g",
        depends_on=depends or [], critical=critical,
    )


def _ok_handler(summary):
    async def h(action, state):
        return WorkflowActionResult(action_id=action.id, status=WorkflowActionStatus.SUCCESS, summary=summary)
    return h


def _fail_handler(err):
    async def h(action, state):
        return WorkflowActionResult(action_id=action.id, status=WorkflowActionStatus.FAILED, error=err)
    return h


@pytest.mark.asyncio
async def test_all_success_collects_summaries():
    plan = _plan([
        _action("a1", WorkflowActionType.DEEP_RESEARCH),
        _action("a2", WorkflowActionType.ROADMAP_CREATE, ["a1"]),
        _action("a3", WorkflowActionType.FINAL_SYNTHESIS, ["a2"]),
    ])
    handlers = {
        WorkflowActionType.DEEP_RESEARCH: _ok_handler("riset selesai"),
        WorkflowActionType.ROADMAP_CREATE: _ok_handler("roadmap 5 milestone"),
        WorkflowActionType.FINAL_SYNTHESIS: _ok_handler("ringkasan akhir"),
    }
    res = await WorkflowExecutor(handlers=handlers).execute(plan)
    assert res.status == WorkflowActionStatus.SUCCESS
    assert len(res.succeeded()) == 3
    assert "ringkasan akhir" in res.final_response


@pytest.mark.asyncio
async def test_noncritical_failure_continues():
    plan = _plan([
        _action("a1", WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS),       # fails (non-critical)
        _action("a2", WorkflowActionType.TASK_PLANNING, ["a1"]),          # must still run
        _action("a3", WorkflowActionType.FINAL_SYNTHESIS, ["a2"]),
    ])
    handlers = {
        WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS: _fail_handler("link file tidak ditemukan"),
        WorkflowActionType.TASK_PLANNING: _ok_handler("planning 4 milestone"),
        WorkflowActionType.FINAL_SYNTHESIS: _ok_handler("done"),
    }
    res = await WorkflowExecutor(handlers=handlers).execute(plan)
    statuses = {r.action_id: r.status for r in res.action_results}
    assert statuses["a1"] == WorkflowActionStatus.FAILED
    assert statuses["a2"] == WorkflowActionStatus.SUCCESS  # continued despite a1 failing
    assert "link file tidak ditemukan" in res.final_response
    assert "planning 4 milestone" in res.final_response


@pytest.mark.asyncio
async def test_critical_failure_stops_with_partial():
    plan = _plan([
        _action("a1", WorkflowActionType.HEBAT_SYNC, critical=True),  # critical fail → stop
        _action("a2", WorkflowActionType.TASK_PLANNING, ["a1"]),
    ])
    handlers = {
        WorkflowActionType.HEBAT_SYNC: _fail_handler("login HEBAT gagal"),
        WorkflowActionType.TASK_PLANNING: _ok_handler("should not run"),
    }
    res = await WorkflowExecutor(handlers=handlers).execute(plan)
    assert res.status == WorkflowActionStatus.FAILED
    ran = {r.action_id for r in res.action_results}
    assert "a2" not in ran  # stopped before a2
    assert "login HEBAT gagal" in res.final_response


@pytest.mark.asyncio
async def test_skipped_dependency_cascades():
    # a1 skipped (unknown handler type via empty registry) → a2 depends on a1 → skipped
    plan = _plan([
        _action("a1", WorkflowActionType.MEMORY_SAVE),
        _action("a2", WorkflowActionType.OBSIDIAN_SAVE, ["a1"]),
    ])

    async def skip_handler(action, state):
        return WorkflowActionResult(action_id=action.id, status=WorkflowActionStatus.SKIPPED, summary="skip")

    handlers = {WorkflowActionType.MEMORY_SAVE: skip_handler}  # a2 has no handler
    res = await WorkflowExecutor(handlers=handlers).execute(plan)
    statuses = {r.action_id: r.status for r in res.action_results}
    assert statuses["a1"] == WorkflowActionStatus.SKIPPED
    assert statuses["a2"] == WorkflowActionStatus.SKIPPED


@pytest.mark.asyncio
async def test_notifier_called_on_success(monkeypatch):
    sent: list[str] = []

    class FakeNotifier:
        async def notify_action_started(self, plan, action): ...
        async def notify_action_done(self, plan, action): sent.append(f"done:{action.id}")
        async def notify_action_failed(self, plan, action): sent.append(f"fail:{action.id}")
        async def notify_final(self, plan, line): sent.append("final")

    plan = _plan([_action("a1", WorkflowActionType.DEEP_RESEARCH)])
    handlers = {WorkflowActionType.DEEP_RESEARCH: _ok_handler("ok")}
    await WorkflowExecutor(notifier=FakeNotifier(), handlers=handlers).execute(plan)
    assert "done:a1" in sent and "final" in sent
