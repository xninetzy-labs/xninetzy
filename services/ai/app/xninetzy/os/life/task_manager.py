from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")


def create_task(title: str, description: str = "", priority: str = "medium",
                due_at: str | None = None, goal_id: int | None = None,
                domain: str | None = None, source: str = "manual") -> dict:
    init_db()
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks
              (title, description, status, priority, domain, goal_id, due_at, source, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (title, description, "inbox", priority, domain, goal_id, due_at, source, now, now),
        )
        tid = cur.lastrowid
    return get_task(tid) or {"id": tid, "title": title}


def get_task(task_id: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(status: str | None = None, priority: str | None = None,
               domain: str | None = None, limit: int = 30) -> list[dict]:
    init_db()
    sql = "SELECT * FROM tasks WHERE status NOT IN ('done','cancelled')"
    params: list = []
    if status:
        sql = "SELECT * FROM tasks WHERE status=?"
        params.append(status)
    if priority:
        sql += " AND priority=?"
        params.append(priority)
    if domain:
        sql += " AND domain=?"
        params.append(domain)
    sql += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, due_at ASC NULLS LAST LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def list_tasks_today() -> list[dict]:
    """Tasks due today or overdue, plus scheduled for today."""
    init_db()
    today = _today()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE status NOT IN ('done','cancelled')
              AND (due_at <= ? OR scheduled_at = ?)
            ORDER BY priority DESC, due_at ASC NULLS LAST
            LIMIT 15
            """,
            (today + "T23:59:59", today),
        ).fetchall()
    return [dict(r) for r in rows]


def complete_task(task_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET status='done', updated_at=? WHERE id=?",
            (_now(), task_id),
        )


def update_task_status(task_id: int, status: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE id=?",
            (status, _now(), task_id),
        )
