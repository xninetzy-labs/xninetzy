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


HF_LEADERBOARD_URL = "https://huggingface.co/api/spaces/open-llm-leaderboard/open_llm_leaderboard/backend"


class OpenLLMLeaderboardAdapter(SourceAdapter):
    id = "open_llm_leaderboard"
    category = SourceCategory.BENCHMARK
    base_url = HF_LEADERBOARD_URL
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=10, burst=2)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=1.0, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("open_llm_leaderboard breaker open; skipping search")
            return []
        await self._limiter.acquire()
        try:
            payload = await retry_async(self.retry, self._fetch_json, "", None)
        except Exception as exc:
            logger.warning("open_llm_leaderboard fetch failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        if not isinstance(payload, list):
            return []
        needle = query.strip().lower()
        records: list[SourceRecord] = []
        for entry in payload[:200]:
            try:
                rec = self._from_row(entry)
            except Exception as exc:
                logger.warning("open_llm_leaderboard parse failed: %s", exc)
                continue
            if not rec:
                continue
            if not needle or needle in rec.title.lower():
                records.append(rec)
                if len(records) >= limit:
                    return records
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        if not identifier:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(self.retry, self._fetch_json, "", None)
        except Exception as exc:
            logger.warning("open_llm_leaderboard fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list):
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        needle = identifier.strip().lower()
        for entry in payload:
            try:
                rec = self._from_row(entry)
            except Exception as exc:
                logger.warning("open_llm_leaderboard row parse failed: %s", exc)
                continue
            if rec and needle in rec.title.lower():
                return rec
        return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("", None)
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _from_row(self, entry: dict[str, Any]) -> SourceRecord | None:
        model_name = str(entry.get("model") or entry.get("name") or "").strip()
        if not model_name:
            return None
        avg_score = entry.get("average") or entry.get("avg_score")
        scores = entry.get("scores") or {}
        snippet_parts: list[str] = []
        if avg_score is not None:
            snippet_parts.append(f"avg={avg_score}")
        if isinstance(scores, dict):
            for k, v in list(scores.items())[:3]:
                snippet_parts.append(f"{k}={v}")
        elif isinstance(scores, list):
            for v in scores[:3]:
                snippet_parts.append(str(v))
        precision = entry.get("precision")
        if precision:
            snippet_parts.append(f"precision={precision}")
        snippet = " | ".join(snippet_parts) or model_name
        identifiers: dict[str, str] = {"leaderboard_model": model_name}
        hf_id = entry.get("hf_model_id") or entry.get("fullname") or model_name
        url = f"https://huggingface.co/{hf_id}" if hf_id else "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard"
        return SourceRecord(
            title=model_name[:300],
            url=url,
            source="open_llm_leaderboard",
            source_type="benchmark",
            published_at=None,
            updated_at=str(entry.get("submitted_date") or "") or None,
            author=None,
            snippet=snippet[:600],
            content=None,
            language="en",
            license=None,
            retrieved_at=make_retrieved_at(),
            confidence=0.85,
            primary_source=bool(url),
            citation=f"OpenLLM-LB:{model_name}",
            identifiers=identifiers,
        )

    async def _fetch_json(self, path: str, params: dict[str, Any] | None) -> Any:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
        try:
            return json.loads(text)
        except Exception:
            return []


register_adapter(OpenLLMLeaderboardAdapter())
