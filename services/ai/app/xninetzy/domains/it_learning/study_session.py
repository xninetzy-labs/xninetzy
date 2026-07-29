from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.concept_graph import (
    link_session_concept,
    next_ready_concept,
    record_evidence_in_transaction,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _bounded_int(value: int, minimum: int, maximum: int, name: str) -> int:
    if value < minimum or value > maximum:
        raise ValueError(f"{name} harus antara {minimum} dan {maximum}.")
    return value


def _bounded_mastery(value: float, name: str) -> float:
    if value < 0 or value > 1:
        raise ValueError(f"{name} harus antara 0 dan 1.")
    return value


def _get_session(session_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM learning_study_sessions WHERE id=?", (session_id,)
        ).fetchone()
    return dict(row) if row else None


def start_study_session(
    roadmap_id: int | None = None,
    objective: str = "",
    planned_minutes: int = 25,
    energy_before: int = 3,
    mastery_before: float = 0,
    learning_task_id: int | None = None,
    idempotency_key: str | None = None,
    chat_id: str = "system",
) -> tuple[dict, bool]:
    init_db()
    _bounded_int(planned_minutes, 5, 240, "planned_minutes")
    _bounded_int(energy_before, 1, 5, "energy_before")
    _bounded_mastery(mastery_before, "mastery_before")
    now = _now()
    with connect() as conn:
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM learning_study_sessions WHERE session_key=?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                return dict(existing), False
        active = conn.execute(
            "SELECT * FROM learning_study_sessions WHERE status='active' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if active:
            return dict(active), False
        if roadmap_id is None:
            roadmap = conn.execute(
                "SELECT * FROM learning_roadmaps WHERE status='active' ORDER BY updated_at DESC, id DESC LIMIT 1"
            ).fetchone()
        else:
            roadmap = conn.execute(
                "SELECT * FROM learning_roadmaps WHERE id=? AND status='active'",
                (roadmap_id,),
            ).fetchone()
        if not roadmap:
            raise LookupError("Roadmap aktif tidak ditemukan.")
        if learning_task_id is not None:
            selected_task = conn.execute(
                "SELECT * FROM learning_tasks WHERE id=? AND roadmap_id=?",
                (learning_task_id, roadmap["id"]),
            ).fetchone()
            if not selected_task:
                raise LookupError(
                    "Learning task tidak ditemukan pada roadmap tersebut."
                )
        else:
            selected_task = conn.execute(
                "SELECT * FROM learning_tasks WHERE roadmap_id=? AND status!='done' ORDER BY day_index, id LIMIT 1",
                (roadmap["id"],),
            ).fetchone()
        concept = next_ready_concept(
            conn,
            int(roadmap["id"]),
            int(selected_task["id"]) if selected_task else None,
        )
        if concept is None:
            concept = next_ready_concept(conn, int(roadmap["id"]))
        resolved_objective = objective.strip()
        if not resolved_objective and selected_task:
            resolved_objective = selected_task["title"]
            if concept:
                resolved_objective = f"{resolved_objective} — {concept['title']}"
        if not resolved_objective:
            resolved_objective = f"Belajar {roadmap['topic']}"
        session_key = idempotency_key or f"study:{roadmap['id']}:{uuid4().hex}"
        try:
            result = conn.execute(
                """
                INSERT INTO learning_study_sessions
                  (session_key, roadmap_id, learning_task_id, chat_id, topic, objective,
                   planned_minutes, energy_before, mastery_before, status, started_at,
                   created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,'active',?,?,?)
                """,
                (
                    session_key,
                    roadmap["id"],
                    selected_task["id"] if selected_task else None,
                    chat_id,
                    roadmap["topic"],
                    resolved_objective,
                    planned_minutes,
                    energy_before,
                    mastery_before,
                    now,
                    now,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            existing = conn.execute(
                "SELECT * FROM learning_study_sessions WHERE session_key=? OR status='active' ORDER BY id DESC LIMIT 1",
                (session_key,),
            ).fetchone()
            if existing:
                return dict(existing), False
            raise
        session_id = int(result.lastrowid)
        if concept:
            link_session_concept(conn, session_id, int(concept["id"]), now)
    session = _get_session(session_id)
    if not session:
        raise RuntimeError("Sesi belajar gagal disimpan.")
    return session, True


def complete_study_session(
    session_id: int,
    actual_minutes: int,
    mastery_after: float,
    reflection: str = "",
    energy_after: int | None = None,
    evidence: list[str] | None = None,
) -> tuple[dict, bool]:
    init_db()
    _bounded_int(actual_minutes, 1, 480, "actual_minutes")
    _bounded_mastery(mastery_after, "mastery_after")
    if energy_after is not None:
        _bounded_int(energy_after, 1, 5, "energy_after")
    now = _now()
    event_id = None
    with connect() as conn:
        session = conn.execute(
            "SELECT * FROM learning_study_sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not session:
            raise LookupError(f"Sesi belajar #{session_id} tidak ditemukan.")
        if session["status"] == "completed":
            return dict(session), False
        if session["status"] != "active":
            raise ValueError(f"Sesi belajar #{session_id} tidak aktif.")
        event_payload = {
            "roadmap_id": session["roadmap_id"],
            "learning_task_id": session["learning_task_id"],
            "objective": session["objective"],
            "actual_minutes": actual_minutes,
            "mastery_after": mastery_after,
            "energy_after": energy_after,
        }
        concept_rows = conn.execute(
            "SELECT concept_id FROM learning_session_concepts WHERE session_id=? ORDER BY concept_id",
            (session_id,),
        ).fetchall()
        concept_ids = [int(row["concept_id"]) for row in concept_rows]
        event_payload["concept_ids"] = concept_ids
        event = conn.execute(
            """
            INSERT INTO ecosystem_events
              (chat_id, event_type, source, entity_type, entity_id, payload_json, created_at)
            VALUES (?, 'learning_session_completed', 'learning', 'study_session', ?, ?, ?)
            """,
            (
                session["chat_id"] or "system",
                str(session_id),
                json.dumps(event_payload, ensure_ascii=False),
                now,
            ),
        )
        event_id = int(event.lastrowid)
        conn.execute(
            """
            UPDATE learning_study_sessions
            SET actual_minutes=?, energy_after=?, mastery_after=?, reflection=?,
                evidence_json=?, completion_event_id=?, status='completed',
                completed_at=?, updated_at=?
            WHERE id=? AND status='active'
            """,
            (
                actual_minutes,
                energy_after,
                mastery_after,
                reflection.strip(),
                json.dumps(evidence or [], ensure_ascii=False),
                event_id,
                now,
                now,
                session_id,
            ),
        )
        conn.execute(
            "INSERT INTO learning_progress (roadmap_id, note, created_at) VALUES (?,?,?)",
            (
                session["roadmap_id"],
                f"Sesi #{session_id}: {session['objective']} | {actual_minutes} menit | mastery {mastery_after:.0%}",
                now,
            ),
        )
        conn.execute(
            "UPDATE learning_roadmaps SET updated_at=? WHERE id=?",
            (now, session["roadmap_id"]),
        )
        for concept_id in concept_ids:
            record_evidence_in_transaction(
                conn,
                concept_id,
                "study_session",
                f"xninetzy://learning/session/{session_id}",
                reflection.strip(),
                mastery_after,
                f"study-session:{session_id}:concept:{concept_id}",
                now,
            )
    if event_id is not None:
        try:
            from app.xninetzy.ecosystem.reducers import consume_event

            consume_event(event_id)
        except Exception:
            logger.exception(
                "Study-session event reducer failed for event %s", event_id
            )
    completed = _get_session(session_id)
    if not completed:
        raise RuntimeError("Sesi belajar gagal diperbarui.")
    return completed, True


def list_study_sessions(roadmap_id: int | None = None, limit: int = 10) -> list[dict]:
    bounded_limit = max(1, min(limit, 50))
    with connect() as conn:
        if roadmap_id is None:
            rows = conn.execute(
                "SELECT * FROM learning_study_sessions ORDER BY id DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM learning_study_sessions WHERE roadmap_id=? ORDER BY id DESC LIMIT ?",
                (roadmap_id, bounded_limit),
            ).fetchall()
    return [dict(row) for row in rows]


@tool
def learning_start_study_session(
    roadmap_id: int | None = None,
    objective: str = "",
    planned_minutes: int = 25,
    energy_before: int = 3,
    mastery_before: float = 0,
    learning_task_id: int | None = None,
    idempotency_key: str | None = None,
    chat_id: str = "system",
) -> str:
    """Mulai satu sesi belajar aktif yang terhubung ke roadmap dan learning task."""
    try:
        session, created = start_study_session(
            roadmap_id=roadmap_id,
            objective=objective,
            planned_minutes=planned_minutes,
            energy_before=energy_before,
            mastery_before=mastery_before,
            learning_task_id=learning_task_id,
            idempotency_key=idempotency_key,
            chat_id=chat_id,
        )
    except (LookupError, ValueError) as exc:
        return f"Tidak dapat memulai sesi: {exc}"
    prefix = "Sesi belajar dimulai" if created else "Sesi aktif digunakan kembali"
    return (
        f"*{prefix}*\nID: `{session['id']}`\nRoadmap: #{session['roadmap_id']}\n"
        f"Fokus: {session['objective']}\nTarget: {session['planned_minutes']} menit\n"
        f"Energi awal: {session['energy_before']}/5"
    )


@tool
def learning_complete_study_session(
    session_id: int,
    actual_minutes: int,
    mastery_after: float,
    reflection: str = "",
    energy_after: int | None = None,
    evidence: list[str] | None = None,
) -> str:
    """Selesaikan sesi belajar dan simpan durasi, mastery, energi, refleksi, serta evidence."""
    try:
        session, changed = complete_study_session(
            session_id=session_id,
            actual_minutes=actual_minutes,
            mastery_after=mastery_after,
            reflection=reflection,
            energy_after=energy_after,
            evidence=evidence,
        )
    except (LookupError, ValueError) as exc:
        return f"Tidak dapat menyelesaikan sesi: {exc}"
    prefix = "Sesi selesai" if changed else "Sesi sudah selesai sebelumnya"
    return (
        f"*{prefix}*\nID: `{session['id']}`\nFokus: {session['objective']}\n"
        f"Durasi: {session['actual_minutes']} menit\nMastery: {session['mastery_after']:.0%}"
    )


@tool
def learning_list_study_sessions(roadmap_id: int | None = None, limit: int = 10) -> str:
    """Tampilkan riwayat sesi belajar terbaru untuk owner lokal."""
    sessions = list_study_sessions(roadmap_id, limit)
    if not sessions:
        return "Belum ada sesi belajar."
    lines = ["*Riwayat Sesi Belajar*"]
    for session in sessions:
        duration = session["actual_minutes"] or session["planned_minutes"]
        mastery = session["mastery_after"]
        mastery_text = f" | mastery {mastery:.0%}" if mastery is not None else ""
        lines.append(
            f"`{session['id']}` [{session['status']}] {session['objective']} | {duration} menit{mastery_text}"
        )
    return "\n".join(lines)
