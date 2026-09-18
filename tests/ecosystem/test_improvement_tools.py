from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.improvement_tools import (
    improvement_approve,
    improvement_detect,
    improvement_evaluate,
    improvement_list,
    improvement_propose,
    improvement_regress,
    improvement_reject,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "imp_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def test_detect_emits_event(sqlite_env):
    out = _invoke(
        improvement_detect,
        scope="tool",
        signal="repo_search latency up 3x",
        target_kind="tool",
        target_id="repo_search",
        notes="burst on large repos",
        owner="misbah",
    )
    assert out["signal_id"].startswith("sig-")


def test_propose_creates_proposal(sqlite_env):
    out = _invoke(
        improvement_propose,
        scope="tool",
        title="cap repo_search latency",
        rationale="large repos timeout",
        target_kind="tool",
        target_id="repo_search",
        rollout="candidate",
        metrics={"p95_ms": 1500},
        owner="misbah",
        idempotency_key="p-1",
    )
    assert out["proposal_id"].startswith("imp-")
    assert out["status"] == "proposed"


def test_propose_rejects_unknown_scope(sqlite_env):
    out = _invoke(improvement_propose, scope="other", title="x", rationale="y", owner="misbah")
    assert "error" in out


def test_propose_rejects_empty_title(sqlite_env):
    out = _invoke(improvement_propose, scope="tool", title="", rationale="x", owner="misbah")
    assert "error" in out


def test_evaluate_records_verdict(sqlite_env):
    proposal = _invoke(improvement_propose, scope="tool", title="x", rationale="r", owner="misbah", idempotency_key="ex1")
    out = _invoke(improvement_evaluate, proposal_id=proposal["proposal_id"], metric_name="success_rate", baseline=0.7, candidate=0.9)
    assert out["verdict"] == "improved"
    assert out["delta"] == pytest.approx(0.2)


def test_evaluate_marks_regression(sqlite_env):
    proposal = _invoke(improvement_propose, scope="tool", title="x", rationale="r", owner="misbah", idempotency_key="exr")
    out = _invoke(improvement_evaluate, proposal_id=proposal["proposal_id"], metric_name="recall", baseline=0.8, candidate=0.6)
    assert out["verdict"] == "regressed"


def test_approve_sets_rollout_canary(sqlite_env):
    proposal = _invoke(improvement_propose, scope="tool", title="x", rationale="r", owner="misbah", idempotency_key="ap1")
    out = _invoke(improvement_approve, proposal_id=proposal["proposal_id"], approver="lead", rationale="safe")
    assert out["status"] == "approved"


def test_reject_marks_status(sqlite_env):
    proposal = _invoke(improvement_propose, scope="tool", title="x", rationale="r", owner="misbah", idempotency_key="rj1")
    out = _invoke(improvement_reject, proposal_id=proposal["proposal_id"], rationale="risky")
    assert out["status"] == "rejected"


def test_regress_emits_event_and_retires(sqlite_env):
    proposal = _invoke(improvement_propose, scope="tool", title="x", rationale="r", owner="misbah", idempotency_key="rg1")
    out = _invoke(improvement_regress, proposal_id=proposal["proposal_id"], metric_name="recall", observed_value=0.5, threshold=0.7)
    assert out["regression"] is True


def test_list_returns_owner_proposals(sqlite_env):
    _invoke(improvement_propose, scope="tool", title="a", rationale="r", owner="userA", idempotency_key="l1")
    _invoke(improvement_propose, scope="tool", title="b", rationale="r", owner="userA", idempotency_key="l2")
    out = json.loads(improvement_list.invoke({"owner": "userA", "limit": 5}))
    assert out["summary"].startswith("2 proposal")
