from __future__ import annotations

import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


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
    metadata: dict | None = None,
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
            (
                trace_id,
                user_id,
                chat_id,
                message_id,
                (input_text or "")[:4000],
                intent,
                json.dumps(context_sources or [], ensure_ascii=False),
                json.dumps(tools_used or [], ensure_ascii=False),
                (response_text or "")[:4000],
                confidence,
                status,
                error_type,
                error_message or None,
                json.dumps(metadata or {}, ensure_ascii=False),
                _now(),
            ),
        )
    return trace_id


def latest_trace(chat_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM agent_traces WHERE chat_id=? ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ).fetchone()
    return dict(row) if row else None


def trace_for_message(
    *,
    chat_id: str | None,
    message_id: str | None,
    trace_id: str | None = None,
) -> dict | None:
    init_db()
    clauses: list[str] = []
    params: list[str] = []
    if trace_id:
        clauses.append("trace_id=?")
        params.append(trace_id)
    if message_id:
        clauses.append("message_id=?")
        params.append(message_id)
    if chat_id:
        clauses.append("chat_id=?")
        params.append(chat_id)
    if not clauses:
        return None
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM agent_traces WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT 1",
            params,
        ).fetchone()
    return dict(row) if row else None


def recent_error_traces(limit: int = 20) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_traces WHERE status!='ok' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


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
    episode_id: str | None = None,
    idempotency_key: str | None = None,
    source_interface: str = "internal",
    attribution_confidence: str = "explicit",
) -> str:
    init_db()
    if idempotency_key:
        with connect() as conn:
            existing = conn.execute(
                "SELECT feedback_id FROM agent_feedback WHERE user_id=? AND idempotency_key=?",
                (user_id, idempotency_key),
            ).fetchone()
            if existing:
                return existing["feedback_id"]
    fid = _uuid("F")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_feedback
              (feedback_id, user_id, chat_id, message_id, trace_id, feedback_type,
               feedback_text, severity, parsed_issue_json, created_at, episode_id,
               idempotency_key, source_interface, attribution_confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                fid,
                user_id,
                chat_id,
                message_id,
                trace_id,
                feedback_type,
                feedback_text[:2000],
                severity,
                json.dumps(parsed_issue or {}, ensure_ascii=False),
                _now(),
                episode_id,
                idempotency_key,
                source_interface,
                attribution_confidence,
            ),
        )
    return fid


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
    confidence: float = 0.0,
    risk_score: float = 0.0,
    evidence: dict | None = None,
    baseline_metrics: dict | None = None,
    candidate_metrics: dict | None = None,
    rollout_state: str = "pending",
    rollback: dict | None = None,
    expires_at: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    init_db()
    if idempotency_key:
        with connect() as conn:
            existing = conn.execute(
                "SELECT id, proposal_id, title, target_area FROM improvement_proposals WHERE user_id=? AND idempotency_key=?",
                (user_id, idempotency_key),
            ).fetchone()
            if existing:
                return dict(existing)
    pid = _uuid("P")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO improvement_proposals
              (proposal_id, source_type, source_id, user_id, title, problem,
               proposed_change, target_area, patch_json, risk_level, status,
               created_at, confidence, risk_score, evidence_json,
               baseline_metrics_json, candidate_metrics_json, rollout_state,
               rollback_json, expires_at, idempotency_key)
            VALUES (?,?,?,?,?,?,?,?,?,?, 'pending', ?,?,?,?,?,?,?,?,?,?)
            """,
            (
                pid,
                source_type,
                source_id,
                user_id,
                title[:120],
                problem[:2000],
                proposed_change[:2000],
                target_area,
                json.dumps(patch or {}, ensure_ascii=False),
                risk_level,
                _now(),
                max(0.0, min(1.0, confidence)),
                max(0.0, min(1.0, risk_score)),
                json.dumps(evidence or {}, ensure_ascii=False),
                json.dumps(baseline_metrics or {}, ensure_ascii=False),
                json.dumps(candidate_metrics or {}, ensure_ascii=False),
                rollout_state,
                json.dumps(rollback or {}, ensure_ascii=False),
                expires_at,
                idempotency_key,
            ),
        )
        return {
            "id": int(cur.lastrowid),
            "proposal_id": pid,
            "title": title,
            "target_area": target_area,
            "confidence": confidence,
            "risk_score": risk_score,
        }


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
                "SELECT * FROM improvement_proposals ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_proposal(proposal_pk: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM improvement_proposals WHERE id=?",
            (proposal_pk,),
        ).fetchone()
    return dict(row) if row else None


def set_proposal_status(
    proposal_pk: int,
    status: str,
    reviewed_by: str | None,
    rollout_state: str | None = None,
) -> bool:
    init_db()
    with connect() as conn:
        if rollout_state is None:
            cur = conn.execute(
                "UPDATE improvement_proposals SET status=?, reviewed_at=?, reviewed_by=? WHERE id=?",
                (status, _now(), reviewed_by, proposal_pk),
            )
        else:
            cur = conn.execute(
                "UPDATE improvement_proposals SET status=?, rollout_state=?, reviewed_at=?, reviewed_by=? WHERE id=?",
                (status, rollout_state, _now(), reviewed_by, proposal_pk),
            )
        return cur.rowcount > 0
