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


_INDICATOR_DESCRIPTIONS: dict[str, str] = {
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SP.POP.TOTL": "Population, total",
    "SL.UEM.TOTL.ZS": "Unemployment (% of total labor force)",
    "FR.INR.RINR": "Real interest rate (%)",
}


def _country_record(country: dict[str, Any]) -> SourceRecord:
    iso3 = str(country.get("id") or "").strip()
    iso2 = str(country.get("iso2Code") or "").strip()
    name = str(country.get("name") or "").strip() or iso3 or "(unknown country)"
    region = (country.get("region") or {}).get("value") if isinstance(country.get("region"), dict) else None
    income = (country.get("incomeLevel") or {}).get("value") if isinstance(country.get("incomeLevel"), dict) else None
    url = f"https://data.worldbank.org/country/{iso3.lower()}" if iso3 else "https://data.worldbank.org"
    snippet_parts: list[str] = []
    if region:
        snippet_parts.append(f"region={region}")
    if income:
        snippet_parts.append(f"income={income}")
    if iso2:
        snippet_parts.append(f"iso2={iso2}")
    snippet = " | ".join(snippet_parts) or name
    return SourceRecord(
        title=name,
        url=url,
        source="world_bank",
        source_type="entity",
        published_at=None,
        updated_at=None,
        author=None,
        snippet=snippet[:600],
        content=None,
        language="en",
        license="CC BY 4.0",
        retrieved_at=make_retrieved_at(),
        confidence=0.9 if iso3 else 0.4,
        primary_source=bool(iso3),
        citation=f"WorldBank:{iso3} - {name}" if iso3 else None,
        identifiers={"iso3": iso3, "iso2": iso2} if iso3 else {},
    )


def _indicator_record(item: list[Any], indicator: str, country_iso3: str) -> SourceRecord | None:
    if not isinstance(item, list) or len(item) < 2:
        return None
    meta = item[0] if isinstance(item[0], dict) else None
    value_obj = item[1] if isinstance(item[1], dict) else None
    value = value_obj.get("value") if isinstance(value_obj, dict) else None
    date = value_obj.get("date") if isinstance(value_obj, dict) else None
    if value is None:
        return None
    description = (meta or {}).get("value") or _INDICATOR_DESCRIPTIONS.get(indicator, indicator)
    url = (
        f"https://data.worldbank.org/indicator/{indicator}?locations={country_iso3.lower()}"
        if country_iso3
        else f"https://data.worldbank.org/indicator/{indicator}"
    )
    return SourceRecord(
        title=f"{country_iso3 or 'global'} - {description} ({date})",
        url=url,
        source="world_bank",
        source_type="indicator",
        published_at=date,
        updated_at=date,
        author=None,
        snippet=f"indicator={indicator} value={value} date={date}",
        content=None,
        language="en",
        license="CC BY 4.0",
        retrieved_at=make_retrieved_at(),
        confidence=0.9,
        primary_source=True,
        citation=f"WorldBank:{indicator}:{country_iso3}:{date}={value}",
        identifiers={"indicator": indicator, "country": country_iso3, "value": str(value)},
    )


class WorldBankAdapter(SourceAdapter):
    id = "world_bank"
    category = SourceCategory.ECONOMICS
    base_url = "https://api.worldbank.org/v2"
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
            logger.warning("world_bank breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "format": "json",
            "per_page": max(1, min(limit, 100)),
        }
        upper = query.strip().upper()
        if "/" in upper or "." in upper:
            params["id"] = upper
            path = "/indicator"
        else:
            path = "/country"
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, params)
        except Exception as exc:
            logger.warning("world_bank search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        if not isinstance(payload, list) or len(payload) < 2:
            return []
        records: list[SourceRecord] = []
        for entry in payload[1]:
            try:
                if path == "/country" and isinstance(entry, dict):
                    records.append(_country_record(entry))
                elif path == "/indicator" and isinstance(entry, list):
                    indicator = upper
                    rec = _indicator_record(entry, indicator, "")
                    if rec:
                        records.append(rec)
            except Exception as exc:
                logger.warning("world_bank parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        if ":" in cleaned:
            indicator, country = cleaned.split(":", 1)
            return await self._fetch_indicator(indicator, country)
        upper = cleaned.upper()
        if "/" in upper or "." in upper:
            return await self._fetch_indicator(upper, "")
        return await self._fetch_country(upper)

    async def _fetch_country(self, iso3: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        params: dict[str, Any] = {"format": "json", "per_page": 1}
        try:
            payload = await retry_async(self.retry, self._fetch_json, f"/country/{iso3}", params)
        except Exception as exc:
            logger.warning("world_bank country fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _country_record(payload[1][0])
        except Exception as exc:
            logger.warning("world_bank country parse failed: %s", exc)
            return None

    async def _fetch_indicator(self, indicator: str, country_iso3: str) -> SourceRecord | None:
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        path = f"/country/{country_iso3}/indicator/{indicator}" if country_iso3 else f"/indicator/{indicator}"
        params: dict[str, Any] = {"format": "json", "per_page": 1}
        try:
            payload = await retry_async(self.retry, self._fetch_json, path, params)
        except Exception as exc:
            logger.warning("world_bank indicator fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _indicator_record(payload[1][0], indicator, country_iso3)
        except Exception as exc:
            logger.warning("world_bank indicator parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/country/USA", {"format": "json", "per_page": 1})
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self, path: str, params: dict[str, Any] | None
    ) -> Any:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(WorldBankAdapter())
