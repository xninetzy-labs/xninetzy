from __future__ import annotations

import json

import pytest

from xninetzy.tools.ecosystem.security_tools import (
    security_correlate,
    security_scope,
)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "correlate_test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def test_correlate_groups_same_asset_location(sqlite_env):
    hits = [
        {"asset": "api.example.com", "location": "/v1/users", "category": "auth_bypass", "severity": "high", "confidence": 0.7, "scanner": "sast", "title": "missing auth check"},
        {"asset": "api.example.com", "location": "/v1/users", "category": "auth_bypass", "severity": "critical", "confidence": 0.9, "scanner": "headers", "title": "missing WWW-Authenticate"},
    ]
    out = _invoke(security_correlate, hits=hits)
    assert out["finding_count"] == 1
    finding = out["findings"][0]
    assert finding["hit_count"] == 2
    assert finding["severity"] == "critical"
    assert "sast" in finding["scanners"]
    assert "headers" in finding["scanners"]


def test_correlate_tier_high_when_three_scanners_agree(sqlite_env):
    hits = [
        {"asset": "x.test", "location": "/a", "category": "sqli", "severity": "high", "confidence": 0.6, "scanner": "sast"},
        {"asset": "x.test", "location": "/a", "category": "sqli", "severity": "high", "confidence": 0.7, "scanner": "deps"},
        {"asset": "x.test", "location": "/a", "category": "sqli", "severity": "medium", "confidence": 0.5, "scanner": "headers"},
    ]
    out = _invoke(security_correlate, hits=hits)
    assert out["findings"][0]["confidence_tier"] == "high"


def test_correlate_tier_low_for_single_scanner_low_severity(sqlite_env):
    hits = [
        {"asset": "x.test", "location": "/a", "category": "info_leak", "severity": "info", "confidence": 0.3, "scanner": "headers"},
    ]
    out = _invoke(security_correlate, hits=hits)
    assert out["findings"][0]["confidence_tier"] == "low"


def test_correlate_distinct_assets_dont_merge(sqlite_env):
    hits = [
        {"asset": "a.test", "location": "/x", "category": "sqli", "severity": "high", "confidence": 0.7, "scanner": "sast"},
        {"asset": "b.test", "location": "/x", "category": "sqli", "severity": "high", "confidence": 0.8, "scanner": "sast"},
    ]
    out = _invoke(security_correlate, hits=hits)
    assert out["finding_count"] == 2


def test_correlate_empty_returns_error(sqlite_env):
    out = _invoke(security_correlate, hits=[])
    assert "error" in out


def test_correlate_persist_requires_scope(sqlite_env):
    out = _invoke(security_correlate, hits=[{"asset": "x.test", "location": "/a", "category": "sqli"}], persist=True)
    assert "error" in out


def test_correlate_persists_with_valid_scope(sqlite_env):
    scope_out = _invoke(
        security_scope,
        owner="misbah",
        targets=["https://example.com"],
        rationale="authorized pentest",
        duration_days=1,
        chat_id="c1",
        sender_id="misbah",
    )
    scope_token = scope_out["scope_token"]
    hits = [
        {"asset": "https://example.com", "location": "/login", "category": "auth_bypass", "severity": "high", "confidence": 0.8, "scanner": "sast", "title": "auth"},
        {"asset": "https://example.com", "location": "/login", "category": "auth_bypass", "severity": "critical", "confidence": 0.9, "scanner": "headers", "title": "headers"},
    ]
    out = _invoke(security_correlate, hits=hits, persist=True, scope_token=scope_token)
    assert out["finding_count"] == 1
    assert out["findings"][0]["persisted"] is True


def test_correlate_rejects_out_of_scope_asset(sqlite_env):
    scope_out = _invoke(
        security_scope,
        owner="misbah",
        targets=["https://example.com"],
        rationale="scope test",
        duration_days=1,
        chat_id="c1",
        sender_id="misbah",
    )
    scope_token = scope_out["scope_token"]
    hits = [
        {"asset": "evil.test", "location": "/login", "category": "auth_bypass", "severity": "high", "confidence": 0.8, "scanner": "sast"},
    ]
    out = _invoke(security_correlate, hits=hits, persist=True, scope_token=scope_token)
    assert "persist_failures" in out
    assert any("out of scope" in f for f in out["persist_failures"])
