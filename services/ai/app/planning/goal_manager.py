from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


VALID_DOMAINS = {"learning", "career", "health", "money", "relationship", "project", "spiritual", "personal"}
VALID_HORIZONS = {"daily", "weekly", "monthly", "quarterly", "yearly", "lifetime"}
VALID_STATUS = {"active", "paused", "completed", "cancelled"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def create_goal(title: str, description: str = "", domain: str = "personal",
                horizon: str = "monthly", priority: str = "medium",
                due_date: str | None = None, target_metric: str | None = None,
                target_value: float | None = None, unit: str | None = None) -> dict:
    init_db()
    now = _now()
    domain = domain if domain in VALID_DOMAINS else "personal"
    horizon = horizon if horizon in VALID_HORIZONS else "monthly"
    priority = priority if priority in VALID_PRIORITIES else "medium"
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO life_goals
              (title, description, domain, horizon, status, priority,
               target_metric, target_value, unit, due_date, start_date, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (title, description, domain, horizon, "active", priority,
             target_metric, target_value, unit, due_date, now[:10], now, now),
        )
        gid = cur.lastrowid
    return get_goal(gid) or {"id": gid, "title": title}


def get_goal(goal_id: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM life_goals WHERE id=?", (goal_id,)).fetchone()
    return dict(row) if row else None


def list_goals(status: str | None = "active", domain: str | None = None,
               limit: int = 20) -> list[dict]:
    init_db()
    sql = "SELECT * FROM life_goals WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if domain:
        sql += " AND domain=?"
        params.append(domain)
    sql += " ORDER BY priority DESC, created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def log_progress(goal_id: int, log_text: str, delta: float = 0,
                 mood: int | None = None, confidence: int | None = None) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            "INSERT INTO life_goal_logs (goal_id, log_text, progress_delta, mood, confidence, created_at) VALUES (?,?,?,?,?,?)",
            (goal_id, log_text, delta, mood, confidence, now),
        )
        if delta:
            conn.execute(
                "UPDATE life_goals SET current_value=current_value+?, updated_at=? WHERE id=?",
                (delta, now, goal_id),
            )


def update_goal_status(goal_id: int, status: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE life_goals SET status=?, updated_at=? WHERE id=?",
            (status, _now(), goal_id),
        )


def get_goal_logs(goal_id: int, limit: int = 10) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM life_goal_logs WHERE goal_id=? ORDER BY id DESC LIMIT ?",
            (goal_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
