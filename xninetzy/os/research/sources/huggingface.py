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


def _from_model(model: dict[str, Any]) -> SourceRecord:
    model_id = str(model.get("id") or model.get("modelId") or "").strip()
    sha = str(model.get("sha") or "")
    tags = model.get("tags") or []
    pipeline_tag = next(
        (str(t) for t in tags if isinstance(t, str) and not t.startswith("license:")),
        None,
    )
    license_tag = next(
        (str(t).split(":", 1)[-1] for t in tags if isinstance(t, str) and t.startswith("license:")),
        None,
    )
    last_modified = model.get("lastModified")
    downloads = model.get("downloads") or 0
    likes = model.get("likes") or 0
    url = f"https://huggingface.co/{model_id}" if model_id else ""
    snippet_parts: list[str] = []
    if pipeline_tag:
        snippet_parts.append(f"pipeline={pipeline_tag}")
    if license_tag:
        snippet_parts.append(f"license={license_tag}")
    if downloads:
        snippet_parts.append(f"downloads={downloads}")
    if likes:
        snippet_parts.append(f"likes={likes}")
    snippet = " | ".join(snippet_parts)
    identifiers: dict[str, str] = {}
    if model_id:
        identifiers["hf_model"] = model_id
    if sha:
        identifiers["hf_sha"] = sha
    return SourceRecord(
        title=model_id or "(unnamed model)",
        url=url,
        source="huggingface",
        source_type="model",
        published_at=model.get("createdAt"),
        updated_at=last_modified,
        author=None,
        snippet=snippet[:600],
        content=None,
        language="en",
        license=license_tag,
        retrieved_at=make_retrieved_at(),
        confidence=0.6 + min(0.3, downloads * 0.000001),
        primary_source=bool(model_id),
        citation=f"HF:{model_id}" if model_id else None,
        identifiers=identifiers,
    )


def _from_dataset(dataset: dict[str, Any]) -> SourceRecord:
    dataset_id = str(dataset.get("id") or "").strip()
    tags = dataset.get("tags") or []
    license_tag = next(
        (str(t).split(":", 1)[-1] for t in tags if isinstance(t, str) and t.startswith("license:")),
        None,
    )
    last_modified = dataset.get("lastModified")
    downloads = dataset.get("downloads") or 0
    likes = dataset.get("likes") or 0
    url = f"https://huggingface.co/datasets/{dataset_id}" if dataset_id else ""
    snippet_parts: list[str] = []
    if license_tag:
        snippet_parts.append(f"license={license_tag}")
    if downloads:
        snippet_parts.append(f"downloads={downloads}")
    if likes:
        snippet_parts.append(f"likes={likes}")
    snippet = " | ".join(snippet_parts)
    identifiers: dict[str, str] = {}
    if dataset_id:
        identifiers["hf_dataset"] = dataset_id
    return SourceRecord(
        title=dataset_id or "(unnamed dataset)",
        url=url,
        source="huggingface",
        source_type="dataset",
        published_at=dataset.get("createdAt"),
        updated_at=last_modified,
        author=None,
        snippet=snippet[:600],
        content=None,
        language="en",
        license=license_tag,
        retrieved_at=make_retrieved_at(),
        confidence=0.6 + min(0.3, downloads * 0.000001),
        primary_source=bool(dataset_id),
        citation=f"HF-dataset:{dataset_id}" if dataset_id else None,
        identifiers=identifiers,
    )


class HuggingFaceAdapter(SourceAdapter):
    id = "huggingface"
    category = SourceCategory.MODEL
    base_url = "https://huggingface.co/api"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._token = ""

    def _load_token(self) -> str:
        if not self._token:
            settings = get_settings()
            self._token = str(getattr(settings, "HF_TOKEN", "") or "")
        return self._token

    def _headers(self) -> dict[str, str]:
        token = self._load_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("huggingface breaker open; skipping search")
            return []
        await self._limiter.acquire()
        target = str(kwargs.get("target") or "models")
        if target not in {"models", "datasets"}:
            target = "models"
        params: dict[str, Any] = {
            "search": query,
            "limit": max(1, min(limit, 100)),
        }
        try:
            payload = await retry_async(self.retry, self._fetch_json, f"/{target}", params, self._headers())
        except Exception as exc:
            logger.warning("huggingface search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        parser = _from_model if target == "models" else _from_dataset
        records: list[SourceRecord] = []
        for entry in payload if isinstance(payload, list) else []:
            try:
                records.append(parser(entry))
            except Exception as exc:
                logger.warning("huggingface parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not cleaned:
            return None
        target = "models"
        if cleaned.startswith("dataset:"):
            target = "datasets"
            cleaned = cleaned.split(":", 1)[1].strip()
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(self.retry, self._fetch_json, f"/{target}/{cleaned}", None, self._headers())
        except Exception as exc:
            logger.warning("huggingface fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        parser = _from_model if target == "models" else _from_dataset
        try:
            return parser(payload)
        except Exception as exc:
            logger.warning("huggingface fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/models", {"limit": 1, "search": "test"}, self._headers())
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_json(
        self,
        path: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        import httpx

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text
        return json.loads(text)


register_adapter(HuggingFaceAdapter())
