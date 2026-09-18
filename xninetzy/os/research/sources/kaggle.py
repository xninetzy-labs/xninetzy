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


class KaggleAdapter(SourceAdapter):
    id = "kaggle"
    category = SourceCategory.DATASET
    base_url = "https://www.kaggle.com/api/v1"
    requires_api_key = True
    rate_limit = RateLimit(requests_per_minute=20, burst=2)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._credentials = ""

    def _load_credentials(self) -> str:
        if not self._credentials:
            settings = get_settings()
            username = str(getattr(settings, "KAGGLE_USERNAME", "") or "")
            key = str(getattr(settings, "KAGGLE_KEY", "") or "")
            self._credentials = f"{username}:{key}" if username and key else ""
        return self._credentials

    def is_configured(self) -> bool:
        return bool(self._credentials)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not self.is_configured():
            logger.info("kaggle search skipped: KAGGLE_USERNAME/KAGGLE_KEY not set")
            return []
        if not await self._breaker.allow():
            logger.warning("kaggle breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {"search": query, "page_size": max(1, min(limit, 20))}
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, "/datasets/list", params
            )
        except Exception as exc:
            logger.warning("kaggle search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for entry in payload[:limit]:
            try:
                records.append(self._from_dataset(entry))
            except Exception as exc:
                logger.warning("kaggle parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not self.is_configured():
            return None
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if cleaned.startswith("https://www.kaggle.com/datasets/"):
            cleaned = cleaned.split("/datasets/", 1)[1]
        slug = cleaned.strip("/")
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, f"/datasets/view/{slug}", None
            )
        except Exception as exc:
            logger.warning("kaggle fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_dataset(payload)
        except Exception as exc:
            logger.warning("kaggle fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not self.is_configured():
            return HealthStatus.DEGRADED
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/datasets/list", {"page_size": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_dataset(self, entry: dict[str, Any]) -> SourceRecord:
        ref = (entry.get("datasetRef") or "") if isinstance(entry, dict) else ""
        title = (entry.get("title") or ref or "(untitled)").strip()
        url = entry.get("url") or (f"https://www.kaggle.com/datasets/{ref}" if ref else "")
        size = entry.get("totalBytes")
        last_updated = entry.get("lastUpdated")
        creator = entry.get("creatorName") or entry.get("ownerName")
        snippet_parts: list[str] = []
        if size:
            snippet_parts.append(f"size_bytes={size}")
        if last_updated:
            snippet_parts.append(f"updated={last_updated}")
        snippet = " | ".join(snippet_parts)
        identifiers: dict[str, str] = {}
        if ref:
            identifiers["kaggle_ref"] = ref
        return SourceRecord(
            title=title[:300],
            url=url,
            source="kaggle",
            source_type="dataset",
            published_at=None,
            updated_at=str(last_updated) if last_updated else None,
            author=creator,
            snippet=snippet[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.85 if ref else 0.4,
            primary_source=bool(ref),
            citation=f"Kaggle:{ref}" if ref else None,
            identifiers=identifiers,
        )

    async def _fetch_json(
        self, path: str, params: dict[str, Any] | None
    ) -> dict[str, Any] | list[Any]:
        import base64
        import httpx

        url = f"{self.base_url}{path}"
        auth_str = base64.b64encode(self._credentials.encode("utf-8")).decode("ascii")
        headers = {"Authorization": f"Basic {auth_str}"}
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(KaggleAdapter())
