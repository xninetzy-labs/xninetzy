from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCENARIO_DRY_RUN: str = "dry_run"
SCENARIO_PRACTICE: str = "practice"
SCENARIO_EXAM: str = "exam"

VALID_SCENARIOS: frozenset[str] = frozenset(
    {SCENARIO_DRY_RUN, SCENARIO_PRACTICE, SCENARIO_EXAM}
)


@dataclass(frozen=True, slots=True)
class ExamScenario:
    scenario_id: str
    fixture_id: str
    kind: str
    time_limit_minutes: int
    pass_threshold: float
    authorized: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def build_scenario(
    *,
    scenario_id: str,
    fixture_id: str,
    kind: str,
    time_limit_minutes: int,
    pass_threshold: float,
    authorized: bool = False,
    metadata: dict[str, Any] | None = None,
) -> ExamScenario:
    if not scenario_id:
        raise ValueError("scenario_id is required")
    if not fixture_id:
        raise ValueError("fixture_id is required")
    if kind not in VALID_SCENARIOS:
        raise ValueError(f"invalid scenario kind {kind!r}")
    if time_limit_minutes <= 0:
        raise ValueError("time_limit_minutes must be positive")
    if not (0.0 <= pass_threshold <= 1.0):
        raise ValueError("pass_threshold must be between 0.0 and 1.0")
    return ExamScenario(
        scenario_id=scenario_id,
        fixture_id=fixture_id,
        kind=kind,
        time_limit_minutes=time_limit_minutes,
        pass_threshold=pass_threshold,
        authorized=authorized,
        metadata=dict(metadata or {}),
    )