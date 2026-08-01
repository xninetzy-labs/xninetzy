from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect
from app.xninetzy.os.policy.action_policy import action_hash
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
    expires_in_seconds: int | None = None,
) -> int:
    settings = get_settings()
    data = dict(payload or {})
    created = datetime.now(ZoneInfo(settings.APP_TIMEZONE))
    expires = created + timedelta(
        seconds=max(1, expires_in_seconds or settings.ACTION_POLICY_TTL_SECONDS)
    )
    digest = action_hash(action_type, data)
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO approval_requests
              (chat_id, sender_id, action_type, title, summary, payload_json,
               status, created_at, expires_at, action_hash)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                chat_id,
                sender_id,
                action_type,
                title,
                summary,
                json.dumps(data, ensure_ascii=False),
                "pending",
                created.isoformat(),
                expires.isoformat(),
                digest,
            ),
        )
        return int(cur.lastrowid)


def list_pending() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM approval_requests WHERE status='pending' ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return [dict(row) for row in rows]


def _execute_approved_action(row: dict) -> str:
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


def _expired(row: dict) -> bool:
    value = row.get("expires_at")
    if not value:
        return False
    return datetime.fromisoformat(value) < datetime.now(
        ZoneInfo(get_settings().APP_TIMEZONE)
    )


def set_approval_status(
    approval_id: int,
    status: str,
    sender_id: str | None,
    sender_name: str | None,
) -> tuple[bool, str]:
    if status not in {"approved", "rejected"}:
        return False, "Status approval tidak valid."
    if not is_owner_admin(sender_id, sender_name):
        return False, "Maaf, approval ini hanya bisa dilakukan oleh admin."
    column = "approved_at" if status == "approved" else "rejected_at"
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM approval_requests WHERE id=?", (approval_id,)
        ).fetchone()
        if not row:
            return False, f"Approval #{approval_id} tidak ditemukan."
        row_data = dict(row)
        if row["status"] != "pending":
            if row["status"] == "approved" and status == "approved":
                return True, f"Approval #{approval_id} sudah berstatus approved."
            return False, f"Approval #{approval_id} sudah berstatus {row['status']}."
        if _expired(row_data):
            conn.execute(
                "UPDATE approval_requests SET status='expired', rejected_at=? WHERE id=?",
                (_now(), approval_id),
            )
            return False, f"Approval #{approval_id} sudah kedaluwarsa."
        conn.execute(
            f"UPDATE approval_requests SET status=?, {column}=? WHERE id=?",
            (status, _now(), approval_id),
        )
    if status != "approved":
        return True, f"Approval #{approval_id} rejected."
    try:
        action_message = _execute_approved_action(row_data)
    except Exception as exc:
        with connect() as conn:
            conn.execute(
                """
                UPDATE approval_requests
                SET status='execution_failed', execution_at=?, execution_result=?
                WHERE id=?
                """,
                (_now(), str(exc), approval_id),
            )
        return False, f"Approval #{approval_id} disetujui tetapi eksekusi gagal: {exc}"
    with connect() as conn:
        conn.execute(
            "UPDATE approval_requests SET execution_at=?, execution_result=? WHERE id=?",
            (_now(), action_message, approval_id),
        )
    return True, f"Approval #{approval_id} approved.{action_message}"


def get_approval_status(approval_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM approval_requests WHERE id=?", (approval_id,)
        ).fetchone()
    return dict(row) if row else None


def validate_approval(
    approval_id: int,
    action_type: str,
    expected_hash: str,
) -> dict:
    row = get_approval_status(approval_id)
    if not row:
        raise ValueError(f"Approval #{approval_id} tidak ditemukan.")
    if row["status"] != "approved":
        raise ValueError(f"Approval #{approval_id} belum approved.")
    if row.get("action_type") != action_type:
        raise ValueError("Jenis aksi approval tidak cocok.")
    if row.get("action_hash") != expected_hash:
        raise ValueError("Isi aksi berubah; approval lama tidak berlaku.")
    if _expired(row):
        raise ValueError(f"Approval #{approval_id} sudah kedaluwarsa.")
    return row
