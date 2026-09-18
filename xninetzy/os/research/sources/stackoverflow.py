from __future__ import annotations

import json
from typing import Any

from xninetzy.core.logging import logging
from xninetzy.os.research.sources.base import (
    CircuitBreaker,
    HealthStatus,
    RateLimit,
    RetryPolicy,
    SourceAdapter,
    SourceCategory,
    SourceRecord,
    make_retrieved_at,
)
from xninetzy.os.research.sources.rate_limit import (
    CircuitBreakerGuard,
    RateLimiter,
    retry_async,
)
from xninetzy.os.research.sources.registry import (
    build_breaker,
    build_rate_limiter,
    register_adapter,
)

logger = logging.getLogger(__name__)


def _from_question(q: dict[str, Any]) -> SourceRecord:
    question_id = str(q.get("question_id") or "")
    title = (q.get("title") or "").strip() or "(untitled)"
    link = q.get("link") or (f"https://stackoverflow.com/questions/{question_id}" if question_id else "")
    tags = q.get("tags") or []
    score = q.get("score") or 0
    is_answered = bool(q.get("is_answered"))
    view_count = q.get("view_count") or 0
    creation_date = q.get("creation_date")
    owner = (q.get("owner") or {}).get("display_name") if isinstance(q.get("owner"), dict) else None
    snippet = (q.get("excerpt") or "")[:600] if q.get("excerpt") else " ".join(tags)
    identifiers: dict[str, str] = {}
    if question_id:
        identifiers["so"] = question_id
    if tags:
        identifiers["tags"] = ",".join(tags[:5])
    return SourceRecord(
        title=title,
        url=link,
        source="stackoverflow",
        source_type="general",
        published_at=str(creation_date) if creation_date else None,
        updated_at=str(creation_date) if creation_date else None,
        author=owner,
        snippet=snippet,
        content=None,
        language="en",
        license="CC BY-SA",
        retrieved_at=make_retrieved_at(),
        confidence=0.6 + min(0.3, score * 0.001) + (0.1 if is_answered else 0.0),
        primary_source=bool(question_id),
        citation=f"SO:{question_id} - {title}" if question_id else None,
        identifiers=identifiers,
    )


class StackOverflowAdapter(SourceAdapter):
    id = "stackoverflow"
    category = SourceCategory.GENERAL
    base_url = "https://api.stackexchange.com/2.3"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("stackoverflow breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "order": "desc",
            "sort": "relevance",
            "intitle": query,
            "site": "stackoverflow",
            "pagesize": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search", params)
        except Exception as exc:
            logger.warning("stackoverflow search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for q in payload.get("items") or []:
            try:
                records.append(_from_question(q))
            except Exception as exc:
                logger.warning("stackoverflow parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("https://stackoverflow.com/questions/"):
            parts = cleaned.split("/questions/", 1)[1].split("/")
            cleaned = parts[0]
        if not cleaned.isdigit():
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params = {"site": "stackoverflow", "filter": "withbody"}
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, f"/questions/{cleaned}", params
            )
        except Exception as exc:
            logger.warning("stackoverflow fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        items = payload.get("items") or []
        if not items:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_question(items[0])
        except Exception as exc:
            logger.warning("stackoverflow fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/info", {"site": "stackoverflow"})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self, path: str, params: dict[str, Any] | None
    ) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(StackOverflowAdapter())
