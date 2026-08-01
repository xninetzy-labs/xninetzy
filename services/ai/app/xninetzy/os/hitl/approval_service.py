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


def _execute_approved_action(row: dict) -> str:
    """Execute the approved payload. Handlers must be idempotent."""
    payload = json.loads(row.get("payload_json") or "{}")
    if row.get("action_type") == "activate_learning_roadmap":
        from app.xninetzy.domains.it_learning.roadmap_store import activate_roadmap

        roadmap_id = int(payload["roadmap_id"])
        if not activate_roadmap(roadmap_id):
            raise ValueError(f"Roadmap #{roadmap_id} tidak ditemukan.")
        return f" Roadmap #{roadmap_id} diaktifkan dan task belajar disiapkan."
    if row.get("action_type") == "graph_rebuild":
        from app.xninetzy.os.graph.v3 import graph_service

        result = graph_service.rebuild_projection()
        return (
            f" Rebuild GraphRAG V3: neo4j_wiped={result['neo4j_wiped']}, "
            f"faiss_rows={result['faiss_rows']}, "
            f"outbox_enqueued={result['outbox_enqueued']}."
        )
    return ""


def set_approval_status(approval_id: int, status: str, sender_id: str | None, sender_name: str | None) -> tuple[bool, str]:
    if not is_owner_admin(sender_id, sender_name):
        return False, "Maaf, approval ini hanya bisa dilakukan oleh admin."
    column = "approved_at" if status == "approved" else "rejected_at"
    with connect() as conn:
        row = conn.execute("SELECT * FROM approval_requests WHERE id=?", (approval_id,)).fetchone()
        if not row:
            return False, f"Approval #{approval_id} tidak ditemukan."
        row_data = dict(row)
        if row["status"] != "pending":
            if row["status"] == "approved" and status == "approved":
                action_message = _execute_approved_action(row_data)
                return True, f"Approval #{approval_id} sudah berstatus approved.{action_message}"
            return False, f"Approval #{approval_id} sudah berstatus {row['status']}."
        conn.execute(
            f"UPDATE approval_requests SET status=?, {column}=? WHERE id=?",
            (status, _now(), approval_id),
        )
    if status == "approved":
        action_message = _execute_approved_action(row_data)
    else:
        action_message = ""
    return True, f"Approval #{approval_id} {status}.{action_message}"


def get_approval_status(approval_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM approval_requests WHERE id=?", (approval_id,)).fetchone()
    return dict(row) if row else None
