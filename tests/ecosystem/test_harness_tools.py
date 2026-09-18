from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.harness_tools import (
    harness_execute,
    harness_plan,
    harness_recover,
    harness_record_step,
    harness_review,
    harness_trace,
    harness_verify,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "harness_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def test_harness_plan_creates(sqlite_env):
    out = _invoke(
        harness_plan,
        title="verify memory lifecycle",
        steps=["a", "b", "c"],
        required_tools=["memory_episode_store"],
        required_skills=["xninetzy-memory"],
        verification="pytest green",
        owner="misbah",
    )
    assert out["plan_id"].startswith("plan-")
    assert out["step_count"] == 3


def test_harness_plan_rejects_empty(sqlite_env):
    out = _invoke(harness_plan, title="x", steps=[], owner="misbah")
    assert "error" in out


def test_harness_execute_records_started(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    out = _invoke(harness_execute, plan_id=plan["plan_id"])
    assert out["status"] == "in_progress"


def test_harness_record_step_appends_seq(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    a = _invoke(harness_record_step, plan_id=plan["plan_id"], tool_name="memory_episode_store", tool_args={"task": "x"}, outcome="ok")
    b = _invoke(harness_record_step, plan_id=plan["plan_id"], tool_name="memory_failure_store", outcome="ok")
    assert a["sequence"] >= 1
    assert b["sequence"] > a["sequence"]


def test_harness_verify_updates_status(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    out = _invoke(harness_verify, plan_id=plan["plan_id"], evidence="pytest green", passed=True)
    assert out["status"] == "verified"
    assert out["passed"] is True


def test_harness_verify_marks_failure(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    out = _invoke(harness_verify, plan_id=plan["plan_id"], evidence="missing", passed=False)
    assert out["status"] == "failed"


def test_harness_recover_truncates_actions(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    _invoke(harness_record_step, plan_id=plan["plan_id"], tool_name="a")
    _invoke(harness_record_step, plan_id=plan["plan_id"], tool_name="b")
    out = _invoke(harness_recover, plan_id=plan["plan_id"], from_sequence=2, new_status="planned", reason="retry")
    assert out["truncated"] >= 1


def test_harness_trace_returns_actions(sqlite_env):
    plan = _invoke(harness_plan, title="x", steps=["s"], owner="misbah")
    _invoke(harness_record_step, plan_id=plan["plan_id"], tool_name="t1")
    out = json.loads(harness_trace.invoke({"plan_id": plan["plan_id"]}))
    assert "actions" in out
    assert out["actions"][0]["tool_name"] == "t1"


def test_harness_review_lists_owner_plans(sqlite_env):
    _invoke(harness_plan, title="a", steps=["a"], owner="userA")
    _invoke(harness_plan, title="b", steps=["b"], owner="userA")
    out = json.loads(harness_review.invoke({"owner": "userA", "limit": 5}))
    assert out["summary"].startswith("2 rencana")
