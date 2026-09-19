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


def _record_from_job(job: dict[str, Any]) -> SourceRecord:
    job_id = str(job.get("id") or job.get("slug") or "")
    title = (job.get("position") or job.get("title") or "").strip() or "(untitled)"
    company = (job.get("company") or "").strip()
    company = company.replace("@@", "@").replace("**", "").strip()
    url = job.get("url") or job.get("apply_url") or ""
    if not url and job_id:
        url = f"https://remoteok.com/remote-jobs/{job_id}"
    description = job.get("description") or ""
    snippet = description[:600] if isinstance(description, str) else ""
    tags = job.get("tags") or []
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
    posted_at = job.get("date") or job.get("created_at") or None
    identifiers: dict[str, str] = {"remoteok_id": job_id} if job_id else {}
    if tags_str:
        identifiers["tags"] = tags_str
    if company:
        identifiers["company"] = company
    return SourceRecord(
        title=title,
        url=url,
        source="remoteok",
        source_type="job",
        published_at=posted_at,
        updated_at=posted_at,
        author=company or None,
        snippet=snippet,
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.7,
        primary_source=True,
        citation=None,
        identifiers=identifiers,
    )


class RemoteOkAdapter(SourceAdapter):
    id = "remoteok"
    category = SourceCategory.COMPANY
    base_url = "https://remoteok.com"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=10, burst=2)
    retry = RetryPolicy(max_attempts=2, backoff_base_seconds=1.0, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=120.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 25, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("remoteok breaker open; skipping search")
            return []
        await self._limiter.acquire()
        headers = {"User-Agent": "xninetzy-research/1.0 (+https://xninetzy.local)"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/api", None, headers)
        except Exception as exc:
            logger.warning("remoteok search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        if not isinstance(payload, list):
            return []
        q = (query or "").strip().lower()
        records: list[SourceRecord] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if entry.get("legal") not in (None, "us-only"):
                continue
            title = (entry.get("position") or "").lower()
            company = (entry.get("company") or "").lower()
            tags = " ".join(entry.get("tags") or []).lower()
            haystack = f"{title} {company} {tags}"
            if q and q not in haystack:
                continue
            try:
                records.append(_record_from_job(entry))
            except Exception as exc:
                logger.warning("remoteok record parse failed: %s", exc)
            if len(records) >= max(1, min(limit, 100)):
                break
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        headers = {"User-Agent": "xninetzy-research/1.0 (+https://xninetzy.local)"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/api", None, headers)
        except Exception as exc:
            logger.warning("remoteok fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        await self._breaker.record_success()
        if not isinstance(payload, list):
            return None
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("id") or "") == identifier or entry.get("slug") == identifier:
                try:
                    return _record_from_job(entry)
                except Exception as exc:
                    logger.warning("remoteok fetch parse failed: %s", exc)
                    return None
        return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/api", None, {"User-Agent": "xninetzy-research/1.0"})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self,
        path: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            text = resp.text
        if not text:
            return {}
        return json.loads(text)


register_adapter(RemoteOkAdapter())
