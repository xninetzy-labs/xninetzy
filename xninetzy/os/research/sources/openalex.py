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


def _record_from_work(work: dict[str, Any]) -> SourceRecord:
    title = (work.get("title") or "").strip() or "(untitled)"
    doi = (work.get("doi") or "").replace("https://doi.org/", "").strip()
    openalex_id = (work.get("id") or "").rsplit("/", 1)[-1]
    authorships = work.get("authorships") or []
    author = None
    if authorships:
        first = authorships[0].get("author") or {}
        author = first.get("display_name")
    publication_date = work.get("publication_date")
    identifiers: dict[str, str] = {"openalex": openalex_id}
    if doi:
        identifiers["doi"] = doi
    primary_location = work.get("primary_location") or {}
    license_info = (work.get("open_access") or {}).get("license") or ""
    url = (
        work.get("doi_url")
        or (primary_location.get("landing_page_url") or "")
        or f"https://openalex.org/{openalex_id}"
    )
    return SourceRecord(
        title=title,
        url=url,
        source="openalex",
        source_type="paper",
        published_at=publication_date,
        updated_at=publication_date,
        author=author,
        snippet=work.get("abstract_inverted_index_summary")
        or _abstract_from_inverted(work.get("abstract_inverted_index") or {}),
        content=None,
        language="en",
        license=license_info or None,
        retrieved_at=make_retrieved_at(),
        confidence=0.8 if doi else 0.6,
        primary_source=bool(doi),
        citation=_format_citation(authorships, publication_date, title),
        identifiers=identifiers,
    )


def _abstract_from_inverted(index: dict[str, list[int]]) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, plist in index.items():
        for pos in plist:
            positions.append((pos, word))
    positions.sort(key=lambda pair: pair[0])
    return " ".join(word for _, word in positions)[:600]


def _format_citation(
    authorships: list[dict[str, Any]],
    publication_date: str | None,
    title: str,
) -> str | None:
    if not authorships:
        return None
    names = [
        (a.get("author") or {}).get("display_name", "")
        for a in authorships[:3]
    ]
    names = [n for n in names if n]
    if not names:
        return None
    year = publication_date[:4] if publication_date else ""
    suffix = " et al." if len(authorships) > 3 else ""
    return f"{', '.join(names)}{suffix} ({year}). {title}"


class OpenAlexAdapter(SourceAdapter):
    id = "openalex"
    category = SourceCategory.PAPER
    base_url = "https://api.openalex.org"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=60, burst=5)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("openalex breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "search": query,
            "per_page": max(1, min(limit, 50)),
            "mailto": "xninetzy-research@local",
        }
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, "/works", params
            )
        except Exception as exc:
            logger.warning("openalex search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        results = payload.get("results") or []
        records: list[SourceRecord] = []
        for work in results:
            try:
                records.append(_record_from_work(work))
            except Exception as exc:
                logger.warning("openalex record parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        cleaned = identifier.strip()
        if cleaned.startswith("https://openalex.org/"):
            cleaned = cleaned.rsplit("/", 1)[-1]
        if cleaned.startswith("doi:") or cleaned.startswith("10."):
            path = f"/works/doi:{cleaned.replace('doi:', '')}"
        elif cleaned.startswith("W"):
            path = f"/works/{cleaned}"
        else:
            path = f"/works/{cleaned}"
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, None)
        except Exception as exc:
            logger.warning("openalex fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        await self._breaker.record_success()
        if not payload:
            return None
        try:
            return _record_from_work(payload)
        except Exception as exc:
            logger.warning("openalex fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            payload = await self._fetch_json("/", {"mailto": "xninetzy-research@local"})
        except Exception:
            return HealthStatus.UNREACHABLE
        if "meta" in payload:
            return HealthStatus.HEALTHY
        return HealthStatus.DEGRADED

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


register_adapter(OpenAlexAdapter())
