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


class OSMAdapter(SourceAdapter):
    id = "osm"
    category = SourceCategory.GEOGRAPHIC
    base_url = "https://nominatim.openstreetmap.org"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=1.0, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    def _user_agent(self) -> str:
        settings = get_settings()
        custom = str(getattr(settings, "OSM_USER_AGENT", "") or "")
        if custom:
            return custom
        contact = str(getattr(settings, "OWNER_PHONE_NUMBER", "") or "xninetzy-owner")
        return f"xninetzy-research/1.0 (contact: {contact})"

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("osm breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "format": "jsonv2",
            "limit": max(1, min(limit, 50)),
            "addressdetails": 1,
        }
        headers = {"User-Agent": self._user_agent(), "Accept": "application/json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search", params, headers)
        except Exception as exc:
            logger.warning("osm search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        if not isinstance(payload, list):
            return []
        records: list[SourceRecord] = []
        for entry in payload:
            try:
                records.append(self._from_entry(entry))
            except Exception as exc:
                logger.warning("osm parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "osm_ids": cleaned.replace(":", ","),
            "format": "jsonv2",
            "addressdetails": 1,
        }
        headers = {"User-Agent": self._user_agent(), "Accept": "application/json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/lookup", params, headers)
        except Exception as exc:
            logger.warning("osm fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list) or not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_entry(payload[0])
        except Exception as exc:
            logger.warning("osm fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/search",
                {"q": "Jakarta", "format": "jsonv2", "limit": 1},
                {"User-Agent": self._user_agent()},
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_entry(self, entry: dict[str, Any]) -> SourceRecord:
        osm_type = str(entry.get("osm_type") or "")
        osm_id = str(entry.get("osm_id") or "")
        display_name = (entry.get("display_name") or "").strip() or f"{osm_type}/{osm_id}"
        lat = entry.get("lat")
        lon = entry.get("lon")
        cls = entry.get("category") or entry.get("type") or ""
        address = entry.get("address") or {}
        country = address.get("country")
        snippet_parts: list[str] = []
        if cls:
            snippet_parts.append(f"class={cls}")
        if country:
            snippet_parts.append(f"country={country}")
        if lat is not None and lon is not None:
            snippet_parts.append(f"lat={lat} lon={lon}")
        snippet = " | ".join(snippet_parts) or display_name
        identifiers: dict[str, str] = {}
        if osm_type and osm_id:
            identifiers["osm"] = f"{osm_type[0]}{osm_id}"
        return SourceRecord(
            title=display_name[:300],
            url=f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_type and osm_id else "",
            source="osm",
            source_type="geographic",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=snippet[:600],
            content=None,
            language="en",
            license="ODbL",
            retrieved_at=make_retrieved_at(),
            confidence=0.8 if osm_id else 0.4,
            primary_source=bool(osm_id),
            citation=f"OSM:{osm_type}/{osm_id}",
            identifiers=identifiers,
        )

    async def _fetch_json(
        self,
        path: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(OSMAdapter())
