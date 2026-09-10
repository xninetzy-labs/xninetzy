from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.concept_graph import (
    record_evidence_in_transaction,
)
from app.xninetzy.ecosystem.event_bus import (
    dispatch_recorded_event,
    record_event_in_transaction,
)

STOPWORDS = {
    "adalah",
    "agar",
    "akan",
    "atau",
    "dalam",
    "dari",
    "dengan",
    "dan",
    "yang",
    "untuk",
    "pada",
    "the",
    "and",
    "for",
    "from",
    "that",
    "this",
    "with",
}


def _now(value: datetime | None = None) -> datetime:
    timezone = ZoneInfo(get_settings().APP_TIMEZONE)
    current = value or datetime.now(timezone)
    return current.replace(tzinfo=timezone) if current.tzinfo is None else current.astimezone(timezone)


def _clean(value: str, name: str, maximum: int) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    if not cleaned:
        raise ValueError(f"{name} tidak boleh kosong.")
    if len(cleaned) > maximum:
        raise ValueError(f"{name} maksimal {maximum} karakter.")
    return cleaned


def _normalize(value: str) -> str:
    return re.sub(r"[^\w]+", " ", value.casefold(), flags=re.UNICODE).strip()


def _keywords(expected_answer: str, keywords: list[str] | None) -> list[str]:
    values = keywords or []
    if not values:
        values = [
            token
            for token in _normalize(expected_answer).split()
            if len(token) >= 3 and token not in STOPWORDS
        ]
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _clean(value, "keyword", 80)
        key = _normalize(clean)
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(key)
        if len(normalized) == 12:
            break
    if not normalized:
        raise ValueError("Recall card membutuhkan minimal satu keyword jawaban.")
    return normalized


def _payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def _stable_key(namespace: str, value: str) -> str:
    return hashlib.sha256(f"{namespace}:{value}".encode()).hexdigest()


