from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.sqlite import connect


class ResearchSubStep(BaseModel):
    id: str
    type: str
    title: str
    detail: str | None = None
    status: str = "pending"
    payload: dict = Field(default_factory=dict)
    created_at: str


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _loads(value: str | None, default):
    try:
        return json.loads(value or "")
    except Exception:
        return default


def create_research_session(
    chat_id: str,
    topic: str,
    requester_id: str | None = None,
    requester_name: str | None = None,
    mode: str = "balanced",
    plan: list[dict] | None = None,
) -> int:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO research_sessions
              (chat_id, requester_id, requester_name, topic, mode, status,
               plan_json, substeps_json, sources_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (chat_id, requester_id, requester_name, topic, mode, "planned",
             json.dumps(plan or [], ensure_ascii=False), "[]", "[]", now, now),
        )
        return int(cur.lastrowid)


def get_research_session(session_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM research_sessions WHERE id=?", (session_id,)).fetchone()
    return dict(row) if row else None


def add_substep(
    session_id: int,
    type: str,
    title: str,
    detail: str | None = None,
    payload: dict | None = None,
) -> str:
    row = get_research_session(session_id)
    substeps = _loads(row.get("substeps_json") if row else None, [])
    substep_id = f"{type}-{len(substeps) + 1}"
    substep = ResearchSubStep(
        id=substep_id,
        type=type,
        title=title,
        detail=detail,
        status="running",
        payload=payload or {},
        created_at=_now(),
    )
    substeps.append(substep.model_dump())
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET substeps_json=?, status=?, updated_at=? WHERE id=?",
            (json.dumps(substeps, ensure_ascii=False), type, _now(), session_id),
        )
    return substep_id


def update_substep_status(
    session_id: int,
    substep_id: str,
    status: str,
    payload: dict | None = None,
) -> None:
    row = get_research_session(session_id)
    substeps = _loads(row.get("substeps_json") if row else None, [])
    for substep in substeps:
        if substep.get("id") == substep_id:
            substep["status"] = status
            if payload:
                substep["payload"] = {**(substep.get("payload") or {}), **payload}
            break
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET substeps_json=?, updated_at=? WHERE id=?",
            (json.dumps(substeps, ensure_ascii=False), _now(), session_id),
        )


def add_sources(session_id: int, sources: list[dict]) -> None:
    row = get_research_session(session_id)
    existing = _loads(row.get("sources_json") if row else None, [])
    existing.extend(sources)
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET sources_json=?, updated_at=? WHERE id=?",
            (json.dumps(existing, ensure_ascii=False), _now(), session_id),
        )


def set_plan(session_id: int, plan: list[dict]) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET plan_json=?, updated_at=? WHERE id=?",
            (json.dumps(plan, ensure_ascii=False), _now(), session_id),
        )


def finish_session(session_id: int, brief: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET status='done', brief=?, updated_at=? WHERE id=?",
            (brief, _now(), session_id),
        )


def fail_session(session_id: int, error: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE research_sessions SET status='failed', brief=?, updated_at=? WHERE id=?",
            (error[:4000], _now(), session_id),
        )
