"""Minimal SEP-2663 Tasks extension surface for Xninetzy.

Each task is a durable handle stored in SQLite. The handle survives
process restart. The result field holds the eventual JSON output of
the underlying tool or workflow action.

This module deliberately implements only the four primitives the MCP
Tasks draft calls for: ``tasks/get``, ``tasks/list``, ``tasks/cancel``,
and ``tasks/result``. Status transitions follow
``queued -> running -> completed | failed | cancelled``.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from xninetzy.db.sqlite import connect, init_db


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.QUEUED: {TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_table() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_tasks (
                id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                arguments_json TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error TEXT,
                owner TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mcp_tasks_owner_status "
            "ON mcp_tasks(owner, status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mcp_tasks_chat "
            "ON mcp_tasks(chat_id, created_at DESC)"
        )


@dataclass(frozen=True, slots=True)
class TaskRecord:
    id: str
    tool_name: str
    status: TaskStatus
    owner: str
    chat_id: str
    created_at: str
    updated_at: str
    arguments_json: str
    result_json: str | None
    error: str | None
    idempotency_key: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "owner": self.owner,
            "chat_id": self.chat_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "arguments_json": self.arguments_json,
            "result_json": self.result_json,
            "error": self.error,
            "idempotency_key": self.idempotency_key,
        }


def _row_to_record(row: Any) -> TaskRecord:
    return TaskRecord(
        id=row["id"],
        tool_name=row["tool_name"],
        status=TaskStatus(row["status"]),
        owner=row["owner"],
        chat_id=row["chat_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        arguments_json=row["arguments_json"],
        result_json=row["result_json"],
        error=row["error"],
        idempotency_key=row["idempotency_key"],
    )


def create_task(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    owner: str,
    chat_id: str,
    idempotency_key: str | None = None,
    task_id: str | None = None,
) -> TaskRecord:
    """Persist a new task handle. Idempotent on ``idempotency_key``."""
    _ensure_table()
    tid = task_id or f"task-{uuid.uuid4().hex[:12]}"
    now = _utcnow()
    args_json = json.dumps(arguments, ensure_ascii=False, sort_keys=True, default=str)
    if idempotency_key:
        with connect() as conn:
            existing = conn.execute(
                "SELECT * FROM mcp_tasks WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                return _row_to_record(existing)
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO mcp_tasks
                (id, tool_name, arguments_json, status, result_json, error,
                 owner, chat_id, idempotency_key, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (tid, tool_name, args_json, TaskStatus.QUEUED.value, None, None,
             owner, chat_id, idempotency_key, now, now),
        )
        row = conn.execute("SELECT * FROM mcp_tasks WHERE id=?", (tid,)).fetchone()
    assert row is not None
    return _row_to_record(row)


def get_task(task_id: str) -> TaskRecord | None:
    _ensure_table()
    with connect() as conn:
        row = conn.execute("SELECT * FROM mcp_tasks WHERE id=?", (task_id,)).fetchone()
    return _row_to_record(row) if row else None


def list_tasks(
    *,
    owner: str | None = None,
    chat_id: str | None = None,
    statuses: list[TaskStatus] | None = None,
    limit: int = 20,
) -> list[TaskRecord]:
    _ensure_table()
    clauses: list[str] = []
    params: list[Any] = []
    if owner:
        clauses.append("owner=?")
        params.append(owner)
    if chat_id:
        clauses.append("chat_id=?")
        params.append(chat_id)
    if statuses:
        placeholders = ",".join("?" for _ in statuses)
        clauses.append(f"status IN ({placeholders})")
        params.extend(s.value for s in statuses)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(int(limit))
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM mcp_tasks {where} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def transition(
    task_id: str,
    *,
    to: TaskStatus,
    result: Any = None,
    error: str | None = None,
) -> TaskRecord | None:
    _ensure_table()
    current = get_task(task_id)
    if current is None:
        return None
    if to not in _VALID_TRANSITIONS[current.status]:
        return current
    result_json = None if result is None else json.dumps(
        result, ensure_ascii=False, sort_keys=True, default=str
    )
    with connect() as conn:
        conn.execute(
            "UPDATE mcp_tasks SET status=?, result_json=?, error=?, updated_at=? WHERE id=?",
            (to.value, result_json, error, _utcnow(), task_id),
        )
    return get_task(task_id)


def cancel(task_id: str) -> TaskRecord | None:
    record = get_task(task_id)
    if record is None or record.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
        return record
    return transition(task_id, to=TaskStatus.CANCELLED, error="cancelled by owner")


def result_of(task_id: str) -> dict[str, Any]:
    record = get_task(task_id)
    if record is None:
        return {"error": f"unknown task: {task_id}"}
    payload: dict[str, Any] = {
        "id": record.id,
        "status": record.status.value,
        "tool_name": record.tool_name,
        "updated_at": record.updated_at,
    }
    if record.status == TaskStatus.COMPLETED:
        payload["result"] = json.loads(record.result_json) if record.result_json else None
    elif record.status == TaskStatus.FAILED:
        payload["error"] = record.error
    elif record.status == TaskStatus.CANCELLED:
        payload["error"] = record.error or "cancelled"
    return payload
