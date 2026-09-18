from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.memory_lifecycle_tools import (
    memory_episode_search,
    memory_episode_store,
    memory_failure_store,
    memory_procedure_store,
    memory_promote,
    memory_relevance,
    memory_retire,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "memory_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def _actions():
    return [
        {"tool": "repo_search", "args": {"query": "x"}, "latency_ms": 12, "result": "ok"},
        {"tool": "image_inspect", "args": {"path": "/tmp/a.png"}, "latency_ms": 8, "result": "ok"},
    ]


def test_episode_store_creates_episode(sqlite_env):
    out = _invoke(
        memory_episode_store,
        task="repo.search",
        intent="cari simbol modul",
        plan=["plan.step1", "plan.step2"],
        actions=_actions(),
        outcome="success",
        verification="pytest pass",
        reward=0.85,
        usefulness=0.7,
        owner="misbah",
        idempotency_key="ep-1",
    )
    assert out["episode_id"].startswith("ep-")
    assert out["task"] == "repo.search"
    assert out["reward"] == 0.85
    assert 0.0 <= out["usefulness"] <= 1.0


def test_episode_store_idempotency(sqlite_env):
    a = _invoke(memory_episode_store, task="x", intent="y", plan=["p"], actions=_actions(), owner="misbah", idempotency_key="key-A")
    b = _invoke(memory_episode_store, task="x", intent="y", plan=["p"], actions=_actions(), owner="misbah", idempotency_key="key-A")
    assert a["episode_id"] == b["episode_id"]


def test_episode_search_filters_by_reward(sqlite_env):
    high = _invoke(
        memory_episode_store,
        task="cache fruit lookup",
        intent="lookup by name",
        plan=["p"], actions=_actions(), outcome="success", reward=0.9, usefulness=0.8,
        owner="misbah", idempotency_key="hi",
    )
    _invoke(
        memory_episode_store,
        task="low score entry",
        intent="x",
        plan=["p"], actions=_actions(), outcome="failure", reward=0.1, usefulness=0.1,
        owner="misbah", idempotency_key="lo",
    )
    out = _invoke(memory_episode_search, query="fruit", owner="misbah", limit=5, min_reward=0.5)
    ids = {item["episode_id"] for item in out["items"]}
    assert high["episode_id"] in ids
    assert len(out["items"]) == 1


def test_failure_store_dedup_recurrence(sqlite_env):
    a = _invoke(memory_failure_store, failure_class="TIMEOUT", title="repo_search hang", owner="misbah", idempotency_key="f1")
    b = _invoke(memory_failure_store, failure_class="TIMEOUT", title="repo_search hang", owner="misbah", idempotency_key="f2")
    assert a["deduplicated"] is False
    assert b["deduplicated"] is True
    assert b["recurrence_count"] >= 2


def test_failure_store_rejects_empty(sqlite_env):
    out = _invoke(memory_failure_store, failure_class="", title="x", owner="misbah")
    assert "error" in out


def test_procedure_store_creates_candidate(sqlite_env):
    out = _invoke(
        memory_procedure_store,
        name="quick wiki lookup",
        trigger="user asks open question",
        steps=["web_search", "web_extract", "knowledge_search"],
        tools=["web_search"],
        skills=["research"],
        verification="answer cites source",
        owner="misbah",
        idempotency_key="proc-1",
    )
    assert out["procedure_id"].startswith("proc-")
    assert out["status"] == "candidate"


def test_procedure_store_rejects_empty_steps(sqlite_env):
    out = _invoke(memory_procedure_store, name="x", trigger="y", steps=[], owner="misbah")
    assert "error" in out


def test_promote_raises_procedure_status(sqlite_env):
    proc = _invoke(memory_procedure_store, name="p", trigger="t", steps=["a"], owner="misbah", idempotency_key="pv")
    out = _invoke(memory_promote, source_kind="procedure", source_id=proc["procedure_id"], target_kind="verified", rationale="2x reusable", owner="misbah", idempotency_key="ppv")
    assert out["stage"] == "VERIFIED"


def test_promote_episode_to_promoted(sqlite_env):
    ep = _invoke(memory_episode_store, task="x", intent="y", plan=["p"], actions=_actions(), owner="misbah", idempotency_key="ee")
    out = _invoke(memory_promote, source_kind="episode", source_id=ep["episode_id"], target_kind="promoted", owner="misbah", idempotency_key="epP")
    assert out["stage"] == "PROMOTED"


def test_retire_marks_status(sqlite_env):
    ep = _invoke(memory_episode_store, task="x", intent="y", plan=["p"], actions=_actions(), owner="misbah", idempotency_key="rr")
    out = _invoke(memory_retire, source_kind="episode", source_id=ep["episode_id"], rationale="deprecated", owner="misbah", idempotency_key="rrR")
    assert out["verdict"] == "retired"


def test_retire_unknown_kind_rejected(sqlite_env):
    out = _invoke(memory_retire, source_kind="artifact", source_id="x", owner="misbah")
    assert "error" in out


def test_relevance_combines_kinds(sqlite_env):
    _invoke(memory_episode_store, task="pixel inspect", intent="check image", plan=["p"], actions=_actions(), outcome="success", reward=0.8, owner="misbah", idempotency_key="rel1")
    _invoke(memory_failure_store, failure_class="OCR_FAIL", title="tesseract missing", owner="misbah", idempotency_key="rel2")
    _invoke(memory_procedure_store, name="pixel probe", trigger="image query", steps=["x"], owner="misbah", idempotency_key="rel3")
    out = json.loads(memory_relevance.invoke({"query": "pixel", "owner": "misbah", "episode_limit": 5, "procedure_limit": 5, "failure_limit": 5}))
    assert out["query"] == "pixel"
    assert isinstance(out["episodes"], list)
    assert isinstance(out["procedures"], list)
    assert isinstance(out["failures"], list)
