from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from sqlite3 import Connection
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.ecosystem.event_bus import (
    dispatch_recorded_event,
    record_event_in_transaction,
)


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _clean(value: str, name: str, maximum: int) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    if not cleaned:
        raise ValueError(f"{name} tidak boleh kosong.")
    if len(cleaned) > maximum:
        raise ValueError(f"{name} maksimal {maximum} karakter.")
    return cleaned


def _slug(title: str) -> str:
    normalized = re.sub(r"[^\w]+", "-", title.casefold(), flags=re.UNICODE).strip("-")
    if normalized:
        return normalized[:100]
    return hashlib.sha256(title.encode()).hexdigest()[:16]


def _bounded_score(value: float) -> float:
    score = float(value)
    if score < 0 or score > 1:
        raise ValueError("mastery_score harus antara 0 dan 1.")
    return score


def _require_roadmap(conn: Connection, roadmap_id: int) -> None:
    if not conn.execute(
        "SELECT id FROM learning_roadmaps WHERE id=?", (roadmap_id,)
    ).fetchone():
        raise LookupError(f"Roadmap #{roadmap_id} tidak ditemukan.")


def _validate_related_ids(
    conn: Connection,
    table: str,
    ids: list[int],
    roadmap_id: int,
    label: str,
) -> None:
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT id FROM {table} WHERE roadmap_id=? AND id IN ({placeholders})",
        (roadmap_id, *ids),
    ).fetchall()
    found = {int(row["id"]) for row in rows}
    missing = sorted(set(ids) - found)
    if missing:
        raise ValueError(f"{label} bukan bagian roadmap #{roadmap_id}: {missing}")


def _would_create_cycle(conn: Connection, concept_id: int, prerequisite_id: int) -> bool:
    row = conn.execute(
        """
        WITH RECURSIVE ancestors(id) AS (
            SELECT prerequisite_id
            FROM learning_concept_prerequisites
            WHERE concept_id=?
            UNION
            SELECT relation.prerequisite_id
            FROM learning_concept_prerequisites relation
            JOIN ancestors ON relation.concept_id=ancestors.id
        )
        SELECT 1 FROM ancestors WHERE id=? LIMIT 1
        """,
        (prerequisite_id, concept_id),
    ).fetchone()
    return row is not None


