from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


_SAFETY_KW = (
    "jangan submit", "jangan upload", "jangan hapus", "jangan kirim ke semua",
    "jangan tag semua", "jangan serang", "keamanan", "auto-submit", "auto submit",
)
_STYLE_KW = ("gaya", "style", "jawab dengan", "nada", "tone", "format", "singkat", "ringkas")
_DONT_KW = ("jangan", "dont", "don't", "stop", "hindari", "no ")
_DO_KW = ("selalu", "harus", "always", "wajib", "tolong selalu", "pastikan")


def classify_rule(content: str) -> str:
    c = content.lower()
    if any(k in c for k in _SAFETY_KW):
        return "safety"
    if any(k in c for k in _STYLE_KW):
        return "style"
    if any(k in c for k in _DONT_KW):
        return "dont"
    if any(k in c for k in _DO_KW):
        return "do"
    return "do"


def add_rule(
    user_id: str,
    content: str,
    rule_type: str | None = None,
    priority: int = 50,
    source_message_id: str | None = None,
) -> dict:
    init_db()
    now = _now()
    rt = rule_type or classify_rule(content)
    # safety rules win ties
    if priority == 50 and rt == "safety":
        priority = 90
    rid = uuid.uuid4().hex[:12]
    title = content.strip()[:60]
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO user_rules
              (rule_id, user_id, scope, rule_type, title, content, priority,
               is_active, created_from, source_message_id, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,1,?,?,?,?,?)
            """,
            (rid, user_id, "personal", rt, title, content.strip(), priority,
             "whatsapp", source_message_id, "{}", now, now),
        )
        return {"id": int(cur.lastrowid), "rule_id": rid, "rule_type": rt, "content": content.strip()}


def list_rules(user_id: str, active_only: bool = False, limit: int = 50) -> list[dict]:
    init_db()
    sql = "SELECT * FROM user_rules WHERE user_id=?"
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY priority DESC, id DESC LIMIT ?"
    with connect() as conn:
        rows = conn.execute(sql, (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get_active_rules(user_id: str, limit: int = 30) -> list[dict]:
    return list_rules(user_id, active_only=True, limit=limit)


def set_active(user_id: str, rule_pk: int, active: bool) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE user_rules SET is_active=?, updated_at=? WHERE id=? AND user_id=?",
            (1 if active else 0, _now(), rule_pk, user_id),
        )
        return cur.rowcount > 0


def delete_rule(user_id: str, rule_pk: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM user_rules WHERE id=? AND user_id=?", (rule_pk, user_id)
        )
        return cur.rowcount > 0


def search_rules(user_id: str, query: str, limit: int = 20) -> list[dict]:
    init_db()
    needle = f"%{query}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM user_rules
            WHERE user_id=? AND (content LIKE ? OR rule_type LIKE ?)
            ORDER BY priority DESC, id DESC LIMIT ?
            """,
            (user_id, needle, needle, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def format_rules_for_prompt(rules: list[dict]) -> str:
    if not rules:
        return ""
    lines = [f"• [{r['rule_type']}] {r['content']}" for r in rules]
    return "\n[Aturan dari user — WAJIB dipatuhi]\n" + "\n".join(lines) + "\n"
