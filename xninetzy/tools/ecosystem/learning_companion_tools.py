from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from xninetzy.os.learning import (
    calibrate_confidence,
    decide_hint,
    detect_dependency,
    detect_misconception,
    independence_score,
    mastery_gaps,
    mastery_review_queue,
    next_action,
    scaffold_fade,
    update_mastery,
)
from xninetzy.schemas.learning_session import (
    AttemptRecord,
    ConceptMastery,
    HINT_LADDER,
    LEARNING_MODES,
    LearningSession,
    PedagogyPolicy,
)
from xninetzy.tools.tool_results import to_tool_result


@tool
def learning_session_start(
    user_id: str,
    subject: str,
    topic: str,
    goal: str,
    mode: str = "LEARN",
    level: str = "beginner",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Start a learning session with goal and mode.

    Args:
        user_id: Owner principal.
        subject: Subject domain.
        topic: Topic within subject.
        goal: Concrete learning objective.
        mode: One of LEARNING_MODES (LEARN | PRACTICE | QUIZ | EXAM | REVIEW | DEBUG | PROJECT | RESEARCH | TEACH_BACK | FLASHCARD | DRILL | REFLECTION).
        level: beginner | intermediate | advanced.
        chat_id: Chat ID.
        idempotency_key: Optional replay key.
    """
    if mode not in LEARNING_MODES:
        return to_tool_result(json.dumps({"error": f"Unknown mode {mode}", "valid_modes": sorted(LEARNING_MODES)}))
    session = LearningSession(user_id=user_id, subject=subject, topic=topic, goal=goal, mode=mode, level=level)
    return to_tool_result(json.dumps({"session": {"id": session.session_id, "topic": topic, "mode": mode, "started_at": session.started_at}}, ensure_ascii=False))


@tool
def learning_attempt_submit(
    session_id: str,
    concept_id: str,
    task: str,
    user_answer: str,
    confidence_before: float,
    correct: bool,
    independent: bool = False,
    hint_level_used: int = 0,
    error_type: str = "",
    feedback: str = "",
) -> str:
    """Submit an attempt and update mastery.

    Args:
        session_id: Active session ID.
        concept_id: Target concept.
        task: Task text.
        user_answer: User's response.
        confidence_before: Self-reported confidence 0-1 before answer.
        correct: Whether the attempt was correct.
        independent: Whether solved without help.
        hint_level_used: 0-7.
        error_type: One of ERROR_TYPES (CONCEPTUAL | PROCEDURAL | ...).
        feedback: Generated feedback.
    """
    session = LearningSession(session_id=session_id)
    session.current_concept_id = concept_id
    attempt = AttemptRecord(
        session_id=session_id,
        concept_id=concept_id,
        task=task,
        user_answer=user_answer,
        confidence_before=confidence_before,
        confidence_after=confidence_before,
        correct=correct,
        independent=independent,
        hint_level_used=hint_level_used,
        feedback=feedback,
        error_type=error_type,
    )
    session.attempts.append(attempt)
    mastery = session.mastery_snapshot.get(concept_id) or ConceptMastery(concept_id=concept_id)
    mastery_update = update_mastery(mastery, attempt)
    session.mastery_snapshot[concept_id] = mastery
    dec = decide_hint(session)
    dep = detect_dependency(session)
    return to_tool_result(json.dumps({
        "mastery_update": {
            "old_state": mastery_update.old_state,
            "new_state": mastery_update.new_state,
            "composite": sum(mastery_update.dimensions.values()) / len(mastery_update.dimensions),
        },
        "next_hint_level": dec.level,
        "dependency": dep,
    }, ensure_ascii=False))


@tool
def learning_hint(
    session_id: str,
    concept_id: str,
    error_type: str = "",
) -> str:
    """Decide next hint level for a session.

    Args:
        session_id: Active session.
        concept_id: Target concept.
        error_type: Optional error type.
    """
    session = LearningSession(session_id=session_id)
    session.current_concept_id = concept_id
    from xninetzy.schemas.learning_session import LearningError
    err = LearningError(concept_id=concept_id, error_type=error_type, frequency=3) if error_type else None
    decision = decide_hint(session, error=err)
    return to_tool_result(json.dumps({
        "level": decision.level,
        "level_name": HINT_LADDER.get(decision.level, "unknown"),
        "text": decision.text,
        "escalate": decision.escalate,
    }, ensure_ascii=False))


@tool
def learning_misconception_check(
    session_id: str,
) -> str:
    """Check for recurring misconception patterns in recent attempts.

    Args:
        session_id: Active session.
    """
    session = LearningSession(session_id=session_id)
    mis = detect_misconception(session.attempts)
    if mis is None:
        return to_tool_result(json.dumps({"misconception_detected": False}, ensure_ascii=False))
    return to_tool_result(json.dumps({
        "misconception_detected": True,
        "concept_id": mis.concept_id,
        "description": mis.description,
        "severity": mis.severity,
        "correction": mis.correction,
    }, ensure_ascii=False))


@tool
def learning_calibration(
    session_id: str,
) -> str:
    """Return confidence calibration metrics for a session.

    Args:
        session_id: Active session.
    """
    session = LearningSession(session_id=session_id)
    return to_tool_result(json.dumps(calibrate_confidence(session.attempts), ensure_ascii=False))


@tool
def learning_independence(
    session_id: str,
) -> str:
    """Return independence score for a session.

    Args:
        session_id: Active session.
    """
    session = LearningSession(session_id=session_id)
    return to_tool_result(json.dumps({
        "independence_score": independence_score(session.attempts),
        "attempts_total": len(session.attempts),
    }, ensure_ascii=False))


@tool
def learning_next_action(
    session_id: str,
    mastery_threshold: float = 0.6,
) -> str:
    """Recommend next learning action based on mastery state.

    Args:
        session_id: Active session.
        mastery_threshold: Mastery threshold for next-step decision.
    """
    session = LearningSession(session_id=session_id)
    composite = 0.0
    if session.mastery_snapshot:
        composite = sum(m.understanding + m.retrieval + m.application for m in session.mastery_snapshot.values()) / (3 * len(session.mastery_snapshot))
    action = next_action(session, composite)
    gaps = mastery_gaps(session.mastery_snapshot, mastery_threshold)
    queue = mastery_review_queue(session.mastery_snapshot)
    return to_tool_result(json.dumps({
        "action": action,
        "composite_mastery": round(composite, 3),
        "weak_concepts": gaps,
        "next_review": queue[:5],
    }, ensure_ascii=False))


@tool
def learning_capabilities() -> str:
    """Return learning companion capability snapshot."""
    return to_tool_result(json.dumps({
        "learning_companion": True,
        "pedagogy_engine": True,
        "mastery_engine": True,
        "hint_ladder": True,
        "misconception_detection": True,
        "calibration": True,
        "independence_tracking": True,
        "modes": sorted(LEARNING_MODES),
    }, ensure_ascii=False))


learning_companion_tools = [
    learning_session_start,
    learning_attempt_submit,
    learning_hint,
    learning_misconception_check,
    learning_calibration,
    learning_independence,
    learning_next_action,
    learning_capabilities,
]
