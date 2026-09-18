from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

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


def _from_search_hit(hit: dict[str, Any]) -> SourceRecord:
    label = (hit.get("label") or hit.get("id") or "(unknown)").strip()
    description = (hit.get("description") or "").strip()
    qid = str(hit.get("id") or "").strip()
    url = f"https://www.wikidata.org/wiki/{qid}" if qid else "https://www.wikidata.org/"
    return SourceRecord(
        title=label,
        url=url,
        source="wikidata",
        source_type="entity",
        published_at=None,
        updated_at=None,
        author=None,
        snippet=description[:600],
        content=None,
        language="en",
        license="CC0",
        retrieved_at=make_retrieved_at(),
        confidence=0.7 if qid else 0.3,
        primary_source=bool(qid),
        citation=f"Wikidata:{qid} - {label}" if qid else None,
        identifiers={"qid": qid} if qid else {},
    )


class WikidataAdapter(SourceAdapter):
    id = "wikidata"
    category = SourceCategory.ENTITY
    base_url = "https://www.wikidata.org/w/api.php"
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
            logger.warning("wikidata breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "limit": max(1, min(limit, 50)),
            "format": "json",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, params=params)
        except Exception as exc:
            logger.warning("wikidata search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        hits = payload.get("search") or []
        records: list[SourceRecord] = []
        for hit in hits:
            try:
                records.append(_from_search_hit(hit))
            except Exception as exc:
                logger.warning("wikidata parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("https://www.wikidata.org/wiki/"):
            cleaned = cleaned.rsplit("/", 1)[-1]
        if not (cleaned.startswith("Q") and cleaned[1:].isdigit()):
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "action": "wbgetentities",
            "ids": cleaned,
            "languages": "en",
            "props": "labels|descriptions",
            "format": "json",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, params=params)
        except Exception as exc:
            logger.warning("wikidata fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        await self._breaker.record_success()
        entity = (payload.get("entities") or {}).get(cleaned) or {}
        labels = entity.get("labels") or {}
        descriptions = entity.get("descriptions") or {}
        label_obj = labels.get("en") or {}
        description_obj = descriptions.get("en") or {}
        return SourceRecord(
            title=str(label_obj.get("value") or cleaned),
            url=f"https://www.wikidata.org/wiki/{cleaned}",
            source="wikidata",
            source_type="entity",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=str(description_obj.get("value") or "")[:600],
            content=None,
            language="en",
            license="CC0",
            retrieved_at=make_retrieved_at(),
            confidence=0.85,
            primary_source=True,
            citation=f"Wikidata:{cleaned}",
            identifiers={"qid": cleaned},
        )

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(params={"action": "wbsearchentities", "search": "test", "language": "en", "limit": 1, "format": "json"})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        import httpx

        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(self.base_url, params=params)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(WikidataAdapter())
