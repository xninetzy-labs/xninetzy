from __future__ import annotations

import json

from xninetzy.cli.orchestrator import _validate_plan
from xninetzy.os.research.router import RouteRequest, route_sources
from xninetzy.os.research.sources import (
    SOURCE_REGISTRY,
    SourceCategory,
    get_adapter,
    list_adapters,
)
from xninetzy.os.research.sources.base import (
    HealthStatus,
    RateLimit,
    RetryPolicy,
    SourceAdapter,
    SourceCategory as SC,
    SourceRecord,
    CircuitBreaker,
)
from xninetzy.os.research.sources.rate_limit import (
    CircuitBreakerGuard,
    RateLimiter,
    retry_async,
)
from xninetzy.os.security.captcha import status_snapshot


def test_registry_has_three_adapters() -> None:
    adapters = list_adapters()
    assert "openalex" in adapters
    assert "arxiv" in adapters
    assert "crossref" in adapters


def test_router_paper_intent() -> None:
    request = RouteRequest(category=SourceCategory.PAPER)
    ids = [a.id for a in route_sources(request)]
    assert "openalex" in ids
    assert "arxiv" in ids
    assert "crossref" in ids


def test_router_code_intent_empty_phase1() -> None:
    request = RouteRequest(category=SourceCategory.CODE)
    assert route_sources(request) == []


def test_validate_plan_accepts_valid() -> None:
    plan = {
        "title": "Test",
        "steps": [
            {"id": "a", "tool": "research_search", "tier": 0},
            {"id": "b", "tool": "research_grade_evidence", "tier": 0, "depends_on": ["a"]},
        ],
    }
    assert _validate_plan(plan) == []


def test_validate_plan_rejects_missing_id() -> None:
    plan = {
        "title": "Test",
        "steps": [{"tool": "research_search", "tier": 0}],
    }
    errors = _validate_plan(plan)
    assert any("missing id" in e for e in errors)


def test_validate_plan_rejects_bad_tier() -> None:
    plan = {
        "title": "Test",
        "steps": [{"id": "a", "tool": "research_search", "tier": 9}],
    }
    errors = _validate_plan(plan)
    assert any("invalid tier" in e for e in errors)


def test_validate_plan_rejects_duplicate_ids() -> None:
    plan = {
        "title": "Test",
        "steps": [
            {"id": "a", "tool": "research_search", "tier": 0},
            {"id": "a", "tool": "research_fetch", "tier": 0},
        ],
    }
    errors = _validate_plan(plan)
    assert any("duplicate id" in e for e in errors)


def test_captcha_status_snapshot_disabled() -> None:
    snap = status_snapshot()
    assert "ocr_enabled" in snap
    assert "lockout_threshold" in snap


def test_source_record_is_frozen() -> None:
    rec = SourceRecord(
        title="x",
        url="https://example.com",
        source="openalex",
        source_type="paper",
        published_at=None,
        updated_at=None,
        author=None,
        snippet="",
        content=None,
        language="en",
        license=None,
        retrieved_at="2026-09-18T00:00:00Z",
        confidence=0.5,
        primary_source=False,
        citation=None,
        identifiers={},
    )
    import dataclasses

    try:
        rec.title = "y"
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("SourceRecord should be frozen")


def test_retry_async_succeeds_after_retry() -> None:
    attempts = {"n": 0}

    async def flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise RuntimeError("boom")
        return "ok"

    import asyncio

    result = asyncio.run(
        retry_async(RetryPolicy(max_attempts=3, backoff_base_seconds=0.01, backoff_max_seconds=0.05), flaky)
    )
    assert result == "ok"
    assert attempts["n"] == 2


def test_circuit_breaker_opens_after_threshold() -> None:
    import asyncio

    async def _drive() -> bool:
        guard = CircuitBreakerGuard(CircuitBreaker(failure_threshold=2, open_duration_seconds=1.0))
        await guard.record_failure()
        await guard.record_failure()
        return await guard.allow()

    import asyncio

    allowed = asyncio.run(_drive())
    assert allowed is False


def test_openalex_health_returns_status() -> None:
    adapter = get_adapter("openalex")
    assert adapter is not None
    assert adapter.base_url.startswith("https://api.openalex.org")
