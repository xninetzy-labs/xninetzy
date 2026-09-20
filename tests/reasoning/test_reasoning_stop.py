from __future__ import annotations

from xninetzy.context.reasoning.stop import (
    AntiLoopSignal,
    STOP_CONTINUE,
    STOP_HALT,
    STOP_REPLAN,
    should_stop,
)


def _step(hypothesis: str, tool: str, outcome: str) -> dict:
    return {"hypothesis": hypothesis, "tool": tool, "outcome": outcome}


def test_should_stop_continues_when_under_budget():
    decision = should_stop(iteration=0, steps=())
    assert decision.outcome == STOP_CONTINUE
    assert decision.is_terminal is False


def test_should_stop_halts_when_success_criteria_met_and_uncertainty_low():
    decision = should_stop(
        iteration=2,
        steps=(_step("a", "t", "ok"), _step("b", "t", "ok")),
        success_criteria_met=True,
        critical_uncertainty=0.1,
        min_iterations=1,
    )
    assert decision.outcome == STOP_HALT
    assert decision.is_terminal is True


def test_should_stop_continues_when_success_but_below_min_iterations():
    decision = should_stop(
        iteration=0,
        success_criteria_met=True,
        critical_uncertainty=0.0,
        min_iterations=2,
    )
    assert decision.outcome == STOP_CONTINUE


def test_should_stop_halts_when_max_iterations_reached():
    decision = should_stop(iteration=10, max_iterations=8)
    assert decision.outcome == STOP_HALT
    assert "max_iterations" in decision.reason


def test_should_stop_replans_on_force_flag():
    decision = should_stop(iteration=1, force_replan=True)
    assert decision.outcome == STOP_REPLAN
    assert decision.reason == "force_replan requested"


def test_should_stop_replans_on_anti_loop_signal():
    steps = (
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
    )
    decision = should_stop(
        iteration=4,
        steps=steps,
        anti_loop_window=4,
    )
    assert decision.outcome == STOP_REPLAN
    assert decision.anti_loop is not None
    assert isinstance(decision.anti_loop, AntiLoopSignal)
    assert decision.anti_loop.repeat_count >= 2


def test_should_stop_continues_when_history_diverse():
    steps = (
        _step("h1", "t1", "ok"),
        _step("h2", "t2", "ok"),
        _step("h3", "t3", "ok"),
        _step("h4", "t4", "ok"),
    )
    decision = should_stop(iteration=4, steps=steps)
    assert decision.outcome == STOP_CONTINUE


def test_should_stop_halts_on_extreme_uncertainty_near_budget():
    decision = should_stop(
        iteration=7,
        critical_uncertainty=0.99,
        max_iterations=8,
    )
    assert decision.outcome == STOP_HALT
    assert "uncertainty" in decision.reason


def test_anti_loop_signal_to_dict():
    signal = AntiLoopSignal(fingerprint="h=1|t=2|o=3", repeat_count=3, window_size=4)
    data = signal.to_dict()
    assert data["fingerprint"] == "h=1|t=2|o=3"
    assert data["repeat_count"] == 3
    assert data["window_size"] == 4


def test_stop_decision_to_dict_includes_anti_loop():
    steps = (
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
    )
    decision = should_stop(iteration=4, steps=steps, anti_loop_window=4)
    data = decision.to_dict()
    assert data["outcome"] == STOP_REPLAN
    assert data["anti_loop"] is not None
    assert data["details"] == {}


def test_empty_steps_no_anti_loop():
    decision = should_stop(iteration=0, steps=(), anti_loop_window=4)
    assert decision.anti_loop is None
    assert decision.outcome == STOP_CONTINUE


def test_anti_loop_window_zero_disables_detection():
    steps = (
        _step("h", "t", "fail"),
        _step("h", "t", "fail"),
    )
    decision = should_stop(iteration=2, steps=steps, anti_loop_window=0)
    assert decision.outcome == STOP_CONTINUE
    assert decision.anti_loop is None
