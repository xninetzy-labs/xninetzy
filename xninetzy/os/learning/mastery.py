from __future__ import annotations

import time
from dataclasses import dataclass

from xninetzy.schemas.learning_session import (
    AttemptRecord,
    ConceptMastery,
    MASTERY_STATES,
)


@dataclass
class MasteryUpdate:
    concept_id: str
    old_state: str
    new_state: str
    dimensions: dict[str, float]
    next_review: float
    reason: str


DIMENSION_WEIGHTS = {
    "understanding": 0.20,
    "retrieval": 0.20,
    "application": 0.20,
    "transfer": 0.20,
    "explanation": 0.20,
}


def update_mastery(mastery: ConceptMastery, attempt: AttemptRecord) -> MasteryUpdate:
    old_state = mastery.mastery_state
    score = 1.0 if attempt.correct else 0.0
    if attempt.independent:
        score = min(1.0, score + 0.2)
    mastery.attempt_count += 1
    mastery.understanding = _decay(mastery.understanding, score, weight=0.3)
    if attempt.correct and not attempt.hint_level_used:
        mastery.retrieval = _decay(mastery.retrieval, score, weight=0.4)
    if attempt.correct and attempt.independent:
        mastery.application = _decay(mastery.application, score, weight=0.4)
    if "transfer" in attempt.task.lower():
        mastery.transfer = _decay(mastery.transfer, score, weight=0.5)
    if attempt.correct and len(attempt.user_answer) > 50:
        mastery.explanation = _decay(mastery.explanation, score, weight=0.4)
    composite = _composite(mastery)
    new_state = _classify_state(composite)
    mastery.mastery_state = new_state
    mastery.confidence = attempt.confidence_after
    mastery.last_practiced = attempt.timestamp
    mastery.review_due = _next_review(mastery, composite)
    mastery.error_rate = (mastery.error_rate * (mastery.attempt_count - 1) + (0 if attempt.correct else 1)) / mastery.attempt_count
    return MasteryUpdate(
        concept_id=mastery.concept_id,
        old_state=old_state,
        new_state=new_state,
        dimensions={
            "understanding": mastery.understanding,
            "retrieval": mastery.retrieval,
            "application": mastery.application,
            "transfer": mastery.transfer,
            "explanation": mastery.explanation,
        },
        next_review=mastery.review_due,
        reason=f"Attempt correct={attempt.correct} independent={attempt.independent}",
    )


def _decay(prev: float, score: float, weight: float) -> float:
    return max(0.0, min(1.0, prev * (1 - weight) + score * weight))


def _composite(mastery: ConceptMastery) -> float:
    return sum(
        getattr(mastery, dim) * w for dim, w in DIMENSION_WEIGHTS.items()
    )


def _classify_state(score: float) -> str:
    if score >= 0.85:
        return "TRANSFERABLE"
    if score >= 0.70:
        return "STRONG"
    if score >= 0.55:
        return "FUNCTIONAL"
    if score >= 0.40:
        return "DEVELOPING"
    if score >= 0.20:
        return "FRAGILE"
    if score > 0.0:
        return "INTRODUCED"
    return "UNKNOWN"


def _next_review(mastery: ConceptMastery, composite: float) -> float:
    if composite >= 0.85:
        interval = 7 * 24 * 3600
    elif composite >= 0.70:
        interval = 3 * 24 * 3600
    elif composite >= 0.55:
        interval = 24 * 3600
    elif composite >= 0.40:
        interval = 6 * 3600
    else:
        interval = 3600
    return mastery.last_practiced + interval if mastery.last_practiced else time.time() + interval


def mastery_gaps(mastery_map: dict[str, ConceptMastery], threshold: float = 0.6) -> list[str]:
    return [cid for cid, m in mastery_map.items() if _composite(m) < threshold]


def mastery_review_queue(mastery_map: dict[str, ConceptMastery]) -> list[tuple[str, float]]:
    return sorted(
        ((cid, m.review_due) for cid, m in mastery_map.items() if m.review_due > 0),
        key=lambda x: x[1],
    )


def independence_score(attempts: list[AttemptRecord]) -> float:
    if not attempts:
        return 0.0
    independent = sum(1 for a in attempts if a.independent)
    low_hint = sum(1 for a in attempts if a.hint_level_used <= 1)
    return round((independent + low_hint) / (2 * len(attempts)), 2)
