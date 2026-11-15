from __future__ import annotations

import asyncio

import pytest

from xninetzy.core.config import get_settings
from xninetzy.db.sqlite import connect, init_db
from xninetzy.workflow import executor, tools
from xninetzy.workflow.models import (
    WorkflowAction, WorkflowActionResult, WorkflowActionStatus as Status,
    WorkflowActionType as Type, WorkflowPlan,
)
from xninetzy.workflow.store import WorkflowStore


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "workflow.sqlite3"))
    monkeypatch.setenv("WORKFLOW_NOTIFY_ENABLED", "false")
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "auto")
    get_settings.cache_clear()
    init_db()
    yield WorkflowStore()
    get_settings.cache_clear()


def plan():
    return WorkflowPlan(
        id="recovery-fixture", chat_id="fixture-owner", original_user_message="Fixture task",
        title="Fixture", final_goal="Fixture", created_at="2026-11-14T00:00:00+00:00",
        actions=[
            WorkflowAction(id="write", type=Type.TASK_PLANNING, title="Write", goal="Fixture"),
            WorkflowAction(id="read", type=Type.REMINDER_LIST, title="Read", goal="Fixture", depends_on=["write"], critical=True),
        ],
    )


def success(action, text="Fixture done"):
    return WorkflowActionResult(action_id=action.id, status=Status.SUCCESS, summary=text)


@pytest.mark.asyncio
async def test_existing_successful_plan_cannot_execute_writes_twice(store):
    effects = []

    async def handler(action, state):
        effects.append(action.id)
        return success(action)

    workflow = plan()
    runner = executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler})
    await runner.execute(workflow)
    await runner.execute(workflow)
    assert effects == ["write", "read"]


@pytest.mark.asyncio
async def test_resume_does_not_rebuild_original_message(store, monkeypatch):
    workflow = plan()
    store.save_plan(workflow)
    rebuilt = []

    async def unexpected(*args, **kwargs):
        rebuilt.append(True)
        return "Rebuilt a different workflow"

    monkeypatch.setattr(executor, "run_workflow", unexpected)
    original_resume = executor.resume_workflow

    async def scoped_resume(chat_id, workflow_id, **kwargs):
        async def read_only_fixture(action, state):
            return success(action)
        return await original_resume(chat_id, workflow_id, from_=False, handlers={Type.TASK_PLANNING: read_only_fixture, Type.REMINDER_LIST: read_only_fixture})

    monkeypatch.setattr(executor, "resume_workflow", scoped_resume)
    await tools.workflow_resume.ainvoke({"chat_id": workflow.chat_id, "workflow_id": workflow.id})
    assert rebuilt == []
    assert len(store.list_for_chat(workflow.chat_id)) == 1


@pytest.mark.asyncio
async def test_persistence_failure_prevents_first_effect(store):
    effects = []
    with connect() as conn:
        conn.execute("CREATE TRIGGER fail_checkpoint BEFORE INSERT ON workflow_action_runs BEGIN SELECT RAISE(ABORT, 'synthetic disk failure'); END")

    async def handler(action, state):
        effects.append(action.id)
        return success(action)

    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(plan())
    assert result.status == Status.FAILED
    assert effects == []


@pytest.mark.asyncio
async def test_recovery_preserves_successful_write_and_working_state(store):
    effects = []
    reads = []

    async def write(action, state):
        effects.append(True)
        state.artifacts["persisted-record"] = "fixture-42"
        return success(action, "Created fixture-42")

    async def read(action, state):
        reads.append(True)
        assert state.artifacts["persisted-record"] == "fixture-42"
        if len(reads) == 1:
            return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Temporary read failure")
        return success(action)

    workflow = plan()
    handlers = {Type.TASK_PLANNING: write, Type.REMINDER_LIST: read}
    assert (await executor.WorkflowExecutor(store=store, handlers=handlers).execute(workflow)).status == Status.FAILED
    # New objects model a restarted process; no in-memory state is passed.
    result = await executor.resume_workflow(workflow.chat_id, workflow.id, handlers=handlers, from_=False)
    assert "sebagian" not in result
    assert effects == [True]
    assert len(reads) == 2
    assert store.get(workflow.id)["status"] == "success"


