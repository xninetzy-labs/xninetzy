from __future__ import annotations

from xninetzy.core.logging import logging
from xninetzy.os.research.academic_search import (
    get_paper as _legacy_get_paper,
    search_papers as _legacy_search,
)
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
)
from xninetzy.os.research.sources.registry import (
    build_breaker,
    build_rate_limiter,
    register_adapter,
)

logger = logging.getLogger(__name__)


def _from_arxiv_dict(item: dict) -> SourceRecord:
    title = item.get("title") or "(untitled)"
    url = item.get("url") or item.get("pdf_url") or ""
    arxiv_id = item.get("arxiv_id") or item.get("identifier") or ""
    identifiers: dict[str, str] = {}
    if arxiv_id:
        identifiers["arxiv"] = arxiv_id
    authors = item.get("authors") or []
    author = ", ".join(authors[:3]) if authors else None
    published = item.get("published") or item.get("year")
    if isinstance(published, int):
        published = str(published)
    return SourceRecord(
        title=title,
        url=url,
        source="arxiv",
        source_type="paper",
        published_at=published,
        updated_at=published,
        author=author,
        snippet=item.get("snippet") or item.get("abstract") or "",
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.85 if arxiv_id else 0.5,
        primary_source=bool(arxiv_id),
        citation=f"arXiv:{arxiv_id} - {title}" if arxiv_id else None,
        identifiers=identifiers,
    )


class ArxivAdapter(SourceAdapter):
    id = "arxiv"
    category = SourceCategory.PAPER
    base_url = "https://export.arxiv.org/api/query"
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
            logger.warning("arxiv breaker open; skipping search")
            return []
        await self._limiter.acquire()
        try:
            rows = await _legacy_search(query, sources="arxiv", max_results=limit)
        except Exception as exc:
            logger.warning("arxiv search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        return [_from_arxiv_dict(item) for item in rows[:limit]]

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            paper = await _legacy_get_paper(identifier, source="arxiv")
        except Exception as exc:
            logger.warning("arxiv fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if paper.get("status") != "ok":
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        return _from_arxiv_dict(paper)

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await _legacy_search("test", sources="arxiv", max_results=1)
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY


register_adapter(ArxivAdapter())
