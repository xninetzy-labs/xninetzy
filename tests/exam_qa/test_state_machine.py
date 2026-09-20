from __future__ import annotations

import pytest

from xninetzy.context.exam_qa.state_machine import (
    PHASE_CANCELLED,
    PHASE_GRADED,
    PHASE_PAUSED,
    PHASE_PLANNED,
    PHASE_READY,
    PHASE_RUNNING,
    PHASE_SUBMITTED,
    ExamRunState,
    transition_run,
)


def _state(phase: str) -> ExamRunState:
    return ExamRunState(
        run_id="r1",
        scenario_id="s1",
        phase=phase,
        started_at="2026-09-20T00:00:00Z",
        updated_at="2026-09-20T00:00:00Z",
    )


def test_happy_path_full_run():
    state = _state(PHASE_PLANNED)
    state = transition_run(state, PHASE_READY, now="2026-09-20T00:01:00Z")
    state = transition_run(state, PHASE_RUNNING, now="2026-09-20T00:02:00Z")
    state = transition_run(state, PHASE_PAUSED, now="2026-09-20T00:03:00Z")
    state = transition_run(state, PHASE_RUNNING, now="2026-09-20T00:04:00Z")
    state = transition_run(state, PHASE_SUBMITTED, now="2026-09-20T00:05:00Z")
    state = transition_run(state, PHASE_GRADED, now="2026-09-20T00:06:00Z", score=0.9)
    assert state.phase == PHASE_GRADED
    assert state.score == 0.9
    assert state.is_terminal()
    assert len(state.history) == 6


def test_cancel_from_planned_is_allowed():
    state = transition_run(_state(PHASE_PLANNED), PHASE_CANCELLED)
    assert state.phase == PHASE_CANCELLED


def test_cannot_jump_planned_to_running():
    with pytest.raises(ValueError):
        transition_run(_state(PHASE_PLANNED), PHASE_RUNNING)


def test_cannot_transition_after_terminal():
    state = transition_run(_state(PHASE_PLANNED), PHASE_READY)
    state = transition_run(state, PHASE_RUNNING)
    state = transition_run(state, PHASE_SUBMITTED)
    state = transition_run(state, PHASE_GRADED)
    with pytest.raises(ValueError):
        transition_run(state, PHASE_RUNNING)


def test_unknown_target_rejected():
    with pytest.raises(ValueError):
        transition_run(_state(PHASE_PLANNED), "wildcard")