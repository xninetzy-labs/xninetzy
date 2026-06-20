from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")


def log_workout(workout_type: str, exercises: list[dict] | None = None,
                duration: int | None = None, intensity: str = "medium",
                notes: str = "", date: str | None = None) -> dict:
    init_db()
    now = _now()
    workout_date = date or _today()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO workout_logs (workout_date, type, exercises_json, duration_minutes, intensity, notes, created_at) VALUES (?,?,?,?,?,?,?)",
            (workout_date, workout_type, json.dumps(exercises or [], ensure_ascii=False),
             duration, intensity, notes, now),
        )
        return {"id": cur.lastrowid, "date": workout_date, "type": workout_type, "duration": duration}


def get_workout_summary(period: str = "week") -> dict:
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    days = 7 if period == "week" else 30
    since = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM workout_logs WHERE workout_date >= ? ORDER BY workout_date DESC",
            (since,),
        ).fetchall()
    sessions = [dict(r) for r in rows]
    total_min = sum(s.get("duration_minutes") or 0 for s in sessions)
    return {
        "period": period,
        "session_count": len(sessions),
        "total_minutes": total_min,
        "sessions": sessions[:10],
    }
