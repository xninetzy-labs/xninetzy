"""Persistence for workflow runs + their actions (history / resume / debug)."""

from __future__ import annotations

from datetime import datetime
from contextlib import contextmanager
import hashlib
import json
import os
from zoneinfo import ZoneInfo

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging
from xninetzy.db.sqlite import connect, init_db, get_db_path
from xninetzy.core.security import sanitize_tool_output
from xninetzy.workflow.models import (
    WorkflowAction,
    WorkflowExecutionResult,
    WorkflowPlan,
    WorkflowState,
    WorkflowCheckpoint,
    WorkflowActionStatus,
    WorkflowActionResult,
)

logger = logging.getLogger(__name__)


class WorkflowRecoveryError(RuntimeError):
    """A safe recovery boundary; the code contains no private payload."""


def plan_fingerprint(plan: WorkflowPlan) -> str:
    payload = plan.model_dump(mode="json")
    for action in payload["actions"]:
        for key in ("status", "result_summary", "error"):
            action.pop(key, None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _safe_plan(plan: WorkflowPlan) -> WorkflowPlan:
    payload = sanitize_tool_output(plan.model_dump(mode="json"))
    payload["chat_id"] = plan.chat_id  # canonical owner identity, not retrieved context
    clean = WorkflowPlan.model_validate(payload)
    if plan_fingerprint(clean) != plan_fingerprint(plan):
        raise WorkflowRecoveryError("workflow_sensitive_input")
    return clean


def _checkpoint(plan, state, results, status=WorkflowActionStatus.RUNNING):
    payload = sanitize_tool_output(state.model_dump(mode="json"))
    payload.update(plan_id=plan.id, chat_id=plan.chat_id)
    result = WorkflowExecutionResult(
        plan_id=plan.id, status=status, final_response="",
        action_results=[WorkflowActionResult.model_validate(sanitize_tool_output(r.model_dump(mode="json"))) for r in results],
        checkpoint=WorkflowCheckpoint(plan_hash=plan_fingerprint(plan), state=WorkflowState.model_validate(payload)),
    )
    if len(result.model_dump_json().encode()) > 262_144:
        raise WorkflowRecoveryError("workflow_checkpoint_limit_exceeded")
    return result


def _now() -> str:
    try:
        tz = ZoneInfo(get_settings().APP_TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).isoformat()


class WorkflowStore:
    @contextmanager
    def execution_lock(self, workflow_id: str):
        """Local POSIX lock; released when the last descriptor closes, never unlinked.

        No SQLite transaction is held across domain execution. Multi-host/NFS
        and non-POSIX runtimes require a separately verified coordination mode.
        """
        try:
            import fcntl
        except ImportError:
            raise WorkflowRecoveryError("workflow_lock_unsupported") from None
        directory = get_db_path().resolve().parent / ".workflow-locks"
        directory.mkdir(mode=0o700, exist_ok=True)
        if directory.is_symlink():
            raise WorkflowRecoveryError("workflow_lock_unsafe_path")
        name = hashlib.sha256(workflow_id.encode()).hexdigest() + ".lock"
        descriptor = os.open(directory / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise WorkflowRecoveryError("workflow_execution_in_progress") from None
            yield
        finally:
            os.close(descriptor)

    def save_plan(self, plan: WorkflowPlan, state: WorkflowState | None = None) -> None:
        init_db()
        plan = _safe_plan(plan)
        state = state or WorkflowState(plan_id=plan.id, chat_id=plan.chat_id, original_user_message=plan.original_user_message)
        checkpoint = _checkpoint(plan, state, [])
        now = _now()
        with connect() as conn:
            inserted = conn.execute(
                """
                INSERT OR IGNORE INTO workflow_runs
                  (id, chat_id, title, original_user_message, status, plan_json,
                   result_json, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (plan.id, plan.chat_id, plan.title, plan.original_user_message,
                 "running", plan.model_dump_json(), checkpoint.model_dump_json(), plan.created_at, now),
            )
            if inserted.rowcount != 1:
                raise WorkflowRecoveryError("workflow_already_exists")
        logger.info("workflow_saved workflow_id=%s actions=%d", plan.id, len(plan.actions))

    def save_checkpoint(self, plan: WorkflowPlan, state: WorkflowState, results: list, action: WorkflowAction) -> None:
        plan = _safe_plan(plan)
        action = next(a for a in plan.actions if a.id == action.id)
        checkpoint = _checkpoint(plan, state, results)
        key = hashlib.sha256(json.dumps([plan.id, action.id]).encode()).hexdigest()
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT result_json,chat_id,status FROM workflow_runs WHERE id=?", (plan.id,)).fetchone()
            if not row or row["chat_id"] != plan.chat_id:
                raise WorkflowRecoveryError("workflow_owner_mismatch")
            if row["status"] == "cancelled" and action.status == WorkflowActionStatus.RUNNING:
                raise WorkflowRecoveryError("workflow_cancelled")
            previous = WorkflowExecutionResult.model_validate_json(row["result_json"])
            if previous.checkpoint is None or previous.checkpoint.plan_hash != checkpoint.checkpoint.plan_hash:
                raise WorkflowRecoveryError("workflow_plan_changed")
            conn.execute(
                "INSERT INTO workflow_action_runs (id,workflow_id,action_type,title,status,input_json,result_json,result_summary,error,started_at,finished_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,result_json=excluded.result_json,"
                "result_summary=excluded.result_summary,error=excluded.error,finished_at=excluded.finished_at",
                (key, plan.id, action.type.value, action.title, action.status.value,
                 json.dumps(action.input), checkpoint.model_dump_json(), action.result_summary, action.error,
                 _now(), None if action.status == WorkflowActionStatus.RUNNING else _now()),
            )
            conn.execute("UPDATE workflow_runs SET status=CASE WHEN status='cancelled' THEN status ELSE 'running' END,plan_json=?,result_json=?,updated_at=? WHERE id=?",
                         (plan.model_dump_json(), checkpoint.model_dump_json(), _now(), plan.id))

    def restore_checkpoint(self, plan: WorkflowPlan) -> WorkflowExecutionResult:
        row = self.get(plan.id)
        if not row or row["chat_id"] != plan.chat_id:
            raise WorkflowRecoveryError("workflow_owner_mismatch")
        if not row["result_json"]:
            raise WorkflowRecoveryError("workflow_legacy_checkpoint_unavailable")
        try:
            result = WorkflowExecutionResult.model_validate_json(row["result_json"])
        except ValueError:
            raise WorkflowRecoveryError("workflow_checkpoint_invalid") from None
        checkpoint = result.checkpoint
        if checkpoint is None:
            raise WorkflowRecoveryError("workflow_legacy_checkpoint_unavailable")
        if row["status"] == "success" and result.status != WorkflowActionStatus.SUCCESS:
            raise WorkflowRecoveryError("workflow_completion_unverified")
        if (result.plan_id != plan.id or checkpoint.plan_hash != plan_fingerprint(plan)
                or checkpoint.state.plan_id != plan.id or checkpoint.state.chat_id != plan.chat_id):
            raise WorkflowRecoveryError("workflow_checkpoint_mismatch")
        by_id = {r.action_id: r for r in result.action_results}
        if len(by_id) != len(result.action_results) or set(by_id) - {a.id for a in plan.actions}:
            raise WorkflowRecoveryError("workflow_checkpoint_invalid")
        for action in plan.actions:
            prior = by_id.get(action.id)
            if action.status == WorkflowActionStatus.SUCCESS and (prior is None or prior.status != action.status):
                raise WorkflowRecoveryError("workflow_completion_unverified")
            if prior is not None and (prior.status != action.status or prior.status not in {
                WorkflowActionStatus.SUCCESS, WorkflowActionStatus.FAILED, WorkflowActionStatus.SKIPPED,
            }):
                raise WorkflowRecoveryError("workflow_checkpoint_invalid")
        return result

    def save_action(self, action: WorkflowAction, workflow_id: str | None = None) -> None:
        init_db()
        wf = workflow_id or getattr(action, "_workflow_id", None)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_action_runs
                  (id, workflow_id, action_type, title, status, input_json,
                   result_json, result_summary, error, started_at, finished_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  status=excluded.status, result_summary=excluded.result_summary,
                  error=excluded.error, finished_at=excluded.finished_at
                """,
                (f"{wf or 'wf'}:{action.id}", wf or "", action.type.value, action.title,
                 action.status.value, None, None, action.result_summary, action.error,
                 None, _now()),
            )

    def save_result(self, plan: WorkflowPlan, result: WorkflowExecutionResult) -> WorkflowExecutionResult:
        init_db()
        plan = _safe_plan(plan)
        if result.checkpoint is not None:
            clean = _checkpoint(plan, result.checkpoint.state, result.action_results, result.status)
            clean.final_response = sanitize_tool_output(result.final_response)
            result = clean
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT status FROM workflow_runs WHERE id=?", (plan.id,)).fetchone()
            if row and row["status"] == "cancelled":
                result.status = WorkflowActionStatus.CANCELLED
                result.final_response = "Workflow dibatalkan; hasil langkah yang sudah selesai tetap tersimpan."
            conn.execute(
                "UPDATE workflow_runs SET status=CASE WHEN status='cancelled' THEN status ELSE ? END, result_json=?, plan_json=?, updated_at=? WHERE id=?",
                (result.status.value, result.model_dump_json(), plan.model_dump_json(),
                 _now(), plan.id),
            )
        return result

    def get(self, workflow_id: str) -> dict | None:
        init_db()
        with connect() as conn:
            row = conn.execute("SELECT * FROM workflow_runs WHERE id=?", (workflow_id,)).fetchone()
        return dict(row) if row else None

    def get_latest(self, chat_id: str) -> dict | None:
        init_db()
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE chat_id=? ORDER BY created_at DESC LIMIT 1",
                (chat_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_for_chat(self, chat_id: str, limit: int = 10) -> list[dict]:
        init_db()
        with connect() as conn:
            rows = conn.execute(
                "SELECT * FROM workflow_runs WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_cancelled(self, chat_id: str, workflow_id: str) -> bool:
        init_db()
        with connect() as conn:
            cur = conn.execute(
                "UPDATE workflow_runs SET status='cancelled', updated_at=? "
                "WHERE id=? AND chat_id=? AND status IN ('running','pending','failed')",
                (_now(), workflow_id, chat_id),
            )
            return cur.rowcount > 0
