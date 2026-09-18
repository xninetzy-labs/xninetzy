from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

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


def _label_from_bindings(bindings: dict[str, Any]) -> str:
    label_obj = bindings.get("label") or {}
    if isinstance(label_obj, dict):
        value = label_obj.get("value")
        if isinstance(value, str):
            return value
    return ""


def _abstract_from_bindings(bindings: dict[str, Any]) -> str:
    abstract_obj = bindings.get("abstract") or {}
    if isinstance(abstract_obj, dict):
        value = abstract_obj.get("value")
        if isinstance(value, str):
            return value
    return ""


class DBpediaAdapter(SourceAdapter):
    id = "dbpedia"
    category = SourceCategory.ENTITY
    base_url = "https://dbpedia.org/sparql"
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
            logger.warning("dbpedia breaker open; skipping search")
            return []
        await self._limiter.acquire()
        sparql = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
            "SELECT ?entity ?label ?abstract WHERE { "
            "?entity rdfs:label ?label . "
            "FILTER (lang(?label) = 'en') "
            "FILTER (regex(str(?label), '" + _escape(query) + "', 'i')) "
            "OPTIONAL { ?entity <http://dbpedia.org/ontology/abstract> ?abstract . "
            "FILTER (lang(?abstract) = 'en') } "
            "} LIMIT " + str(max(1, min(limit, 50)))
        )
        params: dict[str, Any] = {"query": sparql, "format": "application/json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, params)
        except Exception as exc:
            logger.warning("dbpedia search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        bindings = (payload.get("results") or {}).get("bindings") or []
        records: list[SourceRecord] = []
        seen_labels: set[str] = set()
        for entry in bindings:
            try:
                label = _label_from_bindings(entry)
                if not label or label in seen_labels:
                    continue
                seen_labels.add(label)
                uri = (entry.get("entity") or {}).get("value") or ""
                abstract = _abstract_from_bindings(entry)
                resource = uri.split("/resource/", 1)[-1] if "/resource/" in uri else uri
                records.append(SourceRecord(
                    title=label,
                    url=f"https://dbpedia.org/page/{quote(resource, safe=':')}" if resource else "https://dbpedia.org/",
                    source="dbpedia",
                    source_type="entity",
                    published_at=None,
                    updated_at=None,
                    author=None,
                    snippet=abstract[:600],
                    content=None,
                    language="en",
                    license="CC BY-SA",
                    retrieved_at=make_retrieved_at(),
                    confidence=0.7 if uri else 0.3,
                    primary_source=bool(uri),
                    citation=f"DBpedia:{resource}" if resource else None,
                    identifiers={"dbpedia_uri": uri} if uri else {},
                ))
            except Exception as exc:
                logger.warning("dbpedia parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if cleaned.startswith("https://dbpedia.org/page/"):
            resource = cleaned.split("/page/", 1)[1]
        else:
            resource = cleaned
        if not resource:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        sparql = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
            "SELECT ?label ?abstract WHERE { "
            "<http://dbpedia.org/resource/" + _escape(resource) + "> rdfs:label ?label . "
            "FILTER (lang(?label) = 'en') "
            "OPTIONAL { <http://dbpedia.org/resource/" + _escape(resource) + "> "
            "<http://dbpedia.org/ontology/abstract> ?abstract . "
            "FILTER (lang(?abstract) = 'en') } "
            "} LIMIT 1"
        )
        params: dict[str, Any] = {"query": sparql, "format": "application/json"}
        try:
            payload = await retry_async(self.retry, self._fetch_json, params)
        except Exception as exc:
            logger.warning("dbpedia fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        bindings = (payload.get("results") or {}).get("bindings") or []
        if not bindings:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        entry = bindings[0]
        label = _label_from_bindings(entry) or resource
        abstract = _abstract_from_bindings(entry)
        return SourceRecord(
            title=label,
            url=f"https://dbpedia.org/page/{quote(resource, safe=':')}",
            source="dbpedia",
            source_type="entity",
            published_at=None,
            updated_at=None,
            author=None,
            snippet=abstract[:600],
            content=None,
            language="en",
            license="CC BY-SA",
            retrieved_at=make_retrieved_at(),
            confidence=0.9,
            primary_source=True,
            citation=f"DBpedia:{resource}",
            identifiers={"dbpedia_uri": f"http://dbpedia.org/resource/{resource}"},
        )

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        sparql = (
            "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"
        )
        try:
            await self._fetch_json({"query": sparql, "format": "application/json"})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(self, params: dict[str, Any]) -> dict[str, Any]:
        import httpx

        url = self.base_url
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


register_adapter(DBpediaAdapter())
