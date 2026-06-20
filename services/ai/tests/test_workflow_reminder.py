from __future__ import annotations

import pytest

from app.xninetzy.workflow.actions import DEFAULT_HANDLERS
from app.xninetzy.workflow.executor import WorkflowExecutor
from app.xninetzy.workflow.models import WorkflowActionResult, WorkflowActionStatus, WorkflowActionType
from app.xninetzy.workflow.plan import build_workflow_plan
from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.os.reminders.reminder_service import ReminderService


def _types(plan):
    return [a.type for a in plan.actions]


@pytest.fixture(autouse=True)
def sqlite_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "workflow-reminder.sqlite3"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_explicit_reminder_creates_create_action():
    plan = await build_workflow_plan("chat1", "ingatkan aku 30 menit lagi buat cek docker logs")
    assert _types(plan) == [WorkflowActionType.REMINDER_CREATE, WorkflowActionType.FINAL_SYNTHESIS]


@pytest.mark.asyncio
async def test_planning_with_deadline_creates_planning_then_reminder_infer():
    plan = await build_workflow_plan("chat1", "buat planning tugas APSI deadline tanggal 5 Juni jam 10 malam")
    types = _types(plan)
    assert WorkflowActionType.TASK_PLANNING in types
    assert WorkflowActionType.REMINDER_INFER in types
    assert types.index(WorkflowActionType.TASK_PLANNING) < types.index(WorkflowActionType.REMINDER_INFER)


@pytest.mark.asyncio
async def test_planning_without_clear_time_does_not_create_pending_reminder():
    plan = await build_workflow_plan("chat1", "buat planning tugas APSI")
    assert WorkflowActionType.REMINDER_INFER not in _types(plan)
    assert ReminderService().list_pending("chat1") == []


@pytest.mark.asyncio
async def test_final_response_includes_created_reminder_summary():
    plan = await build_workflow_plan("chat1", "buat planning tugas APSI deadline tanggal 5 Juni jam 10 malam")

    async def planning_handler(action, state):
        state.planning_context = {
            "topic": "Tugas APSI",
            "milestones": ["Pahami instruksi", "Kerjakan DFD", "Review"],
        }
        return WorkflowActionResult(
            action_id=action.id,
            status=WorkflowActionStatus.SUCCESS,
            summary="Planning dibuat: 3 milestone.",
        )

    async def obsidian_handler(action, state):
        return WorkflowActionResult(
            action_id=action.id,
            status=WorkflowActionStatus.SUCCESS,
            summary="Obsidian dilewati di test.",
        )

    handlers = {
        WorkflowActionType.TASK_PLANNING: planning_handler,
        WorkflowActionType.REMINDER_INFER: DEFAULT_HANDLERS[WorkflowActionType.REMINDER_INFER],
        WorkflowActionType.OBSIDIAN_SAVE: obsidian_handler,
        WorkflowActionType.FINAL_SYNTHESIS: DEFAULT_HANDLERS[WorkflowActionType.FINAL_SYNTHESIS],
    }
    result = await WorkflowExecutor(handlers=handlers).execute(plan)
    assert result.status == WorkflowActionStatus.SUCCESS
    assert "Reminder" in result.final_response
    assert ReminderService().list_pending("chat1")
