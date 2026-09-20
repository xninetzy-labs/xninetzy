from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


PHASE_PLANNED: str = "planned"
PHASE_READY: str = "ready"
PHASE_RUNNING: str = "running"
PHASE_PAUSED: str = "paused"
PHASE_SUBMITTED: str = "submitted"
PHASE_GRADED: str = "graded"
PHASE_FAILED: str = "failed"
PHASE_CANCELLED: str = "cancelled"

VALID_PHASES: frozenset[str] = frozenset(
    {
        PHASE_PLANNED,
        PHASE_READY,
        PHASE_RUNNING,
        PHASE_PAUSED,
        PHASE_SUBMITTED,
        PHASE_GRADED,
        PHASE_FAILED,
        PHASE_CANCELLED,
    }
)

RunPhase: str = str


ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    PHASE_PLANNED: frozenset({PHASE_READY, PHASE_CANCELLED}),
    PHASE_READY: frozenset({PHASE_RUNNING, PHASE_CANCELLED}),
    PHASE_RUNNING: frozenset(
        {PHASE_PAUSED, PHASE_SUBMITTED, PHASE_FAILED, PHASE_CANCELLED}
    ),
    PHASE_PAUSED: frozenset({PHASE_RUNNING, PHASE_CANCELLED}),
    PHASE_SUBMITTED: frozenset({PHASE_GRADED, PHASE_FAILED}),
    PHASE_GRADED: frozenset(),
    PHASE_FAILED: frozenset({PHASE_READY}),
    PHASE_CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class ExamRunState:
    run_id: str
    scenario_id: str
    phase: RunPhase
    score: float | None = None
    started_at: str = ""
    updated_at: str = ""
    history: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def is_terminal(self) -> bool:
        return self.phase in {PHASE_GRADED, PHASE_CANCELLED}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def transition_run(
    state: ExamRunState,
    target: RunPhase,
    *,
    now: str | None = None,
    note: str | None = None,
    score: float | None = None,
) -> ExamRunState:
    if target not in VALID_PHASES:
        raise ValueError(f"invalid target phase {target!r}")
    if target not in ALLOWED_TRANSITIONS[state.phase]:
        raise ValueError(
            f"cannot transition from {state.phase} to {target}"
        )
    stamp = now or _utcnow()
    history_entry = {
        "from": state.phase,
        "to": target,
        "at": stamp,
        "note": note or "",
    }
    return ExamRunState(
        run_id=state.run_id,
        scenario_id=state.scenario_id,
        phase=target,
        score=score if score is not None else state.score,
        started_at=state.started_at or stamp,
        updated_at=stamp,
        history=state.history + (history_entry,),
    )