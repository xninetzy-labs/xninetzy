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


class PatentsViewAdapter(SourceAdapter):
    id = "patentsview"
    category = SourceCategory.PATENT
    base_url = "https://api.patentsview.org"
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
            logger.warning("patentsview breaker open; skipping search")
            return []
        await self._limiter.acquire()
        body = {
            "q": {"_text_any": {"patent_title": query}},
            "f": ["patent_number", "patent_title", "patent_date", "patent_abstract"],
            "o": {"page": 1, "per_page": max(1, min(limit, 50))},
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/patents/query", body)
        except Exception as exc:
            logger.warning("patentsview search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        patents = payload.get("patents") or []
        if not isinstance(patents, list):
            return records
        for entry in patents:
            try:
                records.append(self._from_patent(entry))
            except Exception as exc:
                logger.warning("patentsview parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        body = {
            "q": {"patent_number": cleaned},
            "f": ["patent_number", "patent_title", "patent_date", "patent_abstract"],
            "o": {"page": 1, "per_page": 1},
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/patents/query", body)
        except Exception as exc:
            logger.warning("patentsview fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        patents = payload.get("patents") or []
        if not patents:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_patent(patents[0])
        except Exception as exc:
            logger.warning("patentsview fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        body = {"q": {"patent_number": "D1000000"}, "f": ["patent_number"], "o": {"per_page": 1}}
        try:
            await self._fetch_json("/patents/query", body)
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_patent(self, entry: dict[str, Any]) -> SourceRecord:
        patent_number = str(entry.get("patent_number") or "").strip()
        title = (entry.get("patent_title") or patent_number or "(untitled)").strip()
        if isinstance(title, list):
            title = title[0] if title else patent_number
        abstract_text = entry.get("patent_abstract") or ""
        if isinstance(abstract_text, list):
            abstract_text = abstract_text[0] if abstract_text else ""
        publication_date = entry.get("patent_date")
        identifiers: dict[str, str] = {"patent_number": patent_number} if patent_number else {}
        url = f"https://patents.uspto.gov/patent/{patent_number}" if patent_number else ""
        return SourceRecord(
            title=str(title)[:300],
            url=url,
            source="patentsview",
            source_type="patent",
            published_at=str(publication_date) if publication_date else None,
            updated_at=str(publication_date) if publication_date else None,
            author=None,
            snippet=str(abstract_text)[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.85 if patent_number else 0.4,
            primary_source=bool(patent_number),
            citation=f"PatentsView:{patent_number}" if patent_number else None,
            identifiers=identifiers,
        )

    async def _fetch_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(PatentsViewAdapter())