@pytest.mark.asyncio
async def test_concurrent_execution_is_held_without_duplicate_effect(store):
    entered, release = asyncio.Event(), asyncio.Event()
    effects = []

    async def handler(action, state):
        effects.append(action.id)
        if action.id == "write":
            entered.set()
            await release.wait()
        return success(action)

    handlers = {Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}
    first = asyncio.create_task(executor.WorkflowExecutor(store=store, handlers=handlers).execute(plan()))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        second = await asyncio.wait_for(executor.WorkflowExecutor(store=store, handlers=handlers).execute(plan()), 1)
        assert second.status == Status.FAILED
    finally:
        release.set()
        await first
    assert effects == ["write", "read"]


@pytest.mark.asyncio
async def test_uncertain_failed_mutation_is_not_retried(store):
    effects = []

    async def mutation(action, state):
        effects.append(True)
        return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Unknown delivery")

    workflow = plan()
    workflow.actions = workflow.actions[:1]
    await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: mutation}).execute(workflow)
    result = await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False, handlers={Type.TASK_PLANNING: mutation})
    assert "workflow_uncertain_outcome_reconcile" in result
    assert effects == [True]


@pytest.mark.asyncio
async def test_cancel_during_execution_stops_next_action_and_preserves_status(store):
    effects = []

    async def handler(action, state):
        effects.append(action.id)
        assert store.mark_cancelled(state.chat_id, state.plan_id)
        return success(action)

    workflow = plan()
    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler}).execute(workflow)
    assert result.status == Status.CANCELLED
    assert store.get(workflow.id)["status"] == "cancelled"
    assert effects == ["write"]
    assert "workflow_cancelled" in await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("change,code", [("legacy", "legacy_checkpoint"), ("plan", "checkpoint_mismatch"), ("corrupt", "checkpoint_invalid")])
async def test_invalid_checkpoint_never_executes(store, change, code):
    workflow = plan()
    store.save_plan(workflow)
    with connect() as conn:
        if change == "legacy":
            conn.execute("UPDATE workflow_runs SET result_json=NULL")
        elif change == "plan":
            workflow.actions[0].input["target"] = "changed"
            conn.execute("UPDATE workflow_runs SET plan_json=?", (workflow.model_dump_json(),))
        else:
            conn.execute("UPDATE workflow_runs SET result_json='not-json'")
    result = await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False)
    assert code in result


@pytest.mark.asyncio
async def test_resume_rechecks_policy_and_owner(store, monkeypatch):
    workflow = plan()
    store.save_plan(workflow)
    assert "tidak ditemukan" in await tools.workflow_resume.ainvoke({"chat_id": "other-owner", "workflow_id": workflow.id})
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "manual")
    get_settings.cache_clear()
    assert "workflow_policy_held" in await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False)
    assert store.get(workflow.id)["status"] == "running"


@pytest.mark.asyncio
async def test_success_checkpoint_failure_holds_after_effect_without_second_step(store):
    effects = []
    with connect() as conn:
        conn.execute("CREATE TRIGGER fail_success BEFORE UPDATE ON workflow_action_runs WHEN NEW.status='success' BEGIN SELECT RAISE(ABORT, 'synthetic commit failure'); END")

    async def handler(action, state):
        effects.append(action.id)
        return success(action)

    workflow = plan()
    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(workflow)
    assert "workflow_checkpoint_unverified" in result.final_response
    assert effects == ["write"]
    with connect() as conn:
        assert conn.execute("SELECT status FROM workflow_action_runs").fetchone()[0] == "running"
    assert "uncertain_outcome" in await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False)


