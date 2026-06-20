from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")


def create_habit(name: str, domain: str = "personal", frequency: str = "daily",
                 target_count: int = 1) -> dict:
    init_db()
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO habits (name, domain, frequency, target_count, status, created_at) VALUES (?,?,?,?,?,?)",
            (name, domain, frequency, target_count, "active", now),
        )
        if cur.lastrowid:
            row = conn.execute("SELECT * FROM habits WHERE id=?", (cur.lastrowid,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM habits WHERE name=?", (name,)).fetchone()
    return dict(row) if row else {"name": name}


def log_habit(name: str, value: int = 1, notes: str = "", date: str | None = None) -> dict:
    init_db()
    today = date or _today()
    now = _now()
    with connect() as conn:
        habit = conn.execute("SELECT id FROM habits WHERE name=?", (name,)).fetchone()
        if not habit:
            cur = conn.execute(
                "INSERT INTO habits (name, domain, frequency, target_count, status, created_at) VALUES (?,?,?,?,?,?)",
                (name, "personal", "daily", 1, "active", now),
            )
            habit_id = cur.lastrowid
        else:
            habit_id = habit["id"]
        cur = conn.execute(
            "INSERT INTO habit_logs (habit_id, log_date, value, notes, created_at) VALUES (?,?,?,?,?)",
            (habit_id, today, value, notes, now),
        )
    return {"habit": name, "date": today, "value": value}


def get_habit_today() -> list[dict]:
    init_db()
    today = _today()
    with connect() as conn:
        habits = conn.execute("SELECT * FROM habits WHERE status='active'").fetchall()
        result = []
        for h in habits:
            log = conn.execute(
                "SELECT SUM(value) as done FROM habit_logs WHERE habit_id=? AND log_date=?",
                (h["id"], today),
            ).fetchone()
            done = log["done"] or 0
            result.append({
                **dict(h),
                "done_today": done,
                "completed": done >= h["target_count"],
            })
    return result


def get_habit_summary(period: str = "week") -> list[dict]:
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    days = 7 if period == "week" else 30
    since = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    with connect() as conn:
        habits = conn.execute("SELECT * FROM habits WHERE status='active'").fetchall()
        result = []
        for h in habits:
            row = conn.execute(
                "SELECT COUNT(DISTINCT log_date) as days, SUM(value) as total FROM habit_logs WHERE habit_id=? AND log_date>=?",
                (h["id"], since),
            ).fetchone()
            result.append({
                **dict(h),
                "days_completed": row["days"] or 0,
                "total_value": row["total"] or 0,
                "streak_rate": f"{(row['days'] or 0) / days * 100:.0f}%",
            })
    return result
