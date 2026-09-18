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


class PapersWithCodeAdapter(SourceAdapter):
    id = "papers_with_code"
    category = SourceCategory.BENCHMARK
    base_url = "https://paperswithcode.com/api/v1"
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
            logger.warning("papers_with_code breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "items_per_page": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/datasets/", params)
        except Exception as exc:
            logger.warning("papers_with_code datasets search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        results = payload.get("results") or []
        for entry in results:
            try:
                records.append(self._from_dataset(entry))
            except Exception as exc:
                logger.warning("papers_with_code parse failed: %s", exc)
        if not records:
            try:
                params["q"] = query
                payload = await retry_async(
                    self.retry, self._fetch_json, "/benchmarks/", params
                )
                for entry in (payload.get("results") or []):
                    try:
                        records.append(self._from_benchmark(entry))
                    except Exception as exc:
                        logger.warning("papers_with_code benchmark parse failed: %s", exc)
            except Exception as exc:
                logger.info("papers_with_code benchmarks search failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        if cleaned.startswith("pwc:"):
            slug = cleaned.split(":", 1)[1]
            path = f"/datasets/{slug}"
        elif cleaned.startswith("benchmark:"):
            slug = cleaned.split(":", 1)[1]
            path = f"/benchmarks/{slug}"
        else:
            path = f"/datasets/{cleaned}"
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, None)
        except Exception as exc:
            logger.warning("papers_with_code fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            if "/benchmarks/" in path:
                return self._from_benchmark(payload)
            return self._from_dataset(payload)
        except Exception as exc:
            logger.warning("papers_with_code fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/datasets/", {"q": "test", "items_per_page": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_dataset(self, entry: dict[str, Any]) -> SourceRecord:
        name = (entry.get("name") or "").strip() or "(unnamed dataset)"
        slug = entry.get("slug") or ""
        description = (entry.get("description") or "").strip()
        url = entry.get("url") or (f"https://paperswithcode.com/dataset/{slug}" if slug else "")
        modalities = entry.get("modalities") or []
        languages = entry.get("languages") or []
        tasks = entry.get("tasks") or []
        snippet_parts: list[str] = []
        if modalities:
            snippet_parts.append(f"modalities={','.join(modalities[:3])}")
        if languages:
            snippet_parts.append(f"languages={','.join(languages[:3])}")
        if tasks:
            snippet_parts.append(f"tasks={','.join([t.get('name', '') for t in tasks[:3] if isinstance(t, dict)])}")
        if description:
            snippet_parts.append(description[:200])
        snippet = " | ".join(snippet_parts) or name
        identifiers: dict[str, str] = {"pwc_slug": slug} if slug else {}
        return SourceRecord(
            title=name[:300],
            url=url,
            source="papers_with_code",
            source_type="dataset",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=snippet[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.7 if slug else 0.4,
            primary_source=bool(slug),
            citation=f"PWC:{slug}" if slug else None,
            identifiers=identifiers,
        )

    def _from_benchmark(self, entry: dict[str, Any]) -> SourceRecord:
        name = (entry.get("name") or "").strip() or "(unnamed benchmark)"
        slug = entry.get("slug") or ""
        description = (entry.get("description") or "").strip()
        url = entry.get("url") or (f"https://paperswithcode.com/benchmark/{slug}" if slug else "")
        identifiers: dict[str, str] = {"pwc_slug": slug} if slug else {}
        return SourceRecord(
            title=name[:300],
            url=url,
            source="papers_with_code",
            source_type="benchmark",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=(description or "")[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.75 if slug else 0.4,
            primary_source=bool(slug),
            citation=f"PWC-benchmark:{slug}" if slug else None,
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


register_adapter(PapersWithCodeAdapter())