@pytest.mark.asyncio
async def test_notification_failure_does_not_erase_committed_checkpoint(store):
    class Notifier:
        async def notify_action_started(self, *args):
            raise RuntimeError("synthetic notification failure")

        notify_action_done = notify_action_started
        notify_action_failed = notify_action_started
        notify_final = notify_action_started

    async def handler(action, state):
        return success(action)

    workflow = plan()
    result = await executor.WorkflowExecutor(store=store, notifier=Notifier(), handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(workflow)
    assert result.status == Status.SUCCESS
    assert store.get(workflow.id)["status"] == "success"


@pytest.mark.asyncio
@pytest.mark.parametrize("interrupt_at", ["write", "read"])
async def test_real_process_restart_preserves_effects_and_releases_lock(store, interrupt_at):
    import os
    import select
    import subprocess
    import sys

    with connect() as conn:
        conn.execute("CREATE TABLE recovery_effects (operation TEXT PRIMARY KEY)")
    workflow = plan()
    code = """
import asyncio, json, sys
from xninetzy.core.config import Settings, get_settings
Settings.model_config['env_file'] = None
get_settings.cache_clear()
from xninetzy.db.sqlite import connect
from xninetzy.workflow.executor import WorkflowExecutor
from xninetzy.workflow.models import WorkflowPlan, WorkflowActionResult, WorkflowActionStatus, WorkflowActionType
from xninetzy.workflow.store import WorkflowStore
workflow = WorkflowPlan.model_validate_json(sys.stdin.readline())
async def handler(action, state):
    if action.id == 'write':
        with connect() as connection:
            connection.execute("INSERT INTO recovery_effects VALUES ('fixture-record')")
        state.artifacts['record'] = 'fixture-record'
    if action.id == sys.argv[1]:
        print('checkpoint-ready', flush=True)
        await asyncio.Event().wait()
    return WorkflowActionResult(action_id=action.id, status=WorkflowActionStatus.SUCCESS, summary='Fixture done')
asyncio.run(WorkflowExecutor(store=WorkflowStore(), handlers={WorkflowActionType.TASK_PLANNING: handler, WorkflowActionType.REMINDER_LIST: handler}).execute(workflow))
"""
    child = subprocess.Popen([sys.executable, "-c", code, interrupt_at], env=dict(os.environ), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        child.stdin.write(workflow.model_dump_json() + "\n")
        child.stdin.flush()
        assert select.select([child.stdout], [], [], 8)[0], "Child did not reach its checkpoint"
        assert child.stdout.readline().strip() == "checkpoint-ready"
        child.kill()  # Only the fixture process; no owner session or container.
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()

    async def recovered(action, state):
        assert action.id == "read", "A completed or uncertain mutation must never repeat"
        assert state.artifacts["record"] == "fixture-record"
        return success(action)

    result = await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False, handlers={Type.TASK_PLANNING: recovered, Type.REMINDER_LIST: recovered})
    with connect() as conn:
        assert conn.execute("SELECT count(*) FROM recovery_effects").fetchone()[0] == 1
    if interrupt_at == "write":
        assert "uncertain_outcome_reconcile" in result
    else:
        assert store.get(workflow.id)["status"] == "success"


@pytest.mark.asyncio
async def test_checkpoint_redacts_credentials_from_working_state(store):
    async def handler(action, state):
        state.artifacts["token"] = "synthetic-private-credential"
        return success(action)

    workflow = plan()
    await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(workflow)
    assert "synthetic-private-credential" not in store.get(workflow.id)["result_json"]
    with connect() as conn:
        assert all("synthetic-private-credential" not in row[0] for row in conn.execute("SELECT result_json FROM workflow_action_runs"))


@pytest.mark.asyncio
async def test_cancellation_wins_race_with_final_commit(store, monkeypatch):
    original = store.save_result

    def cancel_before_commit(workflow, result):
        assert store.mark_cancelled(workflow.chat_id, workflow.id)
        return original(workflow, result)

    monkeypatch.setattr(store, "save_result", cancel_before_commit)

    async def handler(action, state):
        return success(action)

    workflow = plan()
    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(workflow)
    assert result.status == Status.CANCELLED
    assert '"status":"cancelled"' in store.get(workflow.id)["result_json"]


@pytest.mark.asyncio
async def test_cancellation_before_step_claim_prevents_effect(store, monkeypatch):
    original = store.save_checkpoint
    effects = []

    def cancel_before_claim(workflow, state, results, action):
        if action.status == Status.RUNNING:
            store.mark_cancelled(workflow.chat_id, workflow.id)
        return original(workflow, state, results, action)

    monkeypatch.setattr(store, "save_checkpoint", cancel_before_claim)

    async def handler(action, state):
        effects.append(action.id)
        return success(action)

    await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler}).execute(plan())
    assert effects == []


