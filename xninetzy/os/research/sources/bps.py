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


class BPSAdapter(SourceAdapter):
    id = "bps"
    category = SourceCategory.ECONOMICS
    base_url = "https://webapi.bps.go.id/v1/api"
    requires_api_key = True
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._api_key = ""

    def _load_api_key(self) -> str:
        if not self._api_key:
            settings = get_settings()
            self._api_key = str(getattr(settings, "BPS_API_KEY", "") or "")
        return self._api_key

    def is_configured(self) -> bool:
        return bool(self._load_api_key())

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not self.is_configured():
            logger.info("bps search skipped: BPS_API_KEY not set")
            return []
        if not await self._breaker.allow():
            logger.warning("bps breaker open; skipping search")
            return []
        await self._limiter.acquire()
        domain = str(kwargs.get("domain") or "0000")
        path = f"/list/model/statictable?key={self._load_api_key()}&domain={domain}&lang=ind"
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, None)
        except Exception as exc:
            logger.warning("bps list failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        if isinstance(payload, list):
            for entry in payload[:limit]:
                try:
                    records.append(self._from_entry(entry, query))
                except Exception as exc:
                    logger.warning("bps parse failed: %s", exc)
        elif isinstance(payload, dict):
            data = payload.get("data") or []
            if isinstance(data, list):
                for entry in data[:limit]:
                    try:
                        records.append(self._from_entry(entry, query))
                    except Exception as exc:
                        logger.warning("bps parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not self.is_configured():
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        parts = identifier.split(":")
        if len(parts) >= 3:
            domain, table_id = parts[0], parts[2]
            path = f"/list/vertikal/{table_id}?key={self._load_api_key()}&domain={domain}&lang=ind&th={parts[1] if len(parts) > 3 else ''}"
        else:
            domain = parts[0] if parts else "0000"
            path = f"/list/domain/{domain}/statictable?key={self._load_api_key()}&lang=ind"
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, None)
        except Exception as exc:
            logger.warning("bps fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            data = payload.get("data") if isinstance(payload, dict) else payload
            if isinstance(data, list) and data:
                return self._from_entry(data[0], identifier)
        except Exception as exc:
            logger.warning("bps fetch parse failed: %s", exc)
        return None

    async def health(self) -> HealthStatus:
        if not self.is_configured():
            return HealthStatus.DEGRADED
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                f"/list/domain/3500/statictable?key={self._load_api_key()}&lang=ind", None
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_entry(self, entry: Any, query: str) -> SourceRecord:
        if not isinstance(entry, dict):
            entry = {"title": str(entry)}
        table_id = str(entry.get("table_id") or entry.get("table") or "")
        title = str(entry.get("title") or entry.get("nama") or query).strip()
        domain = str(entry.get("domain_id") or entry.get("domain") or "0000")
        url = f"https://www.bps.go.id/indicator/{domain}/{table_id}" if table_id else "https://www.bps.go.id"
        snippet = str(entry.get("notes") or entry.get("description") or "")[:600]
        return SourceRecord(
            title=title[:300],
            url=url,
            source="bps",
            source_type="dataset",
            published_at=str(entry.get("last_update")) if entry.get("last_update") else None,
            updated_at=str(entry.get("last_update")) if entry.get("last_update") else None,
            author="BPS",
            snippet=snippet,
            content=None,
            language="id",
            license="CC BY 4.0",
            retrieved_at=make_retrieved_at(),
            confidence=0.9 if table_id else 0.4,
            primary_source=bool(table_id),
            citation=f"BPS:{domain}/{table_id} - {title}" if table_id else None,
            identifiers={"bps_table": table_id, "bps_domain": domain} if table_id else {},
        )

    async def _fetch_json(self, path: str, params: dict[str, Any] | None) -> Any:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        try:
            return json.loads(text)
        except Exception:
            return text


register_adapter(BPSAdapter())
