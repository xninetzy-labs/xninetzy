from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.harness_router_tools import (
    claim_ledger_record,
    confidence_score,
    evidence_normalize,
    intent_resolve,
    recovery_choose,
    task_state_record,
    tool_route,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "router_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def test_intent_resolve_security_audit(sqlite_env):
    out = _invoke(intent_resolve, query="audit endpoint vulnerability sql injection", top_n=3)
    domains = [intent["domain"] for intent in out["intents"]]
    assert domains[0] == "security"


def test_intent_resolve_research_query(sqlite_env):
    out = _invoke(intent_resolve, query="research paper evidence-based", top_n=2)
    assert out["intents"][0]["domain"] == "research"


def test_intent_resolve_fallback_general(sqlite_env):
    out = _invoke(intent_resolve, query="zzz qqq", top_n=2)
    assert out["intents"][0]["domain"] == "general"


def test_evidence_normalize_aggregates_confidence(sqlite_env):
    out = _invoke(
        evidence_normalize,
        tool_name="web_extract",
        claim="X is a primary source",
        evidence=[
            {"text": "URL a", "confidence": 0.9},
            {"text": "URL b", "confidence": 0.7},
            {"text": "URL c", "confidence": 0.5},
        ],
    )
    assert out["combined_confidence"] > 0.6
    assert out["evidence_count"] == 3


def test_recovery_chooses_known_strategy(sqlite_env):
    out = _invoke(recovery_choose, failure_class="TIMEOUT", attempted_tool="repo_search")
    assert out["strategy"] == "shrink_scope_then_retry"


def test_recovery_chooses_unknown_class_falls_back(sqlite_env):
    out = _invoke(recovery_choose, failure_class="INVALID_NEW_CLASS")
    assert out["strategy"] == "classify_first"


def test_recovery_ocr_failure_maps_to_preprocess(sqlite_env):
    out = _invoke(recovery_choose, failure_class="OCR_FAILURE", attempted_tool="image_ocr")
    assert "image_preprocess" in out["candidate_tools"]


def test_claim_ledger_record_persists(sqlite_env):
    out = _invoke(
        claim_ledger_record,
        claim="X works",
        source_urls=["https://a.example", "https://b.example"],
        confidence=0.85,
    )
    assert out["claim_id"].startswith("claim-")
    assert out["confidence"] == 0.85


def test_claim_ledger_below_threshold_no_episode(sqlite_env):
    out = _invoke(claim_ledger_record, claim="weak claim", source_urls=["u"], confidence=0.1)
    assert out["claim_id"].startswith("claim-")


def test_confidence_score_aggregate(sqlite_env):
    out = _invoke(
        confidence_score,
        claims=[
            {"claim": "A", "confidence": 0.9, "source_count": 3},
            {"claim": "B", "confidence": 0.4, "source_count": 1},
        ],
    )
    assert out["claim_count"] == 2
    assert 0.0 <= out["aggregate_score"] <= 1.0


def test_confidence_score_empty_returns_error(sqlite_env):
    out = _invoke(confidence_score, claims=[])
    assert "error" in out


def test_tool_route_ranks_relevant(sqlite_env):
    out = json.loads(tool_route.invoke({"query": "search repository symbol", "top_n": 50}))
    item_names = [item["tool_name"] for item in out["items"]]
    assert any(name.startswith("repo_") or name == "search" for name in item_names)


def test_tool_route_respects_candidate_set(sqlite_env):
    out = json.loads(tool_route.invoke({"query": "image", "candidate_tools": ["image_inspect", "image_ocr"], "top_n": 2}))
    assert all(item["tool_name"].startswith("image_") for item in out["items"])


def test_task_state_record_creates_event(sqlite_env):
    out = _invoke(
        task_state_record,
        intent="audit endpoint",
        context="uacc login flow",
        constraints=["read-only"],
        required_evidence=["headers", "scope"],
        hypothesis="missing CSP",
        owner="misbah",
    )
    assert out["task_id"].startswith("task-")
    assert out["state"] == "INTENT"


def test_task_state_record_rejects_empty_intent(sqlite_env):
    out = _invoke(task_state_record, intent="", context="x")
    assert "error" in out