def define_concept(
    roadmap_id: int,
    title: str,
    description: str = "",
    prerequisite_ids: list[int] | None = None,
    milestone_ids: list[int] | None = None,
    learning_task_ids: list[int] | None = None,
) -> tuple[dict, bool]:
    init_db()
    clean_title = _clean(title, "title", 200)
    clean_description = re.sub(r"\s+", " ", description or "").strip()[:1000]
    prerequisites = sorted(set(prerequisite_ids or []))
    milestones = sorted(set(milestone_ids or []))
    tasks = sorted(set(learning_task_ids or []))
    now = _now()
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _require_roadmap(conn, roadmap_id)
        existing = conn.execute(
            "SELECT * FROM learning_concepts WHERE roadmap_id=? AND slug=?",
            (roadmap_id, _slug(clean_title)),
        ).fetchone()
        if existing:
            concept_id = int(existing["id"])
            created = False
            if existing["title"] != clean_title or existing["description"] != clean_description:
                conn.execute(
                    "UPDATE learning_concepts SET title=?, description=?, updated_at=? WHERE id=?",
                    (clean_title, clean_description, now, concept_id),
                )
        else:
            result = conn.execute(
                """
                INSERT INTO learning_concepts
                  (roadmap_id, slug, title, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (roadmap_id, _slug(clean_title), clean_title, clean_description, now, now),
            )
            concept_id = int(result.lastrowid)
            created = True
        _validate_related_ids(
            conn, "learning_concepts", prerequisites, roadmap_id, "Prerequisite"
        )
        _validate_related_ids(
            conn, "learning_milestones", milestones, roadmap_id, "Milestone"
        )
        _validate_related_ids(conn, "learning_tasks", tasks, roadmap_id, "Task")
        for prerequisite_id in prerequisites:
            if prerequisite_id == concept_id or _would_create_cycle(
                conn, concept_id, prerequisite_id
            ):
                raise ValueError("Relasi prerequisite membentuk cycle.")
            conn.execute(
                "INSERT OR IGNORE INTO learning_concept_prerequisites (concept_id, prerequisite_id, created_at) VALUES (?,?,?)",
                (concept_id, prerequisite_id, now),
            )
        for milestone_id in milestones:
            conn.execute(
                "INSERT OR IGNORE INTO learning_concept_milestones (concept_id, milestone_id, created_at) VALUES (?,?,?)",
                (concept_id, milestone_id, now),
            )
        for learning_task_id in tasks:
            conn.execute(
                "INSERT OR IGNORE INTO learning_concept_tasks (concept_id, learning_task_id, created_at) VALUES (?,?,?)",
                (concept_id, learning_task_id, now),
            )
        row = conn.execute(
            "SELECT * FROM learning_concepts WHERE id=?", (concept_id,)
        ).fetchone()
    if not row:
        raise RuntimeError("Konsep gagal disimpan.")
    return dict(row), created


def seed_roadmap_concepts(
    conn: Connection,
    roadmap_id: int,
    milestones: list[tuple[int, str]],
    tasks: list[tuple[int, str]],
    now: str,
) -> None:
    concept_ids: list[int] = []
    for position, (milestone_id, title) in enumerate(milestones, start=1):
        slug = f"{position}-{_slug(title)}"
        result = conn.execute(
            """
            INSERT OR IGNORE INTO learning_concepts
              (roadmap_id, slug, title, description, created_at, updated_at)
            VALUES (?,?,?,?,?,?)
            """,
            (roadmap_id, slug, title, f"Milestone {position}", now, now),
        )
        concept_id = int(result.lastrowid)
        if not concept_id:
            row = conn.execute(
                "SELECT id FROM learning_concepts WHERE roadmap_id=? AND slug=?",
                (roadmap_id, slug),
            ).fetchone()
            concept_id = int(row["id"])
        concept_ids.append(concept_id)
        conn.execute(
            "INSERT OR IGNORE INTO learning_concept_milestones (concept_id, milestone_id, created_at) VALUES (?,?,?)",
            (concept_id, milestone_id, now),
        )
        if len(concept_ids) > 1:
            conn.execute(
                "INSERT OR IGNORE INTO learning_concept_prerequisites (concept_id, prerequisite_id, created_at) VALUES (?,?,?)",
                (concept_id, concept_ids[-2], now),
            )
    if not concept_ids:
        return
    for position, (task_id, _) in enumerate(tasks):
        concept_index = min(
            (position * len(concept_ids)) // max(len(tasks), 1),
            len(concept_ids) - 1,
        )
        conn.execute(
            "INSERT OR IGNORE INTO learning_concept_tasks (concept_id, learning_task_id, created_at) VALUES (?,?,?)",
            (concept_ids[concept_index], task_id, now),
        )


def next_ready_concept(
    conn: Connection, roadmap_id: int, learning_task_id: int | None = None
) -> dict | None:
    task_clause = ""
    params: list[object] = [roadmap_id]
    if learning_task_id is not None:
        task_clause = (
            "AND EXISTS (SELECT 1 FROM learning_concept_tasks task_link "
            "WHERE task_link.concept_id=concept.id AND task_link.learning_task_id=?)"
        )
        params.append(learning_task_id)
    row = conn.execute(
        f"""
        SELECT concept.*
        FROM learning_concepts concept
        WHERE concept.roadmap_id=? AND concept.mastery < 0.8
          {task_clause}
          AND NOT EXISTS (
              SELECT 1
              FROM learning_concept_prerequisites relation
              JOIN learning_concepts prerequisite ON prerequisite.id=relation.prerequisite_id
              WHERE relation.concept_id=concept.id AND prerequisite.mastery < 0.7
          )
        ORDER BY concept.mastery ASC, concept.id ASC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return dict(row) if row else None


def concept_for_task(
    conn: Connection, roadmap_id: int, learning_task_id: int
) -> dict | None:
    row = conn.execute(
        """
        SELECT concept.*
        FROM learning_concepts concept
        JOIN learning_concept_tasks task_link ON task_link.concept_id=concept.id
        WHERE concept.roadmap_id=? AND task_link.learning_task_id=?
        ORDER BY concept.mastery ASC, concept.id ASC
        LIMIT 1
        """,
        (roadmap_id, learning_task_id),
    ).fetchone()
    return dict(row) if row else None


def link_session_concept(
    conn: Connection, session_id: int, concept_id: int, now: str
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO learning_session_concepts (session_id, concept_id, created_at) VALUES (?,?,?)",
        (session_id, concept_id, now),
    )


def record_evidence_in_transaction(
    conn: Connection,
    concept_id: int,
    evidence_type: str,
    reference: str,
    note: str,
    mastery_score: float,
    idempotency_key: str,
    now: str,
) -> tuple[dict, bool]:
    concept = conn.execute(
        "SELECT * FROM learning_concepts WHERE id=?", (concept_id,)
    ).fetchone()
    if not concept:
        raise LookupError(f"Konsep #{concept_id} tidak ditemukan.")
    clean_type = _clean(evidence_type, "evidence_type", 50).casefold()
    clean_reference = _clean(reference, "reference", 500)
    clean_note = re.sub(r"\s+", " ", note or "").strip()[:1000]
    clean_key = _clean(idempotency_key, "idempotency_key", 200)
    score = _bounded_score(mastery_score)
    evidence_key = hashlib.sha256(f"learning-evidence:{clean_key}".encode()).hexdigest()
    payload_hash = hashlib.sha256(
        json.dumps(
            {
                "concept_id": concept_id,
                "evidence_type": clean_type,
                "reference": clean_reference,
                "note": clean_note,
                "mastery_score": score,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    existing = conn.execute(
        "SELECT * FROM learning_concept_evidence WHERE evidence_key=?",
        (evidence_key,),
    ).fetchone()
    if existing:
        if existing["payload_hash"] != payload_hash:
            raise ValueError("Idempotency key sudah dipakai untuk evidence berbeda.")
        return dict(existing), False
    result = conn.execute(
        """
        INSERT INTO learning_concept_evidence
          (evidence_key, payload_hash, roadmap_id, concept_id, evidence_type,
           reference, note, mastery_score, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            evidence_key,
            payload_hash,
            concept["roadmap_id"],
            concept_id,
            clean_type,
            clean_reference,
            clean_note,
            score,
            now,
        ),
    )
    count = int(concept["evidence_count"] or 0)
    mastery = score if count == 0 else (float(concept["mastery"]) * 0.4) + (score * 0.6)
    status = "mastered" if mastery >= 0.8 else "practicing"
    conn.execute(
        """
        UPDATE learning_concepts
        SET mastery=?, evidence_count=evidence_count+1, status=?, updated_at=?
        WHERE id=?
        """,
        (round(mastery, 4), status, now, concept_id),
    )
    row = conn.execute(
        "SELECT * FROM learning_concept_evidence WHERE id=?", (result.lastrowid,)
    ).fetchone()
    return dict(row), True


def record_concept_evidence(
    concept_id: int,
    evidence_type: str,
    reference: str,
    mastery_score: float,
    idempotency_key: str,
    note: str = "",
    chat_id: str = "system",
) -> tuple[dict, bool, dict]:
    init_db()
    now = _now()
    event_id: int | None = None
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        evidence, created = record_evidence_in_transaction(
            conn,
            concept_id,
            evidence_type,
            reference,
            note,
            mastery_score,
            idempotency_key,
            now,
        )
        concept = conn.execute(
            "SELECT * FROM learning_concepts WHERE id=?", (concept_id,)
        ).fetchone()
        if created and concept:
            event_id = record_event_in_transaction(
                conn,
                chat_id,
                "learning_concept_evidence_recorded",
                "learning",
                "learning_concept",
                str(concept_id),
                {
                    "roadmap_id": concept["roadmap_id"],
                    "mastery": concept["mastery"],
                    "evidence_count": concept["evidence_count"],
                },
                now,
            )
    if event_id is not None:
        dispatch_recorded_event(event_id)
    if not concept:
        raise RuntimeError("Konsep gagal diperbarui.")
    return evidence, created, dict(concept)


def concept_map(roadmap_id: int) -> list[dict]:
    init_db()
    with connect() as conn:
        _require_roadmap(conn, roadmap_id)
        rows = conn.execute(
            """
            SELECT concept.*,
                   GROUP_CONCAT(DISTINCT prerequisite.prerequisite_id) AS prerequisite_ids,
                   COUNT(DISTINCT milestone.milestone_id) AS milestone_count,
                   COUNT(DISTINCT task.learning_task_id) AS task_count
            FROM learning_concepts concept
            LEFT JOIN learning_concept_prerequisites prerequisite
              ON prerequisite.concept_id=concept.id
            LEFT JOIN learning_concept_milestones milestone
              ON milestone.concept_id=concept.id
            LEFT JOIN learning_concept_tasks task
              ON task.concept_id=concept.id
            WHERE concept.roadmap_id=?
            GROUP BY concept.id
            ORDER BY concept.id
            """,
            (roadmap_id,),
        ).fetchall()
    concepts = []
    for row in rows:
        item = dict(row)
        raw_ids = item.pop("prerequisite_ids") or ""
        item["prerequisite_ids"] = [
            int(value) for value in raw_ids.split(",") if value
        ]
        concepts.append(item)
    return concepts


def mastery_focus(roadmap_id: int | None = None, limit: int = 3) -> list[dict]:
    init_db()
    bounded = min(max(int(limit), 1), 10)
    conditions = [] if roadmap_id is not None else ["roadmap.status='active'"]
    params: list[object] = []
    if roadmap_id is not None:
        conditions.append("concept.roadmap_id=?")
        params.append(roadmap_id)
    params.append(bounded)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT concept.id, concept.title, concept.mastery,
                   concept.evidence_count, concept.status,
                   roadmap.id AS roadmap_id, roadmap.title AS roadmap_title
            FROM learning_concepts concept
            JOIN learning_roadmaps roadmap ON roadmap.id=concept.roadmap_id
            WHERE {' AND '.join(conditions) if conditions else '1=1'}
            ORDER BY concept.mastery ASC, concept.evidence_count ASC, concept.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


@tool
def learning_define_concept(
    roadmap_id: int,
    title: str,
    description: str = "",
    prerequisite_ids: list[int] | None = None,
    milestone_ids: list[int] | None = None,
    learning_task_ids: list[int] | None = None,
) -> str:
    """Definisikan konsep roadmap beserta prerequisite, milestone, dan task terkait."""
    try:
        concept, created = define_concept(
            roadmap_id,
            title,
            description,
            prerequisite_ids,
            milestone_ids,
            learning_task_ids,
        )
    except (LookupError, ValueError) as exc:
        return f"Konsep tidak dapat disimpan: {exc}"
    action = "dibuat" if created else "digunakan kembali"
    return f"Konsep #{concept['id']} {concept['title']} {action} pada roadmap #{roadmap_id}."


@tool
def learning_record_concept_evidence(
    concept_id: int,
    evidence_type: str,
    reference: str,
    mastery_score: float,
    idempotency_key: str,
    note: str = "",
    chat_id: str = "system",
) -> str:
    """Catat evidence idempotent dan perbarui mastery konsep secara deterministik."""
    try:
        _, created, concept = record_concept_evidence(
            concept_id,
            evidence_type,
            reference,
            mastery_score,
            idempotency_key,
            note,
            chat_id,
        )
    except (LookupError, ValueError) as exc:
        return f"Evidence tidak dapat disimpan: {exc}"
    state = "dicatat" if created else "sudah tercatat"
    return (
        f"Evidence konsep #{concept_id} {state}. Mastery: "
        f"{float(concept['mastery']):.0%} dari {concept['evidence_count']} evidence."
    )


@tool
def learning_get_concept_map(roadmap_id: int) -> str:
    """Tampilkan concept graph, prerequisite, evidence, dan mastery roadmap."""
    try:
        concepts = concept_map(roadmap_id)
    except LookupError as exc:
        return str(exc)
    if not concepts:
        return f"Roadmap #{roadmap_id} belum memiliki konsep."
    lines = [f"*Concept Map Roadmap #{roadmap_id}*"]
    for concept in concepts:
        prerequisites = concept["prerequisite_ids"]
        prerequisite_text = ", ".join(f"#{value}" for value in prerequisites) or "-"
        lines.append(
            f"• #{concept['id']} {concept['title']} — {float(concept['mastery']):.0%} "
            f"[{concept['status']}] | prereq: {prerequisite_text} | "
            f"evidence: {concept['evidence_count']}"
        )
    return "\n".join(lines)
