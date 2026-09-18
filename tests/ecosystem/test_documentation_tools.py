from __future__ import annotations

import json
from pathlib import Path

import pytest

from xninetzy.tools.ecosystem.documentation_tools import (
    adr_generate,
    implementation_record,
    learning_record,
    security_finding_record,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path / "vault"


def test_adr_generate_writes_file(vault_env):
    out = _invoke(
        adr_generate,
        title="Use sqlite WAL for harness storage",
        context="Single-writer + multi-reader concurrency required.",
        decision="Use sqlite WAL mode + busy_timeout=5s.",
        consequences=["+ concurrent reads", "- extra fsync on checkpoint"],
        alternatives=["Postgres single-tenant", "JSONL append-only log"],
        tags=["storage", "harness"],
    )
    assert out["kind"] == "adr"
    assert Path(out["path"]).exists()
    text = Path(out["path"]).read_text()
    assert "---" in text
    assert "kind: adr" in text
    assert "# Use sqlite WAL for harness storage" in text


def test_implementation_record_contains_steps(vault_env):
    out = _invoke(
        implementation_record,
        title="Phase S7 harness router",
        summary="Add capability router tools for intent resolution.",
        scope="xninetzy/tools/ecosystem/harness_router_tools.py",
        steps=["Add intent_resolve", "Add evidence_normalize", "Add recovery_choose"],
        tests=["tests/ecosystem/test_harness_router_tools.py"],
        risks=["Regression in capability routing"],
        related_artifacts=["docs/superpowers/specs/section-5.md"],
    )
    assert out["kind"] == "implementation_record"
    text = Path(out["path"]).read_text()
    assert "1. Add intent_resolve" in text
    assert "## Verification" in text
    assert "## Risks" in text


def test_security_finding_record_writes_frontmatter(vault_env):
    out = _invoke(
        security_finding_record,
        title="Missing CSP header on login endpoint",
        asset="https://example.com",
        severity="high",
        category="headers",
        evidence="Response lacks Content-Security-Policy header.",
        impact="XSS via reflected input possible.",
        remediation="Add strict CSP with default-src 'self'.",
        regression_test="tests/ecosystem/test_security_correlate.py::test_correlate_persists_with_valid_scope",
        scope_token="scope-abc",
        confidence=0.9,
    )
    assert out["severity"] == "high"
    text = Path(out["path"]).read_text()
    assert "scope_token: scope-abc" in text
    assert "severity: high" in text
    assert "## Remediation" in text


def test_learning_record_with_references(vault_env):
    out = _invoke(
        learning_record,
        topic="FastMCP over stdio",
        takeaway="MCP servers stay deterministic; clients reason and call tools.",
        context="MCP 2025-06-18 spec.",
        references=["https://modelcontextprotocol.io", "https://github.com/modelcontextprotocol/python-sdk"],
        confidence=0.8,
    )
    assert out["kind"] == "learning_record"
    text = Path(out["path"]).read_text()
    assert "## References" in text
    assert "modelcontextprotocol.io" in text


def test_adr_generate_normalizes_status(vault_env):
    out = _invoke(adr_generate, title="Test", context="c", decision="d", status="INVALID")
    assert out["status"] == "proposed"


def test_security_finding_record_normalizes_severity(vault_env):
    out = _invoke(security_finding_record, title="x", asset="a", severity="garbage", category="c", evidence="e")
    assert out["severity"] == "medium"


def test_slug_handles_special_chars(vault_env):
    out = _invoke(adr_generate, title="Some / Weird? Title!", context="c", decision="d")
    path = Path(out["path"])
    assert path.exists()
    assert "/" not in path.stem or "weird" in path.stem.lower()
