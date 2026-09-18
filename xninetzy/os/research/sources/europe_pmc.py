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


class EuropePMCAdapter(SourceAdapter):
    id = "europe_pmc"
    category = SourceCategory.PAPER
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
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
            logger.warning("europe_pmc breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "query": query,
            "format": "json",
            "pageSize": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search", params)
        except Exception as exc:
            logger.warning("europe_pmc search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for entry in payload.get("resultList", {}).get("result", []) or []:
            try:
                records.append(self._from_entry(entry))
            except Exception as exc:
                logger.warning("europe_pmc parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params: dict[str, Any] = {"query": f"ext_id:{cleaned}", "format": "json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search", params)
        except Exception as exc:
            logger.warning("europe_pmc fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        results = payload.get("resultList", {}).get("result", []) or []
        if not results:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_entry(results[0])
        except Exception as exc:
            logger.warning("europe_pmc fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/search", {"query": "test", "format": "json", "pageSize": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_entry(self, entry: dict[str, Any]) -> SourceRecord:
        title = (entry.get("title") or "").strip() or "(untitled)"
        doi = (entry.get("doi") or "").strip() or None
        pmid = (entry.get("pmid") or "").strip() or None
        pmcid = (entry.get("pmcid") or "").strip() or None
        first_publication_date = entry.get("firstPublicationDate")
        author_string = (entry.get("authorString") or "").strip() or None
        abstract_text = (entry.get("abstractText") or "")[:600]
        journal = (entry.get("journalTitle") or entry.get("bookOrReportDetails", {}).get("publisher") or "").strip() or None
        identifiers: dict[str, str] = {}
        if doi:
            identifiers["doi"] = doi
        if pmid:
            identifiers["pmid"] = pmid
        if pmcid:
            identifiers["pmcid"] = pmcid
        url = ""
        if doi:
            url = f"https://doi.org/{doi}"
        elif pmcid:
            url = f"https://europepmc.org/article/PMC/{pmcid}"
        elif pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        snippet_parts: list[str] = []
        if journal:
            snippet_parts.append(f"journal={journal}")
        if first_publication_date:
            snippet_parts.append(f"date={first_publication_date}")
        if abstract_text:
            snippet_parts.append(abstract_text)
        snippet = " | ".join(snippet_parts)
        return SourceRecord(
            title=title[:300],
            url=url,
            source="europe_pmc",
            source_type="paper",
            published_at=first_publication_date,
            updated_at=first_publication_date,
            author=author_string,
            snippet=snippet[:600],
            content=None,
            language="en",
            license=entry.get("license") or None,
            retrieved_at=make_retrieved_at(),
            confidence=0.9 if (doi or pmid or pmcid) else 0.5,
            primary_source=bool(doi or pmid or pmcid),
            citation=f"EPMC:{pmid or pmcid or doi}",
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


register_adapter(EuropePMCAdapter())
