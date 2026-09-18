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


def _from_crossref_dict(item: dict) -> SourceRecord:
    title = item.get("title") or "(untitled)"
    doi = item.get("identifier") or item.get("DOI") or ""
    url = item.get("url") or (f"https://doi.org/{doi}" if doi else "")
    authors = item.get("authors") or []
    author = ", ".join(authors[:3]) if authors else None
    year = item.get("year")
    published = str(year) if year else None
    identifiers: dict[str, str] = {}
    if doi:
        identifiers["doi"] = doi
    return SourceRecord(
        title=title,
        url=url,
        source="crossref",
        source_type="paper",
        published_at=published,
        updated_at=published,
        author=author,
        snippet=item.get("snippet") or item.get("abstract") or "",
        content=None,
        language="en",
        license=item.get("license") or None,
        retrieved_at=make_retrieved_at(),
        confidence=0.85 if doi else 0.5,
        primary_source=bool(doi),
        citation=f"DOI:{doi} - {title}" if doi else None,
        identifiers=identifiers,
    )


class CrossrefAdapter(SourceAdapter):
    id = "crossref"
    category = SourceCategory.PAPER
    base_url = "https://api.crossref.org/works"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=50, burst=5)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("crossref breaker open; skipping search")
            return []
        await self._limiter.acquire()
        try:
            rows = await _legacy_search(query, sources="crossref", max_results=limit)
        except Exception as exc:
            logger.warning("crossref search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        return [_from_crossref_dict(item) for item in rows[:limit]]

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            paper = await _legacy_get_paper(identifier, source="doi")
        except Exception as exc:
            logger.warning("crossref fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if paper.get("status") != "ok":
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        return _from_crossref_dict(paper)

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await _legacy_search("test", sources="crossref", max_results=1)
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY


register_adapter(CrossrefAdapter())
