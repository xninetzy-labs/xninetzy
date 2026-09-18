from __future__ import annotations

import json
from typing import Any
from xml.etree import ElementTree as ET

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


class DBLPAdapter(SourceAdapter):
    id = "dblp"
    category = SourceCategory.PAPER
    base_url = "https://dblp.org/search/publ/api"
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
            logger.warning("dblp breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "h": max(1, min(limit, 50)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, "", params)
        except Exception as exc:
            logger.warning("dblp search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        hits = (payload.get("result") or {}).get("hits") or {}
        hit_list = hits.get("hit") or []
        records: list[SourceRecord] = []
        for hit in hit_list:
            info = hit.get("info") if isinstance(hit, dict) else None
            if not isinstance(info, dict):
                continue
            try:
                records.append(self._from_info(info))
            except Exception as exc:
                logger.warning("dblp parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if cleaned.startswith("https://dblp.org/"):
            cleaned = cleaned.split("dblp.org/", 1)[1]
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        url_path = cleaned
        try:
            xml_text = await retry_async(self.retry, self._fetch_xml, url_path)
        except Exception as exc:
            logger.warning("dblp fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not xml_text:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return self._from_xml(xml_text, cleaned)
        except Exception as exc:
            logger.warning("dblp fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("", {"q": "test", "format": "json", "h": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_info(self, info: dict[str, Any]) -> SourceRecord:
        title = (info.get("title") or "").strip() or "(untitled)"
        year = str(info.get("year") or "") or None
        venue = (info.get("venue") or "").strip() or None
        doi = (info.get("doi") or "").strip() or None
        url = info.get("url") or ""
        authors_entry = info.get("authors") or {}
        author_list = authors_entry.get("author") or []
        if isinstance(author_list, dict):
            author_list = [author_list]
        author_names = [str(a.get("text", "")) for a in author_list if isinstance(a, dict)]
        author = ", ".join(filter(None, author_names[:3])) or None
        identifiers: dict[str, str] = {"dblp_key": str(info.get("key") or "")}
        if doi:
            identifiers["doi"] = doi
        snippet_parts: list[str] = []
        if venue:
            snippet_parts.append(f"venue={venue}")
        if year:
            snippet_parts.append(f"year={year}")
        if author_names:
            snippet_parts.append(f"authors={','.join(author_names[:5])}")
        snippet = " | ".join(snippet_parts)
        confidence = 0.85 if doi else 0.7
        return SourceRecord(
            title=title[:300],
            url=url,
            source="dblp",
            source_type="paper",
            published_at=year,
            updated_at=year,
            author=author,
            snippet=snippet[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=confidence,
            primary_source=bool(doi or info.get("key")),
            citation=f"DBLP:{info.get('key', '')}" if info.get("key") else None,
            identifiers=identifiers,
        )

    def _from_xml(self, xml_text: str, key: str) -> SourceRecord | None:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("dblp xml parse failed: %s", exc)
            return None
        publication = None
        for child in root.iter():
            tag = child.tag.split("}", 1)[-1]
            if tag in {"article", "inproceedings", "incollection", "book", "phdthesis", "mastersthesis"}:
                publication = child
                break
        if publication is None:
            return None
        title_el = publication.find("title")
        title = (title_el.text if title_el is not None else None) or "(untitled)"
        year_el = publication.find("year")
        year = (year_el.text if year_el is not None else None) or None
        ee_el = publication.find("ee")
        doi_url = (ee_el.text if ee_el is not None else None) or ""
        doi = doi_url.replace("https://doi.org/", "").strip() if "doi.org" in doi_url else None
        url_el = publication.find("url")
        url = (url_el.text if url_el is not None else None) or doi_url or ""
        authors: list[str] = []
        for author_el in publication.findall("author"):
            for child in author_el.iter():
                tag = child.tag.split("}", 1)[-1]
                if tag == "fullname" and child.text:
                    authors.append(child.text.strip())
        author = ", ".join(authors[:3]) or None
        identifiers: dict[str, str] = {"dblp_key": key}
        if doi:
            identifiers["doi"] = doi
        return SourceRecord(
            title=title[:300],
            url=url,
            source="dblp",
            source_type="paper",
            published_at=year,
            updated_at=year,
            author=author,
            snippet=f"dblp_key={key}"[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.85 if doi or url else 0.6,
            primary_source=bool(doi or url),
            citation=f"DBLP:{key}",
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

    async def _fetch_xml(self, key_path: str) -> str:
        import httpx

        url = f"https://dblp.org/{key_path}.xml"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text


register_adapter(DBLPAdapter())