@pytest.mark.asyncio
async def test_interrupted_retry_keeps_independent_success_evidence(store):
    workflow = plan()
    workflow.actions.reverse()
    workflow.actions[0].depends_on = []
    workflow.actions[0].critical = False
    reads, writes = [], []

    async def read(action, state):
        reads.append(True)
        if len(reads) == 1:
            return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Temporary failure")
        if len(reads) == 2:
            raise asyncio.CancelledError()
        return success(action)

    async def write(action, state):
        writes.append(True)
        return success(action)

    handlers = {Type.TASK_PLANNING: write, Type.REMINDER_LIST: read}
    await executor.WorkflowExecutor(store=store, handlers=handlers).execute(workflow)
    with pytest.raises(asyncio.CancelledError):
        await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False, handlers=handlers)
    saved_plan = WorkflowPlan.model_validate_json(store.get(workflow.id)["plan_json"])
    saved = store.restore_checkpoint(saved_plan)
    assert [r.action_id for r in saved.succeeded()] == ["write"]
    await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False, handlers=handlers)
    assert writes == [True]
    assert store.get(workflow.id)["status"] == "success"


@pytest.mark.asyncio
async def test_expired_execution_budget_prevents_starting_another_step(store, monkeypatch):
    monkeypatch.setenv("XNINETZY_TOOL_TIMEOUT_SECONDS", "1")
    get_settings.cache_clear()
    effects = []

    async def handler(action, state):
        effects.append(action.id)
        await asyncio.sleep(1.05)
        return success(action)

    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler, Type.REMINDER_LIST: handler}).execute(plan())
    assert "workflow_deadline_exceeded" in result.final_response
    assert effects == ["write"]


@pytest.mark.asyncio
async def test_sensitive_action_input_is_held_before_persistence_or_effect(store):
    workflow = plan()
    workflow.actions[0].input = {"api_key": "synthetic-private-credential"}
    result = await executor.WorkflowExecutor(store=store).execute(workflow)
    assert "workflow_sensitive_input" in result.final_response
    assert store.get(workflow.id) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["chat_id", "plan_id", "original_user_message"])
async def test_working_context_cannot_change_owner_or_objective(store, field):
    downstream = []

    async def poison(action, state):
        setattr(state, field, "different-context")
        return success(action)

    async def next_step(action, state):
        downstream.append(True)
        return success(action)

    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: poison, Type.REMINDER_LIST: next_step}).execute(plan())
    assert downstream == []
    assert "workflow_context_mismatch" in result.final_response


@pytest.mark.asyncio
@pytest.mark.parametrize("target", ["file", "directory"])
async def test_workflow_lock_refuses_symlink_paths(store, tmp_path, target):
    with store.execution_lock(plan().id):
        pass
    directory = tmp_path / ".workflow-locks"
    marker = tmp_path / "must-not-change"
    marker.write_text("synthetic fixture")
    if target == "file":
        lockfile = next(directory.iterdir())
        lockfile.unlink()  # Fixture only, no live descriptor is held.
        lockfile.symlink_to(marker)
    else:
        for lockfile in directory.iterdir():
            lockfile.unlink()
        directory.rmdir()
        directory.symlink_to(tmp_path, target_is_directory=True)
    effects = []

    async def handler(action, state):
        effects.append(True)
        return success(action)

    result = await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: handler}).execute(plan())
    assert result.status == Status.FAILED
    assert effects == []
    assert marker.read_text() == "synthetic fixture"


@pytest.mark.asyncio
async def test_owner_can_cancel_failed_checkpoint_to_prevent_future_resume(store):
    async def write(action, state):
        return success(action)

    async def fail(action, state):
        return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Temporary read failure")

    workflow = plan()
    await executor.WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: write, Type.REMINDER_LIST: fail}).execute(workflow)
    assert store.mark_cancelled(workflow.chat_id, workflow.id)
    assert "workflow_cancelled" in await executor.resume_workflow(workflow.chat_id, workflow.id, from_=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["exception", "returned"])
async def test_private_handler_errors_do_not_reach_logs_or_progress(store, caplog, kind):
    notifications = []

    class Notifier:
        async def notify_action_started(self, *args):
            pass

        async def notify_action_failed(self, workflow, action):
            notifications.append(action.error)

        async def notify_final(self, *args):
            pass

    async def handler(action, state):
        if kind == "exception":
            raise RuntimeError("arbitrary-private-sentinel")
        return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="password=arbitrary-private-sentinel")

    workflow = plan()
    workflow.actions = workflow.actions[:1]
    with caplog.at_level("WARNING"):
        await executor.WorkflowExecutor(store=store, notifier=Notifier(), handlers={Type.TASK_PLANNING: handler}).execute(workflow)
    assert notifications
    assert "arbitrary-private-sentinel" not in caplog.text
    assert "arbitrary-private-sentinel" not in str(notifications)
