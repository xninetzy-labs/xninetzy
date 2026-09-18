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


class ZenodoAdapter(SourceAdapter):
    id = "zenodo"
    category = SourceCategory.DATASET
    base_url = "https://zenodo.org/api"
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
            logger.warning("zenodo breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "size": max(1, min(limit, 100)),
            "sort": "mostviewed",
        }
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, "/records", params
            )
        except Exception as exc:
            logger.warning("zenodo search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        hits = payload.get("hits", {}).get("hits") if isinstance(payload, dict) else None
        if not isinstance(hits, list):
            return records
        for entry in hits:
            try:
                records.append(self._from_record(entry))
            except Exception as exc:
                logger.warning("zenodo parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if cleaned.startswith("https://zenodo.org/record/"):
            record_id = cleaned.split("/record/", 1)[1].split("/")[0].split("?")[0]
        elif cleaned.startswith("zenodo:"):
            record_id = cleaned.split(":", 1)[1]
        elif cleaned.isdigit():
            record_id = cleaned
        else:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, f"/records/{record_id}", None
            )
        except Exception as exc:
            logger.warning("zenodo fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_record(payload)
        except Exception as exc:
            logger.warning("zenodo fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/records", {"q": "test", "size": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_record(self, entry: dict[str, Any]) -> SourceRecord:
        record_id = str(entry.get("id") or "").strip()
        doi = (entry.get("doi") or "").strip()
        metadata = entry.get("metadata") or {}
        title = str(metadata.get("title") or doi or record_id).strip()
        if isinstance(title, list):
            title = title[0] if title else ""
        description = str(metadata.get("description") or "")[:600]
        if isinstance(description, list):
            description = description[0] if description else ""
        publication_date = metadata.get("publication_date")
        creators = metadata.get("creators") or []
        author = ", ".join(
            [str(c.get("name") or c.get("fullname") or "") for c in creators[:3] if isinstance(c, dict)]
        ) or None
        resource_type = (metadata.get("resource_type") or {}).get("title") if isinstance(metadata.get("resource_type"), dict) else None
        identifiers: dict[str, str] = {"zenodo": record_id}
        if doi:
            identifiers["doi"] = doi
        url = entry.get("links", {}).get("self_html") if isinstance(entry.get("links"), dict) else None
        if not url and record_id:
            url = f"https://zenodo.org/record/{record_id}"
        return SourceRecord(
            title=str(title)[:300],
            url=str(url or ""),
            source="zenodo",
            source_type="dataset",
            published_at=str(publication_date) if publication_date else None,
            updated_at=str(publication_date) if publication_date else None,
            author=author,
            snippet=f"{str(resource_type or 'dataset')} - {description}"[:600],
            content=None,
            language="en",
            license=(metadata.get("license") or {}).get("id") if isinstance(metadata.get("license"), dict) else None,
            retrieved_at=make_retrieved_at(),
            confidence=0.9 if record_id else 0.4,
            primary_source=bool(record_id),
            citation=f"Zenodo:{record_id}" if record_id else None,
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


register_adapter(ZenodoAdapter())