def create_recall_card(
    concept_id: int,
    question: str,
    expected_answer: str,
    answer_keywords: list[str] | None = None,
    source_reference: str = "",
    idempotency_key: str = "",
    now: datetime | None = None,
) -> tuple[dict, bool]:
    init_db()
    clean_question = _clean(question, "question", 1000)
    clean_answer = _clean(expected_answer, "expected_answer", 2000)
    clean_source = re.sub(r"\s+", " ", source_reference or "").strip()[:500]
    keywords = _keywords(clean_answer, answer_keywords)
    current = _now(now)
    raw_key = idempotency_key.strip() or f"{concept_id}:{_normalize(clean_question)}"
    card_key = _stable_key("learning-recall-card", raw_key)
    payload = {
        "concept_id": concept_id,
        "question": clean_question,
        "expected_answer": clean_answer,
        "answer_keywords": keywords,
        "source_reference": clean_source,
    }
    payload_hash = _payload_hash(payload)
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        concept = conn.execute(
            "SELECT * FROM learning_concepts WHERE id=?", (concept_id,)
        ).fetchone()
        if not concept:
            raise LookupError(f"Konsep #{concept_id} tidak ditemukan.")
        existing = conn.execute(
            "SELECT * FROM learning_recall_cards WHERE card_key=?", (card_key,)
        ).fetchone()
        if existing:
            if existing["payload_hash"] != payload_hash:
                raise ValueError("Idempotency key sudah dipakai untuk recall card berbeda.")
            return dict(existing), False
        result = conn.execute(
            """
            INSERT INTO learning_recall_cards
              (card_key, payload_hash, roadmap_id, concept_id, question,
               expected_answer, keywords_json, source_reference, due_at,
               created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                card_key,
                payload_hash,
                concept["roadmap_id"],
                concept_id,
                clean_question,
                clean_answer,
                json.dumps(keywords, ensure_ascii=False),
                clean_source,
                current.isoformat(),
                current.isoformat(),
                current.isoformat(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM learning_recall_cards WHERE id=?", (result.lastrowid,)
        ).fetchone()
    if not row:
        raise RuntimeError("Recall card gagal disimpan.")
    return dict(row), True


def due_recall_cards(
    roadmap_id: int | None = None,
    limit: int = 5,
    now: datetime | None = None,
) -> list[dict]:
    init_db()
    bounded = min(max(int(limit), 1), 20)
    current = _now(now).isoformat()
    conditions = ["card.status='active'", "card.due_at<=?"]
    params: list[object] = [current]
    if roadmap_id is not None:
        conditions.append("card.roadmap_id=?")
        params.append(roadmap_id)
    params.append(bounded)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT card.*, concept.title AS concept_title,
                   roadmap.title AS roadmap_title
            FROM learning_recall_cards card
            JOIN learning_concepts concept ON concept.id=card.concept_id
            JOIN learning_roadmaps roadmap ON roadmap.id=card.roadmap_id
            WHERE {' AND '.join(conditions)}
            ORDER BY card.due_at ASC, card.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def keyword_coverage(answer: str, keywords: list[str]) -> float:
    normalized_answer = f" {_normalize(answer)} "
    matches = sum(1 for keyword in keywords if f" {keyword} " in normalized_answer)
    return matches / len(keywords) if keywords else 0


def recall_quality(coverage: float) -> int:
    if coverage >= 0.9:
        return 5
    if coverage >= 0.7:
        return 4
    if coverage >= 0.5:
        return 3
    if coverage >= 0.25:
        return 2
    if coverage > 0:
        return 1
    return 0


def _next_schedule(card: dict, quality: int, current: datetime) -> dict:
    ease = float(card["ease_factor"])
    repetitions = int(card["repetitions"])
    previous_interval = int(card["interval_days"])
    lapses = int(card["lapse_count"])
    ease = max(
        1.3,
        ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    if quality < 3:
        repetitions = 0
        interval = 1
        lapses += 1
    else:
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = max(1, round(previous_interval * ease))
    return {
        "ease_factor": round(ease, 4),
        "repetitions": repetitions,
        "interval_days": interval,
        "lapse_count": lapses,
        "due_at": (current + timedelta(days=interval)).isoformat(),
    }


def submit_recall_answer(
    card_id: int,
    answer: str,
    confidence: int,
    idempotency_key: str = "",
    chat_id: str = "system",
    now: datetime | None = None,
) -> tuple[dict, bool, dict, dict]:
    init_db()
    clean_answer = _clean(answer, "answer", 4000)
    confidence_value = int(confidence)
    if confidence_value < 1 or confidence_value > 5:
        raise ValueError("confidence harus antara 1 dan 5.")
    current = _now(now)
    event_id: int | None = None
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        card_row = conn.execute(
            "SELECT * FROM learning_recall_cards WHERE id=?", (card_id,)
        ).fetchone()
        if not card_row:
            raise LookupError(f"Recall card #{card_id} tidak ditemukan.")
        if card_row["status"] != "active":
            raise ValueError(f"Recall card #{card_id} tidak aktif.")
        card = dict(card_row)
        raw_key = idempotency_key.strip() or (
            f"{card_id}:{current.date().isoformat()}:{confidence_value}:"
            f"{_normalize(clean_answer)}"
        )
        attempt_key = _stable_key("learning-recall-attempt", raw_key)
        attempt_payload_hash = _payload_hash(
            {
                "card_id": card_id,
                "answer": clean_answer,
                "confidence": confidence_value,
            }
        )
        existing = conn.execute(
            "SELECT * FROM learning_recall_attempts WHERE attempt_key=?",
            (attempt_key,),
        ).fetchone()
        if existing:
            if existing["payload_hash"] != attempt_payload_hash:
                raise ValueError("Idempotency key sudah dipakai untuk jawaban berbeda.")
            concept = conn.execute(
                "SELECT * FROM learning_concepts WHERE id=?", (card["concept_id"],)
            ).fetchone()
            return dict(existing), False, card, dict(concept)
        keywords = json.loads(card["keywords_json"] or "[]")
        coverage = keyword_coverage(clean_answer, keywords)
        quality = recall_quality(coverage)
        schedule = _next_schedule(card, quality, current)
        result = conn.execute(
            """
            INSERT INTO learning_recall_attempts
              (attempt_key, payload_hash, card_id, answer, confidence,
               keyword_coverage, quality, previous_interval_days,
               next_interval_days, next_due_at, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                attempt_key,
                attempt_payload_hash,
                card_id,
                clean_answer,
                confidence_value,
                round(coverage, 4),
                quality,
                card["interval_days"],
                schedule["interval_days"],
                schedule["due_at"],
                current.isoformat(),
            ),
        )
        attempt_id = int(result.lastrowid)
        conn.execute(
            """
            UPDATE learning_recall_cards
            SET ease_factor=?, interval_days=?, repetitions=?, lapse_count=?,
                due_at=?, last_reviewed_at=?, updated_at=?
            WHERE id=?
            """,
            (
                schedule["ease_factor"],
                schedule["interval_days"],
                schedule["repetitions"],
                schedule["lapse_count"],
                schedule["due_at"],
                current.isoformat(),
                current.isoformat(),
                card_id,
            ),
        )
        record_evidence_in_transaction(
            conn,
            int(card["concept_id"]),
            "active_recall",
            f"xninetzy://learning/recall-attempt/{attempt_id}",
            f"Keyword coverage {coverage:.0%}; confidence {confidence_value}/5",
            coverage,
            f"recall-attempt:{attempt_key}",
            current.isoformat(),
        )
        updated_card = conn.execute(
            "SELECT * FROM learning_recall_cards WHERE id=?", (card_id,)
        ).fetchone()
        concept = conn.execute(
            "SELECT * FROM learning_concepts WHERE id=?", (card["concept_id"],)
        ).fetchone()
        event_id = record_event_in_transaction(
            conn,
            chat_id,
            "learning_recall_completed",
            "learning",
            "recall_card",
            str(card_id),
            {
                "attempt_id": attempt_id,
                "concept_id": card["concept_id"],
                "quality": quality,
                "coverage": coverage,
                "next_due_at": schedule["due_at"],
            },
            current.isoformat(),
        )
        attempt = conn.execute(
            "SELECT * FROM learning_recall_attempts WHERE id=?", (attempt_id,)
        ).fetchone()
    if event_id is not None:
        dispatch_recorded_event(event_id)
    return dict(attempt), True, dict(updated_card), dict(concept)


