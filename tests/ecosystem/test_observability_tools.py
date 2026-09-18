from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.observability_tools import (
    observability_checkpoint,
    observability_emit,
    observability_query,
    observability_recent_checkpoints,
    observability_summary,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "obs_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def test_emit_rejects_unknown_kind(sqlite_env):
    out = _invoke(observability_emit, event_kind="unknown_kind")
    assert "error" in out


def test_emit_rejects_unknown_severity(sqlite_env):
    out = _invoke(observability_emit, event_kind="trace", severity="bogus")
    assert "error" in out


def test_emit_persists_event(sqlite_env):
    out = _invoke(observability_emit, event_kind="trace", severity="info", source="repo_search", subject="file:42")
    assert out["event_id"].startswith("evt-")


def test_query_returns_events(sqlite_env):
    _invoke(observability_emit, event_kind="trace", severity="info", subject="a")
    _invoke(observability_emit, event_kind="log", severity="warning", subject="b")
    out = json.loads(observability_query.invoke({"since_minutes": 5, "limit": 10}))
    assert out["summary"].startswith("2 event")


def test_query_filters_kind(sqlite_env):
    _invoke(observability_emit, event_kind="trace", subject="a")
    _invoke(observability_emit, event_kind="alert", subject="b")
    out = json.loads(observability_query.invoke({"event_kind": "alert", "since_minutes": 5, "limit": 10}))
    assert all(item["event_kind"] == "alert" for item in out["items"])


def test_summary_groups_by_kind(sqlite_env):
    _invoke(observability_emit, event_kind="trace", subject="a")
    _invoke(observability_emit, event_kind="trace", subject="b")
    _invoke(observability_emit, event_kind="alert", subject="c", severity="high")
    out = json.loads(observability_summary.invoke({"since_minutes": 5}))
    kinds = {row["event_kind"]: row["n"] for row in out["by_kind"]}
    assert kinds.get("trace") == 2
    assert kinds.get("alert") == 1


def test_checkpoint_persists(sqlite_env):
    out = _invoke(observability_checkpoint, label="before-migration", payload={"step": 1})
    assert out["kind"] == "checkpoint"


def test_recent_checkpoints_returns_in_order(sqlite_env):
    _invoke(observability_checkpoint, label="alpha")
    _invoke(observability_checkpoint, label="beta")
    out = json.loads(observability_recent_checkpoints.invoke({"limit": 5}))
    labels = [item["subject"] for item in out["items"]]
    assert labels[0] == "beta"
