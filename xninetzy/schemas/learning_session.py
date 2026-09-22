from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


HINT_LADDER = {
    0: "no_hint",
    1: "restate_task",
    2: "point_to_concept",
    3: "point_to_subproblem",
    4: "strategic_hint",
    5: "next_step",
    6: "partial_solution",
    7: "full_worked_solution",
}


MASTERY_STATES = {
    "UNKNOWN",
    "INTRODUCED",
    "FRAGILE",
    "DEVELOPING",
    "FUNCTIONAL",
    "STRONG",
    "TRANSFERABLE",
}


LEARNING_MODES = {
    "LEARN",
    "PRACTICE",
    "QUIZ",
    "EXAM",
    "REVIEW",
    "DEBUG",
    "PROJECT",
    "RESEARCH",
    "TEACH_BACK",
    "FLASHCARD",
    "DRILL",
    "REFLECTION",
}


ANSWER_RELEASE_POLICY = {
    "DIRECT_ANSWER",
    "GUIDED_SOLUTION",
    "SOCRATIC",
    "HINT",
    "EXPLANATION",
    "WORKED_EXAMPLE",
    "PRACTICE",
}


ERROR_TYPES = {
    "CONCEPTUAL",
    "PROCEDURAL",
    "ARITHMETIC",
    "READING",
    "ASSUMPTION",
    "STRATEGY",
    "IMPLEMENTATION",
    "DEBUGGING",
    "MEMORY",
    "TRANSFER",
    "METACOGNITIVE",
}


@dataclass
class ConceptMastery:
    concept_id: str = ""
    understanding: float = 0.0
    retrieval: float = 0.0
    application: float = 0.0
    transfer: float = 0.0
    explanation: float = 0.0
    confidence: float = 0.5
    mastery_state: str = "UNKNOWN"
    last_practiced: float = 0.0
    attempt_count: int = 0
    error_rate: float = 0.0
    review_due: float = 0.0


@dataclass
class LearningError:
    error_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    concept_id: str = ""
    error_type: str = "CONCEPTUAL"
    user_attempt: str = ""
    expected: str = ""
    actual: str = ""
    root_cause: str = ""
    correction: str = ""
    retest_status: str = "pending"
    frequency: int = 1
    timestamp: float = field(default_factory=time.time)


@dataclass
class Misconception:
    misconception_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    concept_id: str = ""
    description: str = ""
    evidence: str = ""
    severity: str = "medium"
    correction: str = ""
    verification: str = ""


@dataclass
class HintEvent:
    hint_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    concept_id: str = ""
    hint_level: int = 0
    hint_text: str = ""
    learner_progressed: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class AttemptRecord:
    attempt_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    concept_id: str = ""
    task: str = ""
    user_answer: str = ""
    confidence_before: float = 0.5
    confidence_after: float = 0.5
    correct: bool = False
    hint_level_used: int = 0
    independent: bool = False
    feedback: str = ""
    error_type: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class LearningSession:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = ""
    subject: str = ""
    topic: str = ""
    goal: str = ""
    level: str = "beginner"
    mode: str = "LEARN"
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    current_concept_id: str = ""
    current_difficulty: str = "moderate"
    mastery_snapshot: dict[str, ConceptMastery] = field(default_factory=dict)
    attempts: list[AttemptRecord] = field(default_factory=list)
    errors: list[LearningError] = field(default_factory=list)
    misconceptions: list[Misconception] = field(default_factory=list)
    hints: list[HintEvent] = field(default_factory=list)
    completed_items: list[str] = field(default_factory=list)
    review_items: list[str] = field(default_factory=list)
    reflection: str = ""
    next_action: str = ""
    answer_release_policy: str = "GUIDED_SOLUTION"
    hint_level: int = 0
    scaffold_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearnerProfile:
    user_id: str = ""
    goals: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    current_level: str = "beginner"
    preferred_language: str = "en"
    available_minutes_per_week: int = 0
    constraints: list[str] = field(default_factory=list)
    active_projects: list[str] = field(default_factory=list)
    mastery_map: dict[str, ConceptMastery] = field(default_factory=dict)
    common_errors: list[LearningError] = field(default_factory=list)
    confidence_calibration: dict[str, float] = field(default_factory=dict)
    study_patterns: dict[str, Any] = field(default_factory=dict)


@dataclass
class PedagogyPolicy:
    user_id: str = ""
    default_hint_level: int = 0
    question_frequency: str = "moderate"
    review_timing: str = "spaced"
    difficulty_strategy: str = "adaptive"
    feedback_depth: str = "standard"
    answer_release_policy: str = "GUIDED_SOLUTION"
    scaffold_fading: bool = True
    max_hint_level: int = 7
    require_independent_attempt: bool = True


def hint_level_name(level: int) -> str:
    return HINT_LADDER.get(level, "unknown")


def next_hint_level(current: int) -> int:
    return min(current + 1, 7)
