from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.os.research.router import RouteRequest, route_by_name, route_sources
from xninetzy.os.research.sources import (
    SourceCategory,
    SourceRecord,
    get_adapter,
)
from xninetzy.tools.tool_results import to_tool_result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _record_to_dict(record: SourceRecord) -> dict[str, Any]:
    return {
        "title": record.title,
        "url": record.url,
        "source": record.source,
        "source_type": record.source_type,
        "published_at": record.published_at,
        "updated_at": record.updated_at,
        "author": record.author,
        "snippet": record.snippet,
        "language": record.language,
        "license": record.license,
        "retrieved_at": record.retrieved_at,
        "confidence": record.confidence,
        "primary_source": record.primary_source,
        "citation": record.citation,
        "identifiers": dict(record.identifiers),
    }


def _emit_checkpoint(plan_id: str, step_id: str, status: str, payload: dict[str, Any]) -> None:
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('harness_checkpoint', 'info', 'research_v2', ?, ?, ?)
            """,
            (
                f"{plan_id}:{step_id}",
                json.dumps({"status": status, **payload}, ensure_ascii=False),
                now,
            ),
        )


def _emit_record_step(plan_id: str, tool_name: str, outcome: str, args: dict[str, Any]) -> None:
    _ensure_db()
    action_id = f"action-{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('harness_action', 'info', 'research_v2', ?, ?, ?)
            """,
            (
                action_id,
                json.dumps({
                    "plan_id": plan_id,
                    "tool_name": tool_name,
                    "args": args,
                    "outcome": outcome,
                }, ensure_ascii=False),
                now,
            ),
        )


def _grade_record(record_dict: dict[str, Any], policy: dict[str, Any]) -> tuple[str, float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if record_dict.get("primary_source"):
        score += 0.20
        reasons.append("primary_source=true")
    identifiers = record_dict.get("identifiers") or {}
    if identifiers.get("doi"):
        score += 0.10
        reasons.append("doi present")
    elif identifiers.get("arxiv"):
        score += 0.05
        reasons.append("arxiv id present")
    published_at = record_dict.get("published_at")
    freshness_days = policy.get("freshness_days")
    if freshness_days and published_at:
        try:
            year = int(str(published_at)[:4])
            age_years = max(0, datetime.now(timezone.utc).year - year)
            if age_years * 365 <= int(freshness_days):
                score += 0.10
                reasons.append("within freshness window")
        except (ValueError, TypeError):
            pass
    license_value = record_dict.get("license")
    if license_value and policy.get("prefer_open_access"):
        score += 0.05
        reasons.append("open license")
    author = record_dict.get("author")
    if author:
        score += 0.05
        reasons.append("author present")
    if record_dict.get("confidence") is None:
        score -= 0.10
        reasons.append("missing confidence metadata")
    if not record_dict.get("snippet"):
        score -= 0.10
        reasons.append("empty snippet")
    bounded = max(0.0, min(score, 1.0))
    if bounded >= 0.75:
        grade = "strong"
    elif bounded >= 0.50:
        grade = "moderate"
    elif bounded >= 0.25:
        grade = "weak"
    else:
        grade = "uncertain"
    return grade, bounded, reasons


def _dedupe(records: list[SourceRecord]) -> list[SourceRecord]:
    seen: dict[str, SourceRecord] = {}
    for record in records:
        identifiers = record.identifiers or {}
        key = (
            identifiers.get("doi")
            or identifiers.get("arxiv")
            or identifiers.get("openalex")
            or record.url.strip().lower()
        )
        if not key:
            continue
        existing = seen.get(key)
        if existing is None or record.confidence > existing.confidence:
            seen[key] = record
    return list(seen.values())


@tool
def research_search(
    query: str,
    intent: str = "paper",
    limit: int = 10,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Multi-source research search via the SourceAdapter registry.

    Args:
        query: Search query.
        intent: One of paper|code|dataset|news|company|model|benchmark|security|patent|economics|geographic|entity|general.
        limit: Max results per source.
        plan_id: Harness plan id (optional).
        step_id: Harness step id (optional).
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"query": query, "intent": intent, "limit": limit}
    try:
        adapters = route_by_name(intent)
    except Exception:
        adapters = []
    if not adapters:
        try:
            category = SourceCategory(intent.strip().casefold())
            adapters = route_sources(RouteRequest(category=category))
        except (ValueError, KeyError):
            adapters = []
    if not adapters:
        empty = {"query": query, "intent": intent, "results": [], "sources_used": [], "status": "no_adapters"}
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "research_search", "no_adapters", payload)
        return to_tool_result(json.dumps(empty, ensure_ascii=False))
    import asyncio

    async def _gather() -> list[SourceRecord]:
        coros = [adapter.search(query, limit=limit) for adapter in adapters]
        results = await asyncio.gather(*coros, return_exceptions=True)
        merged: list[SourceRecord] = []
        for adapter, result in zip(adapters, results, strict=True):
            if isinstance(result, Exception):
                continue
            merged.extend(result)
        return merged

    try:
        merged = asyncio.run(_gather())
    except Exception as exc:
        if plan_id:
            _emit_record_step(plan_id, "research_search", "error", {**payload, "error": str(exc)})
        return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
    deduped = _dedupe(merged)
    record_dicts = [_record_to_dict(r) for r in deduped[: max(1, limit)]]
    result_payload = {
        "query": query,
        "intent": intent,
        "sources_used": [a.id for a in adapters],
        "results": record_dicts,
        "total": len(record_dicts),
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "research_search", "ok", {**payload, "total": len(record_dicts)})
        _emit_record_step(plan_id, "research_search", "ok", payload)
    return to_tool_result(json.dumps(result_payload, ensure_ascii=False))


