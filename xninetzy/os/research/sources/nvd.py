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


def _severity_to_grade(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0.0:
        return "low"
    return "unknown"


def _from_cve(cve: dict[str, Any]) -> SourceRecord:
    cve_id = str(cve.get("id") or "").strip()
    descriptions = cve.get("descriptions") or []
    en_desc = next(
        (d.get("value") for d in descriptions if isinstance(d, dict) and d.get("lang") == "en"),
        "",
    )
    metrics = cve.get("metrics") or {}
    cvss_score: float | None = None
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if entries:
            primary = entries[0].get("cvssData") or {}
            score_value = primary.get("baseScore")
            if isinstance(score_value, (int, float)):
                cvss_score = float(score_value)
                break
    published = cve.get("published")
    last_modified = cve.get("lastModified")
    references = cve.get("references") or []
    ref_urls = [r.get("url") for r in references if isinstance(r, dict) and r.get("url")]
    identifiers: dict[str, str] = {"cve": cve_id}
    snippet_parts: list[str] = []
    if cvss_score is not None:
        snippet_parts.append(f"CVSS={cvss_score:.1f}")
    snippet_parts.append(_severity_to_grade(cvss_score))
    if ref_urls:
        snippet_parts.append(f"refs={len(ref_urls)}")
    snippet = " | ".join(snippet_parts)
    confidence = 0.95 if cve_id else 0.3
    url = (
        f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        if cve_id
        else (ref_urls[0] if ref_urls else "")
    )
    return SourceRecord(
        title=cve_id or "(unknown cve)",
        url=url,
        source="nvd",
        source_type="security",
        published_at=published,
        updated_at=last_modified,
        author=None,
        snippet=f"{en_desc[:400]} {snippet}".strip(),
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=confidence,
        primary_source=bool(cve_id),
        citation=f"NVD:{cve_id}" if cve_id else None,
        identifiers=identifiers,
    )


class NVDAdapter(SourceAdapter):
    id = "nvd"
    category = SourceCategory.SECURITY
    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=10, burst=2)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=1.0, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._api_key = ""

    def _load_api_key(self) -> str:
        if not self._api_key:
            settings = get_settings()
            self._api_key = str(getattr(settings, "NVD_API_KEY", "") or "")
        return self._api_key

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("nvd breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "keywordSearch": query,
            "resultsPerPage": max(1, min(limit, 100)),
        }
        headers = self._headers()
        try:
            payload = await retry_async(self.retry, self._fetch_json, "", params, headers)
        except Exception as exc:
            logger.warning("nvd search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for cve in payload.get("vulnerabilities") or []:
            try:
                cve_obj = cve.get("cve") or cve
                records.append(_from_cve(cve_obj))
            except Exception as exc:
                logger.warning("nvd parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip().upper()
        if not cleaned.startswith("CVE-"):
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params = {"cveId": cleaned}
        headers = self._headers()
        try:
            payload = await retry_async(self.retry, self._fetch_json, "", params, headers)
        except Exception as exc:
            logger.warning("nvd fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        vulns = payload.get("vulnerabilities") or []
        if not vulns:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_cve(vulns[0].get("cve") or vulns[0])
        except Exception as exc:
            logger.warning("nvd fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("", {"resultsPerPage": 1}, self._headers())
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        api_key = self._load_api_key()
        if api_key:
            headers["apiKey"] = api_key
        return headers

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


register_adapter(NVDAdapter())
