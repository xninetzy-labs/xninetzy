from __future__ import annotations

import json

from xninetzy.tools.internal.reasoning import (
    _STRATEGY_STATE,
    reasoning_classify_depth,
    reasoning_clear_strategy,
    reasoning_critique,
    reasoning_get_depth,
    reasoning_get_strategy,
    reasoning_list_depths,
    reasoning_record_history,
    reasoning_set_strategy,
    reasoning_should_stop,
    reasoning_trace,
)


def _reset():
    _STRATEGY_STATE.clear()


def setup_function(_fn):
    _reset()


def teardown_function(_fn):
    _reset()


def test_reasoning_classify_depth_trivial():
    result = reasoning_classify_depth.invoke(
        {"side_effect": "read_only", "trust_tier": 0}
    )
    assert result["name"] == "trivial"


def test_reasoning_classify_depth_irreversible_high_risk():
    result = reasoning_classify_depth.invoke(
        {"side_effect": "irreversible", "trust_tier": 0}
    )
    assert result["name"] == "high_risk"


def test_reasoning_get_depth_unknown_falls_back():
    result = reasoning_get_depth.invoke({"name": "weird"})
    assert result["name"] == "routine"


def test_reasoning_list_depths_returns_four():
    result = reasoning_list_depths.invoke({})
    names = [d["name"] for d in result]
    assert names == ["trivial", "routine", "complex", "high_risk"]


def test_reasoning_critique_passes():
    result = reasoning_critique.invoke(
        {"expected": "ok", "actual": "ok"}
    )
    assert result["verdict"] == "pass"


def test_reasoning_critique_claims_csv():
    result = reasoning_critique.invoke(
        {
            "expected": "ok",
            "actual": "ok",
            "claims": "alpha,beta,gamma",
        }
    )
    assert result["checked_claims"] == ["alpha", "beta", "gamma"]


def test_reasoning_critique_claims_json_list():
    result = reasoning_critique.invoke(
        {
            "expected": "ok",
            "actual": "ok",
            "claims": json.dumps(["x", "y"]),
        }
    )
    assert result["checked_claims"] == ["x", "y"]


def test_reasoning_should_stop_continues():
    result = reasoning_should_stop.invoke(
        {"iteration": 0, "success_criteria_met": False}
    )
    assert result["outcome"] == "continue"


def test_reasoning_should_stop_halts_on_max():
    result = reasoning_should_stop.invoke(
        {"iteration": 10, "max_iterations": 8}
    )
    assert result["outcome"] == "halt"


def test_reasoning_should_stop_anti_loop():
    history = json.dumps(
        [
            {"hypothesis": "h", "tool": "t", "outcome": "fail"},
            {"hypothesis": "h", "tool": "t", "outcome": "fail"},
            {"hypothesis": "h", "tool": "t", "outcome": "fail"},
            {"hypothesis": "h", "tool": "t", "outcome": "fail"},
        ]
    )
    result = reasoning_should_stop.invoke(
        {"iteration": 4, "history_json": history, "anti_loop_window": 4}
    )
    assert result["outcome"] == "replan"
    assert result["anti_loop"] is not None


def test_reasoning_record_history_appends():
    out1 = reasoning_record_history.invoke(
        {
            "context_key": "ctx-1",
            "request_id": "req-1",
            "hypothesis": "h1",
            "tool": "t1",
            "outcome": "ok",
        }
    )
    assert out1["history_len"] == 1
    out2 = reasoning_record_history.invoke(
        {
            "context_key": "ctx-1",
            "request_id": "req-1",
            "hypothesis": "h2",
            "tool": "t2",
            "outcome": "ok",
        }
    )
    assert out2["history_len"] == 2


def test_reasoning_set_strategy_returns_descriptor():
    out = reasoning_set_strategy.invoke(
        {
            "context_key": "ctx-2",
            "depth": "high_risk",
            "min_iterations": 2,
            "max_iterations": 12,
            "anti_loop_window": 5,
        }
    )
    assert out["depth"] == "high_risk"
    assert out["min_iterations"] == 2
    assert out["max_iterations"] == 12
    assert out["anti_loop_window"] == 5


def test_reasoning_get_strategy_after_set():
    reasoning_set_strategy.invoke(
        {
            "context_key": "ctx-3",
            "depth": "complex",
            "min_iterations": 1,
            "max_iterations": 6,
            "anti_loop_window": 3,
        }
    )
    out = reasoning_get_strategy.invoke({"context_key": "ctx-3"})
    assert out["depth"] == "complex"
    assert out["max_iterations"] == 6


def test_reasoning_get_strategy_unknown_returns_null_depth():
    out = reasoning_get_strategy.invoke({"context_key": "ctx-missing"})
    assert out["depth"] is None


def test_reasoning_clear_strategy_removes_state():
    reasoning_set_strategy.invoke(
        {"context_key": "ctx-4", "depth": "routine"}
    )
    out = reasoning_clear_strategy.invoke({"context_key": "ctx-4"})
    assert out["cleared"] is True
    after = reasoning_get_strategy.invoke({"context_key": "ctx-4"})
    assert after["depth"] is None


def test_reasoning_trace_returns_history_and_counts():
    ctx = "ctx-trace"
    for hypothesis, tool, outcome in (
        ("h1", "search", "ok"),
        ("h2", "search", "ok"),
        ("h3", "validate", "fail"),
    ):
        reasoning_record_history.invoke(
            {
                "context_key": ctx,
                "request_id": "r1",
                "hypothesis": hypothesis,
                "tool": tool,
                "outcome": outcome,
            }
        )
    trace = reasoning_trace.invoke({"context_key": ctx, "last_n": 2})
    assert trace["total_steps"] == 3
    assert len(trace["history"]) == 2
    assert trace["tool_counts"]["search"] == 2
    assert trace["outcome_counts"]["ok"] == 2
    assert trace["outcome_counts"]["fail"] == 1
