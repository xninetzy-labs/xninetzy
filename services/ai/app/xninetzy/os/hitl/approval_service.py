from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect
from app.xninetzy.os.research.permissions import is_owner_admin


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def request_approval(
    chat_id: str | None,
    sender_id: str | None,
    action_type: str,
    title: str,
    summary: str,
    payload: dict | None = None,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO approval_requests
              (chat_id, sender_id, action_type, title, summary, payload_json, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (chat_id, sender_id, action_type, title, summary, json.dumps(payload or {}, ensure_ascii=False), "pending", _now()),
        )
        return int(cur.lastrowid)


def list_pending() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM approval_requests WHERE status='pending' ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return [dict(row) for row in rows]


def set_approval_status(approval_id: int, status: str, sender_id: str | None, sender_name: str | None) -> tuple[bool, str]:
    if not is_owner_admin(sender_id, sender_name):
        return False, "Maaf, approval ini hanya bisa dilakukan oleh admin."
    column = "approved_at" if status == "approved" else "rejected_at"
    with connect() as conn:
        row = conn.execute("SELECT * FROM approval_requests WHERE id=?", (approval_id,)).fetchone()
        if not row:
            return False, f"Approval #{approval_id} tidak ditemukan."
        if row["status"] != "pending":
            return False, f"Approval #{approval_id} sudah berstatus {row['status']}."
        conn.execute(
            f"UPDATE approval_requests SET status=?, {column}=? WHERE id=?",
            (status, _now(), approval_id),
        )
    return True, f"Approval #{approval_id} {status}."


def get_approval_status(approval_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM approval_requests WHERE id=?", (approval_id,)).fetchone()
    return dict(row) if row else None
