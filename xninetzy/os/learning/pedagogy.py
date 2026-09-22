from __future__ import annotations

import time
from dataclasses import dataclass

from xninetzy.schemas.learning_session import (
    AttemptRecord,
    HintEvent,
    HINT_LADDER,
    LearningError,
    LearningSession,
    MASTERY_STATES,
    Misconception,
    PedagogyPolicy,
    next_hint_level,
    hint_level_name,
)


DEFAULT_ERROR_PATTERNS = {
    "CONCEPTUAL": "Missing conceptual understanding — review definition and prerequisite",
    "PROCEDURAL": "Procedure gap — work through worked example step by step",
    "ARITHMETIC": "Arithmetic slip — slow down, verify each step",
    "READING": "Misread the problem — re-read and restate",
    "ASSUMPTION": "Wrong assumption — list explicit assumptions first",
    "STRATEGY": "Wrong strategy — consider alternative approaches",
    "IMPLEMENTATION": "Code bug — isolate minimal reproduction",
    "DEBUGGING": "Debug gap — add diagnostic output / print",
    "MEMORY": "Recall failed — practice active retrieval",
    "TRANSFER": "Cannot transfer — vary the surface context",
    "METACOGNITIVE": "Strategy blind — reflect on approach before solving",
}


@dataclass
class HintDecision:
    level: int
    text: str
    escalate: bool


def decide_hint(session: LearningSession, error: LearningError | None = None, policy: PedagogyPolicy | None = None) -> HintDecision:
    pol = policy or PedagogyPolicy()
    level = session.hint_level
    if session.attempts:
        last = session.attempts[-1]
        if not last.correct and last.hint_level_used >= level:
            level = next_hint_level(level)
        elif last.correct and last.independent:
            level = max(0, level - 1)
    if error and error.frequency >= 3 and level < pol.max_hint_level:
        level = min(level + 2, pol.max_hint_level)
    level = min(level, pol.max_hint_level)
    text = _hint_text(level, session, error)
    escalate = level > session.hint_level
    return HintDecision(level=level, text=text, escalate=escalate)


def _hint_text(level: int, session: LearningSession, error: LearningError | None) -> str:
    name = hint_level_name(level)
    concept = session.current_concept_id or session.topic
    if level == 0:
        return f"Try again. Focus on {concept}."
    if level == 1:
        return f"Restate the task in your own words before solving."
    if level == 2:
        return f"Recall the definition of {concept}."
    if level == 3:
        return f"Break the problem into sub-steps. Identify the smallest sub-problem first."
    if level == 4:
        return f"Strategy hint: start from the constraints, then derive."
    if level == 5:
        return f"Next step: compute the derivative / first logical step."
    if level == 6:
        return f"Partial solution: [first half of solution]. Continue from there."
    return f"Full worked solution shown. Now reproduce from memory and explain why each step holds."


def record_hint(session: LearningSession, decision: HintDecision, progressed: bool = False) -> HintEvent:
    event = HintEvent(
        session_id=session.session_id,
        concept_id=session.current_concept_id,
        hint_level=decision.level,
        hint_text=decision.text,
        learner_progressed=progressed,
    )
    session.hints.append(event)
    session.hint_level = decision.level
    return event


def detect_misconception(attempts: list[AttemptRecord]) -> Misconception | None:
    if len(attempts) < 3:
        return None
    error_counts: dict[str, int] = {}
    for a in attempts[-5:]:
        if not a.correct and a.error_type:
            error_counts[a.error_type] = error_counts.get(a.error_type, 0) + 1
    if not error_counts:
        return None
    dominant = max(error_counts, key=error_counts.get)
    if error_counts[dominant] >= 3:
        return Misconception(
            concept_id=attempts[-1].concept_id,
            description=f"Recurring {dominant} error pattern",
            evidence=f"Detected {error_counts[dominant]} occurrences of {dominant} errors",
            severity="high" if error_counts[dominant] >= 5 else "medium",
            correction=DEFAULT_ERROR_PATTERNS.get(dominant, "Review the concept"),
        )
    return None


def calibrate_confidence(attempts: list[AttemptRecord]) -> dict[str, float]:
    if not attempts:
        return {"calibration_gap": 0.0, "overconfident": 0.0, "underconfident": 0.0}
    gaps = []
    overconf = 0
    underconf = 0
    for a in attempts:
        gap = a.confidence_before - (1.0 if a.correct else 0.0)
        gaps.append(gap)
        if a.confidence_before > 0.7 and not a.correct:
            overconf += 1
        elif a.confidence_before < 0.4 and a.correct:
            underconf += 1
    return {
        "calibration_gap": sum(gaps) / len(gaps),
        "overconfident": overconf / len(attempts),
        "underconfident": underconf / len(attempts),
    }


def detect_dependency(session: LearningSession) -> dict[str, float | bool]:
    if not session.attempts:
        return {"dependency_risk": 0.0, "needs_intervention": False}
    recent = session.attempts[-10:]
    full_solution_reveals = sum(1 for h in session.hints[-10:] if h.hint_level >= 7)
    independent = sum(1 for a in recent if a.independent)
    total = len(recent)
    dependency_risk = full_solution_reveals / max(1, len(session.hints))
    needs_intervention = dependency_risk > 0.5 or (total > 0 and independent / total < 0.3)
    return {
        "dependency_risk": round(dependency_risk, 2),
        "independent_rate": round(independent / total, 2) if total else 0.0,
        "needs_intervention": needs_intervention,
    }


def scaffold_fade(session: LearningSession, mastery: float) -> int:
    if mastery >= 0.85:
        return max(0, session.hint_level - 2)
    if mastery >= 0.65:
        return max(0, session.hint_level - 1)
    return session.hint_level


def next_action(session: LearningSession, mastery: float) -> str:
    if mastery < 0.4:
        return "prerequisite_review"
    if mastery < 0.65:
        return "guided_practice"
    if mastery < 0.85:
        return "variation_practice"
    if session.completed_items and len(session.completed_items) >= 5:
        return "transfer_test"
    return "next_concept"
