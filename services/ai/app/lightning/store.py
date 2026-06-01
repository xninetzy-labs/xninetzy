from __future__ import annotations

import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ── Traces ──────────────────────────────────────────────────────────────────

def log_trace(
    *,
    user_id: str | None,
    chat_id: str | None,
    message_id: str | None,
    input_text: str,
    response_text: str,
    intent: str | None = None,
    tools_used: list[str] | None = None,
    context_sources: list[str] | None = None,
    confidence: float | None = None,
    status: str = "ok",
    error_type: str | None = None,
    error_message: str | None = None,
) -> str:
    init_db()
    trace_id = _uuid("T")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_traces
              (trace_id, user_id, chat_id, message_id, input_text, intent,
               context_sources_json, tools_used_json, response_text, confidence,
               status, error_type, error_message, metadata_json, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (trace_id, user_id, chat_id, message_id, (input_text or "")[:4000], intent,
             json.dumps(context_sources or [], ensure_ascii=False),
             json.dumps(tools_used or [], ensure_ascii=False),
             (response_text or "")[:4000], confidence, status, error_type,
             (error_message or None), "{}", _now()),
        )
    return trace_id


def latest_trace(chat_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM agent_traces WHERE chat_id=? ORDER BY id DESC LIMIT 1", (chat_id,)
        ).fetchone()
    return dict(row) if row else None


def recent_error_traces(limit: int = 20) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_traces WHERE status!='ok' ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Feedback ────────────────────────────────────────────────────────────────

def log_feedback(
    *,
    user_id: str | None,
    chat_id: str | None,
    message_id: str | None,
    trace_id: str | None,
    feedback_type: str,
    feedback_text: str,
    severity: str = "medium",
    parsed_issue: dict | None = None,
) -> str:
    init_db()
    fid = _uuid("F")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_feedback
              (feedback_id, user_id, chat_id, message_id, trace_id, feedback_type,
               feedback_text, severity, parsed_issue_json, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (fid, user_id, chat_id, message_id, trace_id, feedback_type,
             feedback_text[:2000], severity, json.dumps(parsed_issue or {}, ensure_ascii=False), _now()),
        )
    return fid


# ── Proposals ───────────────────────────────────────────────────────────────

def create_proposal(
    *,
    source_type: str,
    source_id: str | None,
    user_id: str | None,
    title: str,
    problem: str,
    proposed_change: str,
    target_area: str,
    patch: dict | None = None,
    risk_level: str = "low",
) -> dict:
    init_db()
    pid = _uuid("P")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO improvement_proposals
              (proposal_id, source_type, source_id, user_id, title, problem,
               proposed_change, target_area, patch_json, risk_level, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?, 'pending', ?)
            """,
            (pid, source_type, source_id, user_id, title[:120], problem[:2000],
             proposed_change[:2000], target_area, json.dumps(patch or {}, ensure_ascii=False),
             risk_level, _now()),
        )
        return {"id": int(cur.lastrowid), "proposal_id": pid, "title": title, "target_area": target_area}


def list_proposals(status: str | None = "pending", limit: int = 20) -> list[dict]:
    init_db()
    with connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM improvement_proposals WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM improvement_proposals ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def get_proposal(proposal_pk: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM improvement_proposals WHERE id=?", (proposal_pk,)
        ).fetchone()
    return dict(row) if row else None


def set_proposal_status(proposal_pk: int, status: str, reviewed_by: str | None) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE improvement_proposals SET status=?, reviewed_at=?, reviewed_by=? WHERE id=?",
            (status, _now(), reviewed_by, proposal_pk),
        )
        return cur.rowcount > 0