def recall_summary(
    roadmap_id: int | None = None,
    days: int = 7,
    now: datetime | None = None,
) -> dict:
    init_db()
    current = _now(now)
    cutoff = (current - timedelta(days=max(1, min(int(days), 365)))).isoformat()
    conditions = ["attempt.created_at>=?"]
    params: list[object] = [cutoff]
    if roadmap_id is not None:
        conditions.append("card.roadmap_id=?")
        params.append(roadmap_id)
    with connect() as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS attempts,
                   AVG(attempt.keyword_coverage) AS average_coverage,
                   SUM(CASE WHEN attempt.quality<3 THEN 1 ELSE 0 END) AS lapses
            FROM learning_recall_attempts attempt
            JOIN learning_recall_cards card ON card.id=attempt.card_id
            WHERE {' AND '.join(conditions)}
            """,
            params,
        ).fetchone()
        due = conn.execute(
            """
            SELECT COUNT(*)
            FROM learning_recall_cards
            WHERE status='active' AND due_at<=?
              AND (? IS NULL OR roadmap_id=?)
            """,
            (current.isoformat(), roadmap_id, roadmap_id),
        ).fetchone()[0]
    return {
        "attempts": int(row["attempts"] or 0),
        "average_coverage": row["average_coverage"],
        "lapses": int(row["lapses"] or 0),
        "due": int(due or 0),
    }


@tool
def learning_create_recall_card(
    concept_id: int,
    question: str,
    expected_answer: str,
    answer_keywords: list[str] | None = None,
    source_reference: str = "",
    idempotency_key: str = "",
) -> str:
    """Buat recall card immutable yang terhubung ke konsep dan evidence source."""
    try:
        card, created = create_recall_card(
            concept_id,
            question,
            expected_answer,
            answer_keywords,
            source_reference,
            idempotency_key,
        )
    except (LookupError, ValueError) as exc:
        return f"Recall card tidak dapat dibuat: {exc}"
    state = "dibuat" if created else "sudah tersedia"
    return f"Recall card #{card['id']} {state} dan siap direview."


@tool
def learning_due_recall(roadmap_id: int | None = None, limit: int = 5) -> str:
    """Tampilkan pertanyaan recall yang jatuh tempo tanpa membocorkan expected answer."""
    cards = due_recall_cards(roadmap_id, limit)
    if not cards:
        return "Tidak ada recall yang jatuh tempo."
    lines = ["*Active Recall Due*"]
    for card in cards:
        lines.extend(
            [
                "",
                f"#{card['id']} [{card['concept_title']}]",
                card["question"],
                f"Jawab: `/recall answer {card['id']} <confidence 1-5> <jawaban>`",
            ]
        )
    return "\n".join(lines)


@tool
def learning_submit_recall_answer(
    card_id: int,
    answer: str,
    confidence: int,
    idempotency_key: str = "",
    chat_id: str = "system",
) -> str:
    """Nilai jawaban dari keyword eksplisit, catat evidence, dan jadwalkan review berikutnya."""
    try:
        attempt, created, card, concept = submit_recall_answer(
            card_id,
            answer,
            confidence,
            idempotency_key,
            chat_id,
        )
    except (LookupError, ValueError) as exc:
        return f"Jawaban recall tidak dapat disimpan: {exc}"
    state = "dinilai" if created else "sudah dinilai sebelumnya"
    return (
        f"*Recall #{card_id} {state}*\n"
        f"Coverage keyword: {float(attempt['keyword_coverage']):.0%}\n"
        f"Quality: {attempt['quality']}/5 | Confidence: {attempt['confidence']}/5\n"
        f"Expected answer: {card['expected_answer']}\n"
        f"Mastery konsep: {float(concept['mastery']):.0%}\n"
        f"Review berikutnya: {attempt['next_due_at']}"
    )
