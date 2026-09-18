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


def _from_snapshot(snap: dict[str, Any]) -> SourceRecord:
    url = str(snap.get("url") or "").strip()
    timestamp = str(snap.get("timestamp") or "").strip()
    archive_url = (
        f"https://web.archive.org/web/{timestamp}/{url}" if url and timestamp else url
    )
    status = str(snap.get("status") or "")
    mime = str(snap.get("mime") or "text/html")
    digest = str(snap.get("digest") or "")
    identifiers: dict[str, str] = {}
    if timestamp:
        identifiers["wayback_timestamp"] = timestamp
    if digest:
        identifiers["digest"] = digest
    return SourceRecord(
        title=url or "(unknown url)",
        url=archive_url or url,
        source="wayback",
        source_type="archive",
        published_at=timestamp,
        updated_at=timestamp,
        author=None,
        snippet=f"status={status} mime={mime}",
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.8 if status.startswith("2") else 0.4,
        primary_source=bool(archive_url),
        citation=f"Wayback:{timestamp} - {url}" if timestamp else None,
        identifiers=identifiers,
    )


class WaybackAdapter(SourceAdapter):
    id = "wayback"
    category = SourceCategory.GENERAL
    base_url = "https://web.archive.org"
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
            logger.warning("wayback breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "url": query,
            "limit": max(1, min(limit, 100)),
            "output": "json",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/cdx/search/cdx", params)
        except Exception as exc:
            logger.warning("wayback search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        if not isinstance(payload, list) or len(payload) < 2:
            return []
        headers = payload[0]
        records: list[SourceRecord] = []
        for row in payload[1:]:
            try:
                entry = dict(zip(headers, row, strict=True))
                records.append(_from_snapshot(entry))
            except Exception as exc:
                logger.warning("wayback parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params = {"url": cleaned, "limit": 1, "output": "json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/cdx/search/cdx", params)
        except Exception as exc:
            logger.warning("wayback fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list) or len(payload) < 2:
            await self._breaker.record_success()
            return None
        headers = payload[0]
        await self._breaker.record_success()
        try:
            entry = dict(zip(headers, payload[1], strict=True))
            return _from_snapshot(entry)
        except Exception as exc:
            logger.warning("wayback fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/cdx/search/cdx", {"url": "example.com", "limit": 1, "output": "json"}
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self, path: str, params: dict[str, Any] | None
    ) -> dict[str, Any] | list[Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(WaybackAdapter())
