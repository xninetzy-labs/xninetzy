from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.os.research.router import RouteRequest, route_sources
from xninetzy.os.research.sources import SourceCategory, SourceRecord, get_adapter
from xninetzy.tools.tool_results import to_tool_result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _emit_checkpoint(plan_id: str, step_id: str, status: str, payload: dict[str, Any]) -> None:
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('harness_checkpoint', 'info', 'career', ?, ?, ?)
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
            VALUES ('harness_action', 'info', 'career', ?, ?, ?)
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


def _record_to_dict(record: SourceRecord) -> dict[str, Any]:
    return {
        "id": (record.identifiers or {}).get("remoteok_id")
            or (record.identifiers or {}).get("arbeitnow_slug")
            or record.url.rsplit("/", 1)[-1],
        "title": record.title,
        "company": record.author,
        "url": record.url,
        "source": record.source,
        "posted_at": record.published_at,
        "snippet": record.snippet,
        "identifiers": dict(record.identifiers),
    }


def _dedupe_jobs(records: list[SourceRecord]) -> list[SourceRecord]:
    seen: dict[tuple[str, str], SourceRecord] = {}
    for record in records:
        company = (record.author or "").strip().lower()
        title = record.title.strip().lower()
        if not company or not title:
            continue
        key = (company, title[:80])
        if key not in seen:
            seen[key] = record
    return list(seen.values())


def _dedupe_companies(records: list[SourceRecord]) -> list[SourceRecord]:
    seen: dict[str, SourceRecord] = {}
    for record in records:
        company = (record.author or "").strip().lower()
        if not company:
            continue
        if company not in seen:
            seen[company] = record
    return list(seen.values())


_REQUIREMENT_KEYWORDS = (
    "experience",
    "years",
    "knowledge",
    "familiar",
    "proficient",
    "expert",
    "must have",
    "required",
    "requirement",
    "skill",
    "stack",
    "language",
    "framework",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "python",
    "rust",
    "go",
    "typescript",
    "react",
    "vue",
    "angular",
    "node",
    "django",
    "fastapi",
    "flask",
    "postgres",
    "mysql",
    "redis",
    "kafka",
    "llm",
    "rag",
    "pytorch",
    "tensorflow",
    "transformer",
    "sql",
)


def _extract_requirements(snippet: str) -> list[str]:
    if not snippet:
        return []
    lower = snippet.lower()
    found: list[str] = []
    for keyword in _REQUIREMENT_KEYWORDS:
        if keyword in lower:
            found.append(keyword)
    seen: set[str] = set()
    unique: list[str] = []
    for kw in found:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique


@tool
def career_search_jobs(
    query: str,
    country: str = "",
    work_mode: str = "any",
    posted_within_days: int = 0,
    limit: int = 25,
    posting_id: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Search job postings across legal public job-board APIs (RemoteOK, ArbeitNow).

    Args:
        query: Role keywords (e.g. "backend engineer").
        country: ISO country code (optional filter; not enforced by all sources).
        work_mode: remote | hybrid | onsite | any.
        posted_within_days: Recency window in days (0 disables).
        limit: Max postings returned (default 25).
        posting_id: If set, return single posting detail instead of searching.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {
        "query": query,
        "country": country,
        "work_mode": work_mode,
        "posted_within_days": posted_within_days,
        "limit": limit,
        "posting_id": posting_id,
    }
    if posting_id:
        adapter_records: dict[str, SourceRecord | None] = {}
        adapters = route_sources(RouteRequest(category=SourceCategory.COMPANY))

        async def _fetch_all() -> dict[str, SourceRecord | None]:
            coros = {adapter.id: adapter.fetch(posting_id) for adapter in adapters}
            return {k: v for k, v in zip(coros.keys(), await asyncio.gather(*coros.values(), return_exceptions=True))}
        try:
            adapter_records = asyncio.run(_fetch_all())
        except Exception as exc:
            if plan_id:
                _emit_record_step(plan_id, "career_search_jobs", "error", {**payload, "error": str(exc)})
            return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        for source_name, rec in adapter_records.items():
            if rec is not None and not isinstance(rec, Exception):
                if plan_id:
                    _emit_checkpoint(plan_id, step_id or "career_search_jobs", "ok", {"posting_id": posting_id, "source": source_name})
                    _emit_record_step(plan_id, "career_search_jobs", "ok", payload)
                return to_tool_result(json.dumps({
                    "status": "ok",
                    "posting": _record_to_dict(rec),
                    "sources_used": [source_name],
                }, ensure_ascii=False))
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "career_search_jobs", "not_found", payload)
        return to_tool_result(json.dumps({"status": "not_found", "posting_id": posting_id}, ensure_ascii=False))
    adapters = route_sources(RouteRequest(category=SourceCategory.COMPANY))
    if not adapters:
        empty = {"query": query, "results": [], "sources_used": [], "status": "no_adapters"}
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "career_search_jobs", "no_adapters", payload)
        return to_tool_result(json.dumps(empty, ensure_ascii=False))
    effective_query = query
    if posted_within_days:
        effective_query = f"{query} recent"
    if country and country.strip().lower() not in {"", "any"}:
        effective_query = f"{effective_query} {country.strip().lower()}"

    async def _gather() -> list[SourceRecord]:
        coros = [adapter.search(effective_query, limit=max(1, min(limit, 100))) for adapter in adapters]
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
            _emit_record_step(plan_id, "career_search_jobs", "error", {**payload, "error": str(exc)})
        return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
    deduped = _dedupe_jobs(merged)
    record_dicts = [_record_to_dict(r) for r in deduped[: max(1, limit)]]
    result_payload = {
        "query": query,
        "filters": {
            "country": country or None,
            "work_mode": work_mode if work_mode != "any" else None,
            "posted_within_days": posted_within_days or None,
        },
        "results": record_dicts,
        "sources_used": [a.id for a in adapters],
        "total": len(record_dicts),
        "status": "ok",
        "legal_sources_only": True,
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_search_jobs", "ok", {**payload, "total": len(record_dicts)})
        _emit_record_step(plan_id, "career_search_jobs", "ok", payload)
    return to_tool_result(json.dumps(result_payload, ensure_ascii=False))


@tool
def career_search_internships(
    query: str,
    country: str = "",
    work_mode: str = "any",
    limit: int = 25,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Search internship postings across legal public job-board APIs.

    Args:
        query: Role keywords.
        country: ISO country code.
        work_mode: remote | hybrid | onsite | any.
        limit: Max postings returned.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    augmented_query = f"intern OR internship {query}".strip()
    return career_search_jobs.func(
        query=augmented_query,
        country=country,
        work_mode=work_mode,
        posted_within_days=0,
        limit=limit,
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_search_internships",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )


@tool
def career_skill_gap(
    target_role: str,
    profile_skills: list[str],
    limit: int = 25,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Compute skill gap: owner profile vs market top skills for a target role.

    Args:
        target_role: Target role title.
        profile_skills: Owner's known skills.
        limit: Max postings sampled.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"target_role": target_role, "profile_skills": profile_skills}
    raw = career_search_jobs.func(
        query=target_role,
        country="",
        work_mode="any",
        posted_within_days=0,
        limit=limit,
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_skill_gap",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    postings = parsed.get("results") or []
    counter: dict[str, int] = {}
    for p in postings:
        ids = (p.get("identifiers") or {})
        tags_value = ids.get("tags") or ""
        for tag in tags_value.split(","):
            tag = tag.strip().lower()
            if not tag:
                continue
            counter[tag] = counter.get(tag, 0) + 1
    sorted_skills = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)
    owner_set = {s.strip().lower() for s in profile_skills if isinstance(s, str)}
    top_skills = [name for name, _ in sorted_skills[:30]]
    has = sorted([s for s in top_skills if s in owner_set])
    missing = sorted([s for s in top_skills if s not in owner_set])
    total = sum(counter.values()) or 1
    out = {
        "target_role": target_role,
        "postings_analyzed": len(postings),
        "market_top_skills": [
            {"skill": name, "frequency_pct": round((count / total) * 100, 2)}
            for name, count in sorted_skills[:20]
        ],
        "owner_has": has,
        "owner_missing": missing,
        "caveat": "Skill extraction derived from posting tags; may include noise. LLM refinement recommended.",
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_skill_gap", "ok", {**payload, "postings": len(postings)})
        _emit_record_step(plan_id, "career_skill_gap", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_market_skill_trend(
    role: str,
    country: str = "",
    posted_within_days: int = 60,
    limit: int = 50,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Aggregate skill frequency for a target role from legal public postings.

    Args:
        role: Target role title.
        country: ISO country code.
        posted_within_days: Recency window.
        limit: Max postings sampled.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    return career_skill_gap.func(
        target_role=role,
        profile_skills=[],
        limit=limit,
        plan_id=plan_id,
        step_id=step_id or "career_market_skill_trend",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )


@tool
def career_resume_tailor(
    posting_id: str,
    cv_text: str,
    tone: str = "balanced",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Suggest a CV diff for a target posting. Returns a structured diff, never overwrites CV.

    Args:
        posting_id: Posting identifier.
        cv_text: Owner's CV plain text.
        tone: conservative | balanced | bold.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"posting_id": posting_id, "tone": tone, "cv_chars": len(cv_text)}
    raw = career_search_jobs.func(
        query="",
        country="",
        work_mode="any",
        posted_within_days=0,
        limit=1,
        posting_id=posting_id,
        plan_id=plan_id,
        step_id=step_id or "career_resume_tailor",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    posting = parsed.get("posting") or {}
    out = {
        "posting_id": posting_id,
        "tone": tone,
        "posting": posting,
        "cv_chars": len(cv_text),
        "apply_path": "obsidian_save_note | manual_edit",
        "changes": [],
        "rationale": "Refinement requires LLM-side analysis; this stub surfaces inputs for downstream summarization.",
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_resume_tailor", "ok", payload)
        _emit_record_step(plan_id, "career_resume_tailor", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_search_companies(
    query: str,
    limit: int = 25,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Search companies hiring across legal public job-board APIs.

    Args:
        query: Company name or industry keyword.
        limit: Max companies returned.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"query": query, "limit": limit}
    adapters = route_sources(RouteRequest(category=SourceCategory.COMPANY))
    if not adapters:
        empty = {"query": query, "results": [], "sources_used": [], "status": "no_adapters"}
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "career_search_companies", "no_adapters", payload)
        return to_tool_result(json.dumps(empty, ensure_ascii=False))

    async def _gather() -> list[SourceRecord]:
        coros = [adapter.search(query, limit=max(1, min(limit, 100))) for adapter in adapters]
        results = await asyncio.gather(*coros, return_exceptions=True)
        merged: list[SourceRecord] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            merged.extend(result)
        return merged

    try:
        merged = asyncio.run(_gather())
    except Exception as exc:
        if plan_id:
            _emit_record_step(plan_id, "career_search_companies", "error", {**payload, "error": str(exc)})
        return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
    deduped = _dedupe_companies(merged)
    record_dicts = [
        {
            "company": r.author,
            "source": r.source,
            "open_postings": 0,
            "snippet": r.snippet[:200] if r.snippet else "",
            "url": r.url,
        }
        for r in deduped[: max(1, limit)]
    ]
    counter: dict[str, int] = {}
    for r in merged:
        company = (r.author or "").strip()
        if company:
            counter[company] = counter.get(company, 0) + 1
    for entry in record_dicts:
        entry["open_postings"] = counter.get(entry["company"], 0)
    result_payload = {
        "query": query,
        "results": record_dicts,
        "sources_used": [a.id for a in adapters],
        "total": len(record_dicts),
        "status": "ok",
        "legal_sources_only": True,
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_search_companies", "ok", {**payload, "total": len(record_dicts)})
        _emit_record_step(plan_id, "career_search_companies", "ok", payload)
    return to_tool_result(json.dumps(result_payload, ensure_ascii=False))


@tool
def career_get_job(
    posting_id: str,
    source: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Fetch a single job posting by id. Tries every legal job-board source unless source specified.

    Args:
        posting_id: Posting identifier (RemoteOK id, ArbeitNow slug, or URL).
        source: Optional adapter id to constrain the lookup (remoteok|arbeitnow).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"posting_id": posting_id, "source": source}
    if source:
        adapter = get_adapter(source)
        if adapter is None:
            return to_tool_result(json.dumps({"status": "unknown_source", "source": source}, ensure_ascii=False))
        adapters = [adapter]
    else:
        adapters = route_sources(RouteRequest(category=SourceCategory.COMPANY))

    async def _gather() -> dict[str, SourceRecord | None]:
        coros = {adapter.id: adapter.fetch(posting_id) for adapter in adapters}
        return {k: v for k, v in zip(coros.keys(), await asyncio.gather(*coros.values(), return_exceptions=True))}

    try:
        adapter_records = asyncio.run(_gather())
    except Exception as exc:
        if plan_id:
            _emit_record_step(plan_id, "career_get_job", "error", {**payload, "error": str(exc)})
        return to_tool_result(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
    for source_name, rec in adapter_records.items():
        if rec is not None and not isinstance(rec, Exception):
            posting = _record_to_dict(rec)
            posting["requirements"] = _extract_requirements(rec.snippet or "")
            if plan_id:
                _emit_checkpoint(plan_id, step_id or "career_get_job", "ok", {**payload, "source": source_name})
                _emit_record_step(plan_id, "career_get_job", "ok", payload)
            return to_tool_result(json.dumps({
                "status": "ok",
                "posting": posting,
                "source": source_name,
            }, ensure_ascii=False))
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_get_job", "not_found", payload)
    return to_tool_result(json.dumps({"status": "not_found", "posting_id": posting_id}, ensure_ascii=False))


@tool
def career_extract_requirements(
    posting_id: str,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Extract structured requirements (skills, experience, stack) from a posting.

    Args:
        posting_id: Posting identifier.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"posting_id": posting_id}
    raw = career_get_job.func(
        posting_id=posting_id,
        source="",
        plan_id=plan_id,
        step_id=step_id or "career_extract_requirements",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    posting = parsed.get("posting") or {}
    snippet = posting.get("snippet") or ""
    requirements = _extract_requirements(snippet)
    out = {
        "posting_id": posting_id,
        "requirements": requirements,
        "snippet_chars": len(snippet),
        "caveat": "Keyword extraction is heuristic; LLM refinement recommended for nuance.",
        "status": "ok" if posting else "not_found",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_extract_requirements", out["status"], {**payload, "req_count": len(requirements)})
        _emit_record_step(plan_id, "career_extract_requirements", out["status"], payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


_ALTERNATIVE_TITLE_MAP: dict[str, tuple[str, ...]] = {
    "backend": ("backend engineer", "server engineer", "API engineer", "platform engineer"),
    "frontend": ("frontend engineer", "UI engineer", "web engineer", "client engineer"),
    "fullstack": ("full-stack engineer", "full stack developer", "web developer"),
    "data scientist": ("ML engineer", "applied scientist", "data scientist", "research engineer"),
    "data engineer": ("data engineer", "analytics engineer", "ETL engineer", "data platform engineer"),
    "devops": ("DevOps engineer", "SRE", "platform engineer", "infrastructure engineer"),
    "mobile": ("iOS engineer", "Android engineer", "mobile developer", "React Native engineer"),
    "ai": ("AI engineer", "ML engineer", "applied scientist", "research engineer"),
    "security": ("security engineer", "infosec engineer", "AppSec engineer", "cybersecurity analyst"),
    "qa": ("QA engineer", "test engineer", "SDET", "quality engineer"),
}


def _expand_title(query: str) -> list[str]:
    q = (query or "").strip().lower()
    expansions: list[str] = [q] if q else []
    for key, variants in _ALTERNATIVE_TITLE_MAP.items():
        if key in q or q in key:
            expansions.extend(variants)
    if q:
        expansions.extend([f"{q} junior", f"{q} mid", f"{q} senior", f"{q} intern"])
    seen: set[str] = set()
    unique: list[str] = []
    for term in expansions:
        cleaned = term.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


_SALARY_RE = None


def _salary_re():
    global _SALARY_RE
    if _SALARY_RE is None:
        import re

        _SALARY_RE = re.compile(
            r"(?P<currency>usd|eur|gbp|sgd|idr|aud|inr|jpy|cny|brl|myr|thb|php|krw)\s*"
            r"(?P<amount>\d{1,3}(?:[,.]\d{3})*|\d+k?)\s*"
            r"(?:k|\s*000)?",
            re.IGNORECASE,
        )
    return _SALARY_RE


_CURRENCY_TO_USD = {
    "usd": 1.0,
    "eur": 1.08,
    "gbp": 1.27,
    "sgd": 0.74,
    "idr": 0.000063,
    "aud": 0.66,
    "inr": 0.012,
    "jpy": 0.0066,
    "cny": 0.14,
    "brl": 0.20,
    "myr": 0.22,
    "thb": 0.028,
    "php": 0.018,
    "krw": 0.00074,
}


def _parse_salary(text: str) -> tuple[str, float, int] | None:
    if not text:
        return None
    match = _salary_re().search(text)
    if not match:
        return None
    currency = match.group("currency").lower()
    raw = match.group("amount").replace(",", "").replace(".", "")
    suffix = match.group(0).lower()
    try:
        amount = int(raw)
    except (TypeError, ValueError):
        return None
    if "k" in suffix or "000" in suffix:
        amount = amount * (1000 if "k" in suffix and amount < 1000 else 1)
    rate = _CURRENCY_TO_USD.get(currency, 0.0)
    if rate == 0.0:
        return None
    return currency, rate, amount


@tool
def career_company_research(
    company_name: str,
    limit: int = 25,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Aggregate company info from legal sources: hiring signal + snippets + URLs.

    Args:
        company_name: Company name.
        limit: Max postings to inspect.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"company_name": company_name, "limit": limit}
    raw = career_search_jobs.func(
        query=company_name,
        country="",
        work_mode="any",
        posted_within_days=0,
        limit=limit,
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_company_research",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    postings = parsed.get("results") or []
    matched = [
        p for p in postings
        if isinstance(p.get("company"), str)
        and p.get("company", "").strip().lower() == company_name.strip().lower()
    ]
    titles = sorted({p.get("title") for p in matched if p.get("title")})
    out = {
        "company_name": company_name,
        "open_postings_found": len(matched),
        "open_titles_sample": titles[:10],
        "sources_used": parsed.get("sources_used", []),
        "status": "ok",
        "caveat": "Funding/team-size not in scope of job-board APIs. Use research_search for Wikipedia/OpenAlex context.",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_company_research", "ok", {**payload, "matched": len(matched)})
        _emit_record_step(plan_id, "career_company_research", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_salary_analysis(
    role: str,
    country: str = "",
    posted_within_days: int = 60,
    limit: int = 50,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Extract disclosed salary signals from postings for a target role.

    Args:
        role: Target role title.
        country: ISO country code (optional).
        posted_within_days: Recency window.
        limit: Max postings sampled.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"role": role, "country": country, "limit": limit}
    raw = career_search_jobs.func(
        query=role,
        country=country,
        work_mode="any",
        posted_within_days=posted_within_days,
        limit=limit,
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_salary_analysis",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    postings = parsed.get("results") or []
    amounts_usd: list[int] = []
    samples: list[dict[str, Any]] = []
    for posting in postings:
        snippet = posting.get("snippet") or ""
        parsed_salary = _parse_salary(snippet)
        if parsed_salary is None:
            continue
        currency, rate, amount = parsed_salary
        usd = int(amount * rate)
        amounts_usd.append(usd)
        samples.append({"currency": currency, "amount": amount, "usd": usd, "title": posting.get("title")})
    sample_size = len(postings)
    with_pay = len(amounts_usd)
    if amounts_usd:
        sorted_amounts = sorted(amounts_usd)
        median = sorted_amounts[len(sorted_amounts) // 2]
        p25 = sorted_amounts[max(0, len(sorted_amounts) // 4)]
        p75 = sorted_amounts[min(len(sorted_amounts) - 1, (3 * len(sorted_amounts)) // 4)]
    else:
        median = p25 = p75 = 0
    out = {
        "target_role": role,
        "sample_size": sample_size,
        "postings_with_pay": with_pay,
        "median_usd": median,
        "range_p25_usd": p25,
        "range_p75_usd": p75,
        "samples": samples[:5],
        "caveat": "Salary data only from postings that disclose pay; sample may be biased toward transparent employers.",
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_salary_analysis", "ok", {**payload, "with_pay": with_pay})
        _emit_record_step(plan_id, "career_salary_analysis", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_find_similar_jobs(
    posting_id: str,
    limit: int = 15,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Find postings similar to a seed posting (same company, role keywords, or tags).

    Args:
        posting_id: Seed posting identifier.
        limit: Max similar postings returned.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"posting_id": posting_id, "limit": limit}
    raw = career_get_job.func(
        posting_id=posting_id,
        source="",
        plan_id=plan_id,
        step_id=step_id or "career_find_similar_jobs",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    seed = parsed.get("posting") or {}
    seed_company = (seed.get("company") or "").strip()
    seed_title = (seed.get("title") or "").strip()
    if not seed_title and not seed_company:
        out = {"status": "not_found", "posting_id": posting_id, "results": []}
        if plan_id:
            _emit_checkpoint(plan_id, step_id or "career_find_similar_jobs", "not_found", payload)
        return to_tool_result(json.dumps(out, ensure_ascii=False))
    raw_search = career_search_jobs.func(
        query=seed_title,
        country="",
        work_mode="any",
        posted_within_days=0,
        limit=max(1, limit * 2),
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_find_similar_jobs.search",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        search_parsed = json.loads(raw_search)
    except (TypeError, ValueError):
        search_parsed = {}
    candidates = search_parsed.get("results") or []
    seen: list[dict[str, Any]] = []
    seed_id = seed.get("id") or posting_id
    for candidate in candidates:
        if candidate.get("id") == seed_id:
            continue
        if seed_company and candidate.get("company") == seed_company:
            seen.append({"posting": candidate, "reason": "same_company"})
            continue
        if seed_title and candidate.get("title"):
            a = seed_title.lower()
            b = candidate["title"].lower()
            if any(token in b for token in a.split() if len(token) > 3):
                seen.append({"posting": candidate, "reason": "similar_title"})
        if len(seen) >= limit:
            break
    out = {
        "seed_posting_id": posting_id,
        "results": seen[:limit],
        "total": len(seen),
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_find_similar_jobs", "ok", {**payload, "total": len(seen)})
        _emit_record_step(plan_id, "career_find_similar_jobs", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_find_alternative_titles(
    query: str,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Expand a role title to synonyms + seniority variants. LLM can refine further.

    Args:
        query: Original role title.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"query": query}
    expansions = _expand_title(query)
    out = {
        "query": query,
        "alternative_titles": expansions,
        "caveat": "Heuristic synonym map; LLM refinement recommended for novel roles.",
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_find_alternative_titles", "ok", {**payload, "count": len(expansions)})
        _emit_record_step(plan_id, "career_find_alternative_titles", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


_MAINSTREAM_BOARDS = {"linkedin", "indeed", "glassdoor", "jobstreet", "glints"}


@tool
def career_find_hidden_jobs(
    role: str,
    country: str = "",
    limit: int = 25,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Surface postings from long-tail / non-mainstream boards only.

    Args:
        role: Role keywords.
        country: ISO country code.
        limit: Max postings returned.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    payload = {"role": role, "country": country, "limit": limit}
    raw = career_search_jobs.func(
        query=role,
        country=country,
        work_mode="any",
        posted_within_days=0,
        limit=max(1, limit * 2),
        posting_id="",
        plan_id=plan_id,
        step_id=step_id or "career_find_hidden_jobs",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    candidates = parsed.get("results") or []
    filtered: list[dict[str, Any]] = []
    for posting in candidates:
        source = (posting.get("source") or "").strip().lower()
        if source and source in _MAINSTREAM_BOARDS:
            continue
        filtered.append(posting)
        if len(filtered) >= limit:
            break
    out = {
        "role": role,
        "results": filtered,
        "total": len(filtered),
        "mainstream_filter": sorted(_MAINSTREAM_BOARDS),
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_find_hidden_jobs", "ok", {**payload, "total": len(filtered)})
        _emit_record_step(plan_id, "career_find_hidden_jobs", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_monitor(
    query: str,
    country: str = "",
    work_mode: str = "any",
    interval_minutes: int = 240,
    sender_id: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Register a periodic job-posting watch. Always owner-scoped. Returns subscription receipt.

    Args:
        query: Role keywords.
        country: ISO country code.
        work_mode: remote | hybrid | onsite | any.
        interval_minutes: Cadence in minutes (min 60).
        sender_id: Owner principal.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        idempotency_key: Optional idempotency key.
    """
    payload = {
        "query": query,
        "country": country,
        "work_mode": work_mode,
        "interval_minutes": interval_minutes,
        "sender_id": sender_id,
    }
    if interval_minutes < 60:
        interval_minutes = 60
    subscription_id = "career-monitor-" + uuid.uuid4().hex[:12]
    out = {
        "id": subscription_id,
        "query": query,
        "filters": {
            "country": country or None,
            "work_mode": work_mode if work_mode != "any" else None,
            "interval_minutes": interval_minutes,
        },
        "owner": sender_id or None,
        "handler": "career_search_jobs",
        "status": "registered",
        "caveat": "Handler invocation is owner-controlled; do not register monitors on behalf of others.",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_monitor", "ok", {**payload, "id": subscription_id})
        _emit_record_step(plan_id, "career_monitor", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_track_application(
    posting_id: str,
    status: str,
    notes: str = "",
    sender_id: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Persist an application-status update into owner-scoped memory.

    Args:
        posting_id: Posting identifier.
        status: drafted | applied | phone_screen | interviewed | offer | rejected | withdrawn.
        notes: Free-text notes.
        sender_id: Owner principal.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        idempotency_key: Optional idempotency key.
    """
    payload = {
        "posting_id": posting_id,
        "status": status,
        "sender_id": sender_id,
        "notes_chars": len(notes),
    }
    valid = {"drafted", "applied", "phone_screen", "interviewed", "offer", "rejected", "withdrawn"}
    if status not in valid:
        return to_tool_result(json.dumps({
            "status": "error",
            "error": f"invalid status; expected one of {sorted(valid)}",
        }, ensure_ascii=False))
    record_value = {
        "posting_id": posting_id,
        "status": status,
        "notes": notes,
        "updated_at": _now_iso(),
    }
    out = {
        "posting_id": posting_id,
        "status": status,
        "recorded_at": record_value["updated_at"],
        "scope": "career_applications",
        "owner": sender_id or None,
        "retrieve_via": "memory_search(scope='career_applications')",
        "status_flag": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_track_application", "ok", payload)
        _emit_record_step(plan_id, "career_track_application", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_interview_prep(
    posting_id: str,
    sender_id: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Produce an interview-prep pack: posting summary + likely questions + refreshers.

    Args:
        posting_id: Posting identifier.
        sender_id: Owner principal.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        idempotency_key: Optional idempotency key.
    """
    payload = {"posting_id": posting_id, "sender_id": sender_id}
    raw = career_get_job.func(
        posting_id=posting_id,
        source="",
        plan_id=plan_id,
        step_id=step_id or "career_interview_prep",
        chat_id=chat_id,
        sender_id=sender_id,
        idempotency_key=idempotency_key,
    )
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        parsed = {}
    posting = parsed.get("posting") or {}
    requirements = posting.get("requirements") or []
    out = {
        "posting_id": posting_id,
        "posting_summary": {
            "title": posting.get("title"),
            "company": posting.get("company"),
            "url": posting.get("url"),
            "requirements": requirements,
        },
        "likely_questions": [
            {"question": f"Walk me through a project where you used {req}.", "rationale": "Direct skill probe from requirements."}
            for req in requirements[:5]
        ],
        "technical_refreshers": [
            {"topic": "system-design", "sources": ["skill: deep-research", "skill: literature-review"]},
            {"topic": "language-fundamentals", "sources": ["skill: research-paper-search"]},
        ],
        "status": "ok" if posting else "not_found",
        "caveat": "Question list is heuristic; refine against JD + owner profile via LLM.",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_interview_prep", out["status"], payload)
        _emit_record_step(plan_id, "career_interview_prep", out["status"], payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


@tool
def career_resume_analysis(
    cv_text: str,
    target_role: str = "",
    sender_id: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Analyze a CV text. Returns skill extraction + role-fit signals.

    Args:
        cv_text: Owner's CV plain text.
        target_role: Optional role to compare against.
        sender_id: Owner principal.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        idempotency_key: Optional idempotency key.
    """
    payload = {"cv_chars": len(cv_text), "target_role": target_role, "sender_id": sender_id}
    keywords = ("python", "rust", "go", "typescript", "javascript", "java", "kotlin", "swift",
                "react", "vue", "angular", "node", "django", "fastapi", "flask", "postgres",
                "mysql", "redis", "kafka", "docker", "kubernetes", "aws", "gcp", "azure",
                "llm", "rag", "pytorch", "tensorflow", "transformer", "sql", "spark")
    lower = (cv_text or "").lower()
    skills = sorted({kw for kw in keywords if kw in lower})
    target_keywords: list[str] = []
    target_match: list[str] = []
    if target_role:
        target_lower = target_role.lower()
        for kw in keywords:
            if kw in target_lower:
                target_keywords.append(kw)
        target_match = [kw for kw in target_keywords if kw in skills]
    out = {
        "skills": skills,
        "target_role": target_role or None,
        "target_keywords": target_keywords,
        "target_match": target_match,
        "cv_chars": len(cv_text),
        "caveat": "Keyword extraction is heuristic. LLM-side refinement recommended for nuance.",
        "status": "ok",
    }
    if plan_id:
        _emit_checkpoint(plan_id, step_id or "career_resume_analysis", "ok", {**payload, "skills": len(skills)})
        _emit_record_step(plan_id, "career_resume_analysis", "ok", payload)
    return to_tool_result(json.dumps(out, ensure_ascii=False))


career_tools = [
    career_search_jobs,
    career_search_internships,
    career_skill_gap,
    career_market_skill_trend,
    career_resume_tailor,
    career_search_companies,
    career_get_job,
    career_extract_requirements,
    career_company_research,
    career_salary_analysis,
    career_find_similar_jobs,
    career_find_alternative_titles,
    career_find_hidden_jobs,
    career_monitor,
    career_track_application,
    career_interview_prep,
    career_resume_analysis,
]
