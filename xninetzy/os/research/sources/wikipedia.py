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


class WikipediaAdapter(SourceAdapter):
    id = "wikipedia"
    category = SourceCategory.ENTITY
    base_url = "https://en.wikipedia.org/api/rest_v1"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=60, burst=5)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("wikipedia breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/", params)
        except Exception as exc:
            logger.warning("wikipedia search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        hits = ((payload.get("query") or {}).get("search") or [])
        records: list[SourceRecord] = []
        for hit in hits:
            try:
                records.append(self._from_hit(hit))
            except Exception as exc:
                logger.warning("wikipedia parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if cleaned.startswith("https://"):
            parts = cleaned.split("/wiki/", 1)
            if len(parts) == 2:
                cleaned = parts[1].split("#")[0]
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "action": "query",
            "titles": cleaned,
            "format": "json",
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/", params)
        except Exception as exc:
            logger.warning("wikipedia fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        pages = (payload.get("query") or {}).get("pages") or {}
        page = next(iter(pages.values()), None) if isinstance(pages, dict) else None
        if not isinstance(page, dict):
            return None
        try:
            return self._from_page(page)
        except Exception as exc:
            logger.warning("wikipedia fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/",
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": "test",
                    "format": "json",
                    "srlimit": 1,
                },
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_hit(self, hit: dict[str, Any]) -> SourceRecord:
        title = (hit.get("title") or "").strip() or "(untitled)"
        page_id = str(hit.get("pageid") or "")
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        snippet = (hit.get("snippet") or "")[:600]
        snippet = snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        identifiers: dict[str, str] = {}
        if page_id:
            identifiers["wiki_pageid"] = page_id
        return SourceRecord(
            title=title[:300],
            url=url,
            source="wikipedia",
            source_type="entity",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=snippet,
            content=None,
            language="en",
            license="CC BY-SA",
            retrieved_at=make_retrieved_at(),
            confidence=0.8 if page_id else 0.4,
            primary_source=bool(page_id),
            citation=f"Wikipedia:{title}",
            identifiers=identifiers,
        )

    def _from_page(self, page: dict[str, Any]) -> SourceRecord:
        title = (page.get("title") or "").strip() or "(untitled)"
        page_id = str(page.get("pageid") or "")
        fullurl = (page.get("fullurl") or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
        extract = (page.get("extract") or "")[:600]
        identifiers: dict[str, str] = {}
        if page_id:
            identifiers["wiki_pageid"] = page_id
        return SourceRecord(
            title=title[:300],
            url=fullurl,
            source="wikipedia",
            source_type="entity",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=extract,
            content=None,
            language="en",
            license="CC BY-SA",
            retrieved_at=make_retrieved_at(),
            confidence=0.9 if page_id else 0.4,
            primary_source=bool(page_id),
            citation=f"Wikipedia:{title}",
            identifiers=identifiers,
        )

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


register_adapter(WikipediaAdapter())
