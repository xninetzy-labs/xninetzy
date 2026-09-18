from __future__ import annotations

import json
from typing import Any

from xninetzy.core.config import get_settings
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


class FREDAdapter(SourceAdapter):
    id = "fred"
    category = SourceCategory.ECONOMICS
    base_url = "https://api.stlouisfed.org/fred"
    requires_api_key = True
    rate_limit = RateLimit(requests_per_minute=60, burst=5)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._api_key = ""

    def _load_api_key(self) -> str:
        if not self._api_key:
            settings = get_settings()
            self._api_key = str(getattr(settings, "FRED_API_KEY", "") or "")
        return self._api_key

    def is_configured(self) -> bool:
        return bool(self._load_api_key())

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not self.is_configured():
            logger.info("fred search skipped: FRED_API_KEY not set")
            return []
        if not await self._breaker.allow():
            logger.warning("fred breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "search_text": query,
            "api_key": self._load_api_key(),
            "file_type": "json",
            "limit": max(1, min(limit, 100)),
            "order_by": "popularity",
            "sort_order": "desc",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/series/search", params)
        except Exception as exc:
            logger.warning("fred search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for entry in payload.get("seriess") or []:
            try:
                records.append(self._from_series(entry))
            except Exception as exc:
                logger.warning("fred parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not self.is_configured():
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params = {
            "series_id": identifier.strip(),
            "api_key": self._load_api_key(),
            "file_type": "json",
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/series", params)
        except Exception as exc:
            logger.warning("fred fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        seriess = payload.get("seriess") or []
        if not seriess:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_series(seriess[0])
        except Exception as exc:
            logger.warning("fred fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not self.is_configured():
            return HealthStatus.DEGRADED
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/series",
                {"series_id": "GDP", "api_key": self._load_api_key(), "file_type": "json"},
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_series(self, entry: dict[str, Any]) -> SourceRecord:
        series_id = str(entry.get("id") or "").strip()
        title = (entry.get("title") or series_id or "(untitled)").strip()
        frequency = entry.get("frequency_short") or entry.get("frequency")
        observation_start = entry.get("observation_start")
        observation_end = entry.get("observation_end")
        snippet_parts: list[str] = []
        if frequency:
            snippet_parts.append(f"freq={frequency}")
        if observation_start or observation_end:
            snippet_parts.append(f"range={observation_start or '?'}..{observation_end or '?'}")
        snippet = " | ".join(snippet_parts) or title
        identifiers: dict[str, str] = {"fred": series_id} if series_id else {}
        url = f"https://fred.stlouisfed.org/series/{series_id}" if series_id else "https://fred.stlouisfed.org"
        return SourceRecord(
            title=title[:300],
            url=url,
            source="fred",
            source_type="indicator",
            published_at=observation_start,
            updated_at=observation_end,
            author="FRED",
            snippet=snippet[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.95 if series_id else 0.4,
            primary_source=bool(series_id),
            citation=f"FRED:{series_id} - {title}" if series_id else None,
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


register_adapter(FREDAdapter())
