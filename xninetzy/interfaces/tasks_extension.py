from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from langchain_core.tools import tool

from xninetzy.core.logging import logging
from xninetzy.db.sqlite import connect
from xninetzy.os.research.permissions import is_owner_admin

logger = logging.getLogger(__name__)

_TASK_DDL = """
CREATE TABLE IF NOT EXISTS long_tasks (
  task_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  owner TEXT,
  payload_json TEXT,
  result_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  error TEXT
)
"""


@dataclass
class LongTask:
    task_id: str
    name: str
    status: str
    owner: str | None
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    with connect() as conn:
        conn.execute(_TASK_DDL)


def _serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def _row_to_task(row: Any) -> LongTask:
    return LongTask(
        task_id=row["task_id"],
        name=row["name"],
        status=row["status"],
        owner=row["owner"],
        payload=json.loads(row["payload_json"] or "{}"),
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error=row["error"],
    )


def _record(task: LongTask) -> None:
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO long_tasks
              (task_id, name, status, owner, payload_json, result_json, created_at, updated_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
              status=excluded.status,
              result_json=excluded.result_json,
              updated_at=excluded.updated_at,
              error=excluded.error
            """,
            (
                task.task_id,
                task.name,
                task.status,
                task.owner,
                _serialize(task.payload),
                _serialize(task.result) if task.result is not None else None,
                task.created_at,
                task.updated_at,
                task.error,
            ),
        )


def _load(task_id: str) -> LongTask | None:
    _ensure_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM long_tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
    return _row_to_task(row) if row else None


async def _run_task(
    coro_factory: Callable[[], Awaitable[dict[str, Any]]],
    task: LongTask,
) -> None:
    try:
        result = await coro_factory()
        task.status = "completed"
        task.result = result
        task.updated_at = _now()
        _record(task)
    except asyncio.CancelledError:
        task.status = "cancelled"
        task.updated_at = _now()
        task.error = "cancelled"
        _record(task)
        raise
    except Exception as exc:
        task.status = "failed"
        task.error = f"{type(exc).__name__}: {exc}"
        task.updated_at = _now()
        _record(task)
        logger.warning("long_task %s failed: %s", task.task_id, exc)


def submit_long_task(
    name: str,
    coro_factory: Callable[[], Awaitable[dict[str, Any]]],
    *,
    owner: str | None = None,
    payload: dict[str, Any] | None = None,
) -> LongTask:
    task = LongTask(
        task_id=f"task-{uuid.uuid4().hex[:16]}",
        name=name,
        status="running",
        owner=owner,
        payload=payload or {},
        created_at=_now(),
        updated_at=_now(),
    )
    _record(task)
    task.created_at = task.created_at
    task.updated_at = task.updated_at
    coro = _run_task(coro_factory, task)
    asyncio.create_task(coro)
    return task


@tool
def tasks_submit(
    name: str,
    payload_json: str = "{}",
    sender_id: str = "",
    sender_name: str = "",
) -> str:
    """Daftarkan task panjang (placeholder). Pemanggil harus menyediakan handler via tool lain."""
    if not is_owner_admin(sender_id, sender_name):
        return json.dumps({"error": "Hanya owner yang dapat mendaftarkan task."}, ensure_ascii=False)
    try:
        payload = json.loads(payload_json or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "payload_json harus JSON object."}, ensure_ascii=False)
    if not isinstance(payload, dict):
        return json.dumps({"error": "payload_json harus JSON object."}, ensure_ascii=False)
    task = LongTask(
        task_id=f"task-{uuid.uuid4().hex[:16]}",
        name=name,
        status="pending",
        owner=sender_id or None,
        payload=payload,
        created_at=_now(),
        updated_at=_now(),
    )
    _record(task)
    return json.dumps({
        "task_id": task.task_id,
        "status": task.status,
        "name": task.name,
        "submitted_at": task.created_at,
    }, ensure_ascii=False)


@tool
def tasks_get(task_id: str) -> str:
    """Ambil status task panjang via Tasks extension (`io.modelcontextprotocol/tasks`)."""
    task = _load(task_id)
    if task is None:
        return json.dumps({"error": f"task_id {task_id!r} tidak ditemukan"}, ensure_ascii=False)
    return json.dumps(asdict(task), ensure_ascii=False, default=str)


@tool
def tasks_cancel(task_id: str, sender_id: str = "", sender_name: str = "") -> str:
    """Tandai task panjang sebagai cancelled. Eksekusi aktif tidak otomatis dihentikan."""
    if not is_owner_admin(sender_id, sender_name):
        return json.dumps({"error": "Hanya owner yang dapat membatalkan task."}, ensure_ascii=False)
    task = _load(task_id)
    if task is None:
        return json.dumps({"error": f"task_id {task_id!r} tidak ditemukan"}, ensure_ascii=False)
    if task.status in {"completed", "failed", "cancelled"}:
        return json.dumps({"status": task.status, "task_id": task_id, "note": "task sudah selesai"}, ensure_ascii=False)
    task.status = "cancelled"
    task.updated_at = _now()
    _record(task)
    return json.dumps({"status": task.status, "task_id": task_id, "cancelled_at": task.updated_at}, ensure_ascii=False)


@tool
def tasks_list(limit: int = 20) -> str:
    """Daftar task panjang terbaru."""
    _ensure_db()
    bounded = max(1, min(int(limit), 200))
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM long_tasks ORDER BY updated_at DESC LIMIT ?",
            (bounded,),
        ).fetchall()
    return json.dumps([asdict(_row_to_task(row)) for row in rows], ensure_ascii=False, default=str)


TASKS_TOOLS = [tasks_submit, tasks_get, tasks_cancel, tasks_list]
