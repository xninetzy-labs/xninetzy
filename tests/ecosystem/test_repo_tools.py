from __future__ import annotations

import json

from xninetzy.tools.ecosystem.repo_tools import (
    repo_architecture,
    repo_dependency,
    repo_diff,
    repo_risk,
    repo_search,
    repo_symbol,
    repo_test,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def test_repo_search_returns_ranked_hits():
    out = _invoke(repo_search, query="idempotent_call", limit=10)
    assert out["count"] >= 1
    assert out["hits"][0]["path"].endswith(".py")
    assert out["hits"][0]["line"] >= 1


def test_repo_search_respects_limit_cap():
    out = _invoke(repo_search, query="def", limit=999, glob="**/*.py")
    assert out["limit"] == 200
    assert out["count"] <= 200


def test_repo_search_regex_mode():
    out = _invoke(repo_search, query=r"idempotent_call\(.*scope", use_regex=True, limit=5)
    assert out["regex"] is True
    assert out["count"] >= 1


def test_repo_symbol_finds_function_definition():
    out = _invoke(repo_symbol, name="idempotent_call", limit=5)
    assert out["count"] >= 1
    first = out["matches"][0]
    assert first["file"].endswith("idempotency.py")
    assert first["signature"].startswith("def idempotent_call")
    assert first["line"] >= 1


def test_repo_symbol_handles_unknown_name():
    out = _invoke(repo_symbol, name="__definitely_not_a_symbol_xyz__")
    assert out["count"] == 0
    assert out["matches"] == []


def test_repo_dependency_returns_edges_and_top_lists():
    out = _invoke(repo_dependency, limit=50)
    assert out["module_count"] > 0
    assert isinstance(out["edges"], list)
    assert isinstance(out["most_imported"], list)
    assert out["most_imported"][0]["incoming"] >= 1


def test_repo_dependency_excludes_stdlib_by_default():
    out = _invoke(repo_dependency, limit=200, include_stdlib=False)
    targets = {edge["target"] for edge in out["edges"]}
    assert "json" not in targets
    assert "hashlib" not in targets


def test_repo_test_inventory():
    out = _invoke(repo_test, limit=10)
    assert out["file_count"] >= 1
    assert "pytest" in out["by_framework"]
    assert all(t["count"] >= 1 for t in out["tests"])


def test_repo_diff_handles_no_changes():
    out = _invoke(repo_diff, base="HEAD", target="HEAD", limit=10)
    assert out["base"] == "HEAD"
    assert out["target"] == "HEAD"
    assert out["additions"] == 0
    assert out["deletions"] == 0


def test_repo_diff_returns_structure_on_existing_ref():
    out = _invoke(repo_diff, base="HEAD~0", target="HEAD", limit=5, include_sample=False)
    assert "file_count" in out
    assert "truncated" in out


def test_repo_architecture_emits_binding_files():
    out = _invoke(repo_architecture, depth=2, limit=20)
    assert out["node_count"] >= 1
    binding_paths = [n["path"] for n in out["nodes"] if n.get("binding")]
    assert any("AGENTS.md" in p or "CLAUDE.md" in p for p in binding_paths)


def test_repo_risk_finds_known_patterns():
    out = _invoke(repo_risk, limit=20)
    assert "subprocess" in out["by_rule"]
    high = [f for f in out["findings"] if f["severity"] == "high"]
    assert len(high) >= 1
    assert all(f["file"].endswith(".py") for f in out["findings"])


def test_repo_risk_severity_ordering():
    out = _invoke(repo_risk, limit=100)
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    severities = [f["severity"] for f in out["findings"]]
    assert severities == sorted(severities, key=lambda s: severity_rank.get(s, 99))
