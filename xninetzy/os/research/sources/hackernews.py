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


def _from_hit(hit: dict[str, Any]) -> SourceRecord:
    title = (hit.get("title") or hit.get("story_title") or "(untitled)").strip()
    url = hit.get("url") or hit.get("story_url") or ""
    object_id = str(hit.get("objectID") or "")
    author = hit.get("author") or None
    created_at = hit.get("created_at")
    points = hit.get("points") or 0
    num_comments = hit.get("num_comments") or 0
    snippet_parts = [
        f"{points} points" if points else "",
        f"{num_comments} comments" if num_comments else "",
    ]
    snippet = " | ".join([p for p in snippet_parts if p]) or (hit.get("_tags") or "")
    identifiers: dict[str, str] = {}
    if object_id:
        identifiers["hn"] = object_id
    return SourceRecord(
        title=title,
        url=url or f"https://news.ycombinator.com/item?id={object_id}",
        source="hackernews",
        source_type="news",
        published_at=created_at,
        updated_at=created_at,
        author=author,
        snippet=snippet[:600],
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.6 + min(0.3, points * 0.001),
        primary_source=bool(url),
        citation=f"HN:{object_id} - {title}" if object_id else None,
        identifiers=identifiers,
    )


class HackerNewsAdapter(SourceAdapter):
    id = "hackernews"
    category = SourceCategory.NEWS
    base_url = "https://hn.algolia.com/api/v1"
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
            logger.warning("hackernews breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "query": query,
            "hitsPerPage": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search", params)
        except Exception as exc:
            logger.warning("hackernews search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for hit in payload.get("hits") or []:
            try:
                records.append(_from_hit(hit))
            except Exception as exc:
                logger.warning("hackernews parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("https://"):
            if "item?id=" in cleaned:
                cleaned = cleaned.split("item?id=", 1)[1].split("&")[0].split("#")[0]
            else:
                cleaned = cleaned.rsplit("/", 1)[-1]
        if not cleaned.isdigit():
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(self.retry, self._fetch_json, f"/items/{cleaned}", None)
        except Exception as exc:
            logger.warning("hackernews fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload or payload.get("id") is None:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_hit({
                "objectID": str(payload.get("id")),
                "title": payload.get("title"),
                "url": payload.get("url"),
                "author": payload.get("author"),
                "created_at": payload.get("created_at"),
                "points": payload.get("points"),
                "num_comments": payload.get("num_comments"),
            })
        except Exception as exc:
            logger.warning("hackernews fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/search", {"query": "test", "hitsPerPage": 1})
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


register_adapter(HackerNewsAdapter())
