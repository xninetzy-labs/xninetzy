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


def _from_paper(paper: dict[str, Any]) -> SourceRecord:
    paper_id = str(paper.get("paperId") or "")
    title = (paper.get("title") or "").strip() or "(untitled)"
    authors = paper.get("authors") or []
    author = ", ".join([a.get("name", "") for a in authors[:3] if a.get("name")])
    year = paper.get("year")
    published_at = str(year) if isinstance(year, int) else None
    venue = (paper.get("venue") or "").strip()
    citation_count = paper.get("citationCount") or 0
    snippet = (paper.get("abstract") or "")[:600]
    identifiers: dict[str, str] = {}
    if paper_id:
        identifiers["s2"] = paper_id
    external_ids = paper.get("externalIds") or {}
    if external_ids.get("DOI"):
        identifiers["doi"] = external_ids["DOI"]
    if external_ids.get("ArXiv"):
        identifiers["arxiv"] = external_ids["ArXiv"]
    url = paper.get("url") or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "")
    confidence = 0.7 + min(0.2, (citation_count or 0) * 0.001)
    citation = f"S2:{paper_id} - {title}" if paper_id else None
    if venue:
        citation = f"{citation} ({venue})" if citation else f"{title} ({venue})"
    return SourceRecord(
        title=title,
        url=url,
        source="semantic_scholar",
        source_type="paper",
        published_at=published_at,
        updated_at=published_at,
        author=author or None,
        snippet=snippet,
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=min(confidence, 1.0),
        primary_source=bool(identifiers.get("doi") or identifiers.get("arxiv")),
        citation=citation,
        identifiers=identifiers,
    )


class SemanticScholarAdapter(SourceAdapter):
    id = "semantic_scholar"
    category = SourceCategory.PAPER
    base_url = "https://api.semanticscholar.org/graph/v1"
    requires_api_key = False
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
            self._api_key = str(getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", "") or "")
        return self._api_key

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("semantic_scholar breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "query": query,
            "limit": max(1, min(limit, 100)),
            "fields": "title,abstract,year,authors,venue,citationCount,externalIds,url,paperId",
        }
        headers: dict[str, str] = {}
        api_key = self._load_api_key()
        if api_key:
            headers["x-api-key"] = api_key
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/paper/search", params, headers)
        except Exception as exc:
            logger.warning("semantic_scholar search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for paper in payload.get("data") or []:
            try:
                records.append(_from_paper(paper))
            except Exception as exc:
                logger.warning("semantic_scholar parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        cleaned = identifier.strip()
        if cleaned.startswith("https://"):
            if "/paper/" in cleaned:
                cleaned = cleaned.split("/paper/")[-1].split("?")[0].split("#")[0]
            else:
                cleaned = cleaned.rsplit("/", 1)[-1]
        fields = "title,abstract,year,authors,venue,citationCount,externalIds,url,paperId"
        headers: dict[str, str] = {}
        api_key = self._load_api_key()
        if api_key:
            headers["x-api-key"] = api_key
        try:
            payload = await retry_async(self.retry, self._fetch_json, f"/paper/{cleaned}", {"fields": fields}, headers)
        except Exception as exc:
            logger.warning("semantic_scholar fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_paper(payload)
        except Exception as exc:
            logger.warning("semantic_scholar fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/paper/search", {"query": "test", "limit": 1, "fields": "paperId"})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self,
        path: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(SemanticScholarAdapter())
