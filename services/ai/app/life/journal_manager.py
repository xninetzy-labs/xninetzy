from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")


def checkin(mood: int, energy: int, focus: int, summary: str) -> dict:
    init_db()
    today = _today()
    now = _now()
    with connect() as conn:
        row = conn.execute("SELECT id FROM daily_reviews WHERE date=?", (today,)).fetchone()
        if row:
            conn.execute(
                "UPDATE daily_reviews SET mood=?, energy=?, focus=?, summary=? WHERE date=?",
                (mood, energy, focus, summary, today),
            )
            rid = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO daily_reviews (date, mood, energy, focus, summary, created_at) VALUES (?,?,?,?,?,?)",
                (today, mood, energy, focus, summary, now),
            )
            rid = cur.lastrowid
    return {"id": rid, "date": today, "mood": mood, "energy": energy, "focus": focus}


def get_review(date: str | None = None) -> dict | None:
    init_db()
    d = date or _today()
    with connect() as conn:
        row = conn.execute("SELECT * FROM daily_reviews WHERE date=?", (d,)).fetchone()
    return dict(row) if row else None


def get_latest_review() -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM daily_reviews ORDER BY date DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def save_review(date: str, wins: str, problems: str, next_actions: str,
                ai_feedback: str, obsidian_path: str | None = None) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE daily_reviews SET wins=?, problems=?, next_actions=?, ai_feedback=?, obsidian_path=? WHERE date=?",
            (wins, problems, next_actions, ai_feedback, obsidian_path, date),
        )


def list_reviews(limit: int = 7) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_reviews ORDER BY date DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
