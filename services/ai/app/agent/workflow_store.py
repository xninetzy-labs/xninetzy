"""Persistence for workflow runs + their actions (history / resume / debug)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.logging import logging
from app.db.sqlite import connect, init_db
from app.agent.workflow_models import (
    WorkflowAction,
    WorkflowExecutionResult,
    WorkflowPlan,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    try:
        tz = ZoneInfo(get_settings().APP_TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).isoformat()


class WorkflowStore:
    def save_plan(self, plan: WorkflowPlan) -> None:
        init_db()
        now = _now()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs
                  (id, chat_id, title, original_user_message, status, plan_json,
                   result_json, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  title=excluded.title, status=excluded.status,
                  plan_json=excluded.plan_json, updated_at=excluded.updated_at
                """,
                (plan.id, plan.chat_id, plan.title, plan.original_user_message,
                 "running", plan.model_dump_json(), None, plan.created_at, now),
            )
        logger.info("workflow_saved workflow_id=%s actions=%d", plan.id, len(plan.actions))

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

    def save_result(self, plan: WorkflowPlan, result: WorkflowExecutionResult) -> None:
        init_db()
        with connect() as conn:
            conn.execute(
                "UPDATE workflow_runs SET status=?, result_json=?, plan_json=?, updated_at=? WHERE id=?",
                (result.status.value, result.model_dump_json(), plan.model_dump_json(),
                 _now(), plan.id),
            )

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
                "WHERE id=? AND chat_id=? AND status IN ('running','pending')",
                (_now(), workflow_id, chat_id),
            )
            return cur.rowcount > 0