@tool
def research_fetch(
    identifier: str,
    source: str = "openalex",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Fetch a single record by identifier from a specific source adapter.

    Args:
        identifier: DOI, arXiv ID, OpenAlex ID, or URL.
        source: Source adapter id (default openalex).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    adapter = get_adapter(source)
    if adapter is None:
        return to_tool_result(json.dumps({"status": "unknown_source", "source": source}, ensure_ascii=False))
    import asyncio

    async def _do() -> SourceRecord | None:
        return await adapter.fetch(identifier)

    try:
        record = asyncio.run(_do())
    except Exception as exc:
        if plan_id:
            _emit_record_step(plan_id, "research_fetch", "error", {"identifier": identifier, "source": source, "error": str(exc)})
        return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
    if record is None:
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "research_fetch", "not_found", {"identifier": identifier, "source": source})
        return to_tool_result(json.dumps({"status": "not_found", "identifier": identifier, "source": source}, ensure_ascii=False))
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "research_fetch", "ok", {"identifier": identifier, "source": source})
        _emit_record_step(plan_id, "research_fetch", "ok", {"identifier": identifier, "source": source})
    return to_tool_result(json.dumps({"status": "ok", "record": _record_to_dict(record)}, ensure_ascii=False))


@tool
def research_compare_sources(
    record_dicts: list[dict[str, Any]],
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Dedup + cross-source confirmation over a list of SourceRecord dicts.

    Args:
        record_dicts: List of record dicts (from research_search output).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    sources_seen: set[str] = set()
    canonical_keys: set[str] = set()
    duplicates: list[dict[str, Any]] = []
    confirmed: list[dict[str, Any]] = []
    for entry in record_dicts:
        if not isinstance(entry, dict):
            continue
        identifiers = entry.get("identifiers") or {}
        key = (
            identifiers.get("doi")
            or identifiers.get("arxiv")
            or identifiers.get("openalex")
            or str(entry.get("url") or "").strip().lower()
        )
        source_name = entry.get("source")
        if source_name:
            sources_seen.add(str(source_name))
        if not key:
            continue
        if key in canonical_keys:
            duplicates.append({"key": key, "title": entry.get("title")})
            continue
        canonical_keys.add(key)
        confirmed.append(entry)
    result = {
        "unique": len(confirmed),
        "duplicates": duplicates,
        "sources_seen": sorted(sources_seen),
        "independent_sources": len(sources_seen),
        "records": confirmed,
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "research_compare_sources", "ok", {"unique": len(confirmed), "sources": len(sources_seen)})
        _emit_record_step(plan_id, "research_compare_sources", "ok", {"input_count": len(record_dicts)})
    return to_tool_result(json.dumps(result, ensure_ascii=False))


@tool
def research_grade_evidence(
    record_dicts: list[dict[str, Any]],
    prefer_open_access: bool = True,
    freshness_days: int = 0,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Assign evidence strength to a list of SourceRecord dicts.

    Args:
        record_dicts: List of record dicts.
        prefer_open_access: Bonus for open licenses.
        freshness_days: Window for recency bonus (0 disables).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    policy = {"prefer_open_access": prefer_open_access, "freshness_days": freshness_days or None}
    graded = []
    counts: dict[str, int] = {"strong": 0, "moderate": 0, "weak": 0, "uncertain": 0}
    for entry in record_dicts:
        if not isinstance(entry, dict):
            continue
        grade, score, reasons = _grade_record(entry, policy)
        counts[grade] += 1
        graded.append({"record": entry, "grade": grade, "score": score, "reasons": reasons})
    summary = {
        "graded": graded,
        "counts": counts,
        "strong_or_moderate": counts["strong"] + counts["moderate"],
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "research_grade_evidence", "ok", {"counts": counts})
        _emit_record_step(plan_id, "research_grade_evidence", "ok", {"graded": len(graded)})
    return to_tool_result(json.dumps(summary, ensure_ascii=False))


research_v2_tools = [
    research_search,
    research_fetch,
    research_compare_sources,
    research_grade_evidence,
]
