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


def _from_pubmed_article(article: dict[str, Any]) -> SourceRecord:
    medline = article.get("MedlineCitation") or {}
    article_data = medline.get("Article") or {}
    title = (article_data.get("ArticleTitle") or "").strip() or "(untitled)"
    authors_list = (article_data.get("AuthorList") or {}).get("Author") or []
    authors = [
        " ".join(filter(None, [
            ((a.get("ForeName") or "")),
            ((a.get("LastName") or "")),
        ]))
        for a in authors_list
    ]
    author = ", ".join([a for a in authors if a][:3]) or None
    journal = ((article_data.get("Journal") or {}).get("Title") or "").strip()
    pub_date = ((article_data.get("Journal") or {}).get("JournalIssue") or {}).get("PubDate") or {}
    year_raw = pub_date.get("Year") or ""
    if not year_raw:
        medline_date = pub_date.get("MedlineDate") or ""
        year_raw = medline_date[:4] if len(medline_date) >= 4 else ""
    published_at = str(year_raw).strip() or None
    pmid = str(medline.get("PMID") or "")
    abstract_in = article_data.get("Abstract") or {}
    abstract_text = ""
    if isinstance(abstract_in, dict):
        abstract_parts = abstract_in.get("AbstractText") or []
        if isinstance(abstract_parts, list):
            abstract_text = " ".join(
                [
                    str(p.get("#text") if isinstance(p, dict) else p)
                    for p in abstract_parts
                ]
            )
        elif isinstance(abstract_parts, str):
            abstract_text = abstract_parts
    elif isinstance(abstract_in, str):
        abstract_text = abstract_in
    identifiers: dict[str, str] = {}
    if pmid:
        identifiers["pmid"] = pmid
    article_ids = article_data.get("ELocationID") or []
    for loc in article_ids if isinstance(article_ids, list) else []:
        if isinstance(loc, dict) and loc.get("EIdType") == "doi":
            doi = str(loc.get("#text") or "").strip()
            if doi:
                identifiers["doi"] = doi
                break
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
    citation = None
    if pmid:
        citation = f"PMID:{pmid} - {title}"
        if journal:
            citation = f"{citation} ({journal})"
    return SourceRecord(
        title=title,
        url=url,
        source="pubmed",
        source_type="paper",
        published_at=published_at,
        updated_at=published_at,
        author=author,
        snippet=abstract_text[:600],
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.85 if pmid else 0.5,
        primary_source=bool(pmid),
        citation=citation,
        identifiers=identifiers,
    )


class PubMedAdapter(SourceAdapter):
    id = "pubmed"
    category = SourceCategory.PAPER
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
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
            logger.warning("pubmed breaker open; skipping search")
            return []
        await self._limiter.acquire()
        search_params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": max(1, min(limit, 50)),
            "retmode": "json",
        }
        try:
            envelope = await retry_async(
                self.retry, self._fetch_json, "/esearch.fcgi", search_params
            )
        except Exception as exc:
            logger.warning("pubmed esearch failed: %s", exc)
            await self._breaker.record_failure()
            return []
        id_list = (envelope.get("esearchresult") or {}).get("idlist") or []
        if not id_list:
            await self._breaker.record_success()
            return []
        await self._breaker.record_success()
        return await self._fetch_many(list(id_list))

    async def _fetch_many(self, pmids: list[str]) -> list[SourceRecord]:
        if not pmids:
            return []
        if not await self._breaker.allow():
            return []
        await self._limiter.acquire()
        fetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        try:
            envelope = await retry_async(
                self.retry, self._fetch_json, "/esummary.fcgi", fetch_params
            )
        except Exception as exc:
            logger.warning("pubmed esummary failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        result = envelope.get("result") or {}
        records: list[SourceRecord] = []
        for pmid in pmids:
            article = result.get(pmid) or result.get("uids")
            if not isinstance(article, dict):
                continue
            try:
                records.append(_from_pubmed_article(article))
            except Exception as exc:
                logger.warning("pubmed parse failed for %s: %s", pmid, exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("PMID:"):
            cleaned = cleaned.split(":", 1)[1].strip()
        if not cleaned.isdigit():
            return None
        records = await self._fetch_many([cleaned])
        return records[0] if records else None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/esearch.fcgi", {"db": "pubmed", "term": "test", "retmax": 1, "retmode": "json"}
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

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


register_adapter(PubMedAdapter())
