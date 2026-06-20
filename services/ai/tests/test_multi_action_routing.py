"""Routing + history persistence tests for the workflow engine."""

from __future__ import annotations

import pytest

from app.xninetzy.workflow.plan import build_workflow_plan, is_multi_action_request
from app.xninetzy.workflow.store import WorkflowStore
from app.xninetzy.workflow.models import WorkflowActionStatus, WorkflowExecutionResult


def test_simple_message_does_not_route_to_workflow():
    assert not is_multi_action_request("ringkas pdf ini")
    assert not is_multi_action_request("apa deadline tugasku")


def test_compound_message_routes_to_workflow():
    assert is_multi_action_request("riset graph rag lalu buat planning pengerjaan tugas")


@pytest.mark.asyncio
async def test_workflow_history_saved_and_listed():
    chat = "test-wf-history-628"
    plan = await build_workflow_plan(chat, "riset graph rag lalu buat roadmap")
    store = WorkflowStore()
    store.save_plan(plan)

    latest = store.get_latest(chat)
    assert latest and latest["id"] == plan.id
    assert latest["status"] == "running"

    # Persist a result → status updated.
    result = WorkflowExecutionResult(
        plan_id=plan.id, status=WorkflowActionStatus.SUCCESS, final_response="done",
    )
    store.save_result(plan, result)
    assert store.get(plan.id)["status"] == "success"

    runs = store.list_for_chat(chat)
    assert any(r["id"] == plan.id for r in runs)


@pytest.mark.asyncio
async def test_workflow_cancel():
    chat = "test-wf-cancel-628"
    plan = await build_workflow_plan(chat, "riset graph rag lalu buat roadmap")
    store = WorkflowStore()
    store.save_plan(plan)  # status = running
    assert store.mark_cancelled(chat, plan.id) is True
    assert store.get(plan.id)["status"] == "cancelled"
    # Cancelling again (already cancelled) → False
    assert store.mark_cancelled(chat, plan.id) is False
