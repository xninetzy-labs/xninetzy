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


def _from_repo(repo: dict[str, Any]) -> SourceRecord:
    full_name = str(repo.get("full_name") or "").strip()
    description = (repo.get("description") or "").strip()
    html_url = repo.get("html_url") or (f"https://github.com/{full_name}" if full_name else "")
    owner = (repo.get("owner") or {}).get("login") if isinstance(repo.get("owner"), dict) else None
    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    language = repo.get("language") or None
    license_info = (repo.get("license") or {}).get("spdx_id") if isinstance(repo.get("license"), dict) else None
    pushed_at = repo.get("pushed_at") or repo.get("updated_at")
    identifiers: dict[str, str] = {}
    if full_name:
        identifiers["github"] = full_name
    topic_list = repo.get("topics") or []
    snippet_parts: list[str] = []
    if language:
        snippet_parts.append(f"lang={language}")
    if stars:
        snippet_parts.append(f"stars={stars}")
    if forks:
        snippet_parts.append(f"forks={forks}")
    if topic_list:
        snippet_parts.append(f"topics={','.join(topic_list[:5])}")
    snippet = " | ".join(snippet_parts)
    if description:
        snippet = f"{description[:400]} | {snippet}" if snippet else description[:400]
    confidence = 0.6 + min(0.3, stars * 0.0001)
    return SourceRecord(
        title=full_name or "(unnamed repo)",
        url=html_url,
        source="github",
        source_type="code",
        published_at=repo.get("created_at"),
        updated_at=pushed_at,
        author=owner,
        snippet=snippet,
        content=None,
        language="en",
        license=license_info,
        retrieved_at=make_retrieved_at(),
        confidence=min(confidence, 1.0),
        primary_source=bool(full_name),
        citation=f"GitHub:{full_name}" if full_name else None,
        identifiers=identifiers,
    )


class GitHubAdapter(SourceAdapter):
    id = "github"
    category = SourceCategory.CODE
    base_url = "https://api.github.com"
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
            self._token = str(getattr(settings, "GITHUB_TOKEN", "") or "")
        return self._token

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("github breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "per_page": max(1, min(limit, 100)),
            "sort": "stars",
            "order": "desc",
        }
        headers = self._headers()
        try:
            payload = await retry_async(self.retry, self._fetch_json, "/search/repositories", params, headers)
        except Exception as exc:
            logger.warning("github search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        records: list[SourceRecord] = []
        for repo in payload.get("items") or []:
            try:
                records.append(_from_repo(repo))
            except Exception as exc:
                logger.warning("github parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("https://github.com/"):
            cleaned = cleaned[len("https://github.com/"):]
        cleaned = cleaned.strip("/")
        if not cleaned:
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, f"/repos/{cleaned}", None, self._headers()
            )
        except Exception as exc:
            logger.warning("github fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not payload:
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_repo(payload)
        except Exception as exc:
            logger.warning("github fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json("/zen", None, self._headers())
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        token = self._load_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
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


register_adapter(GitHubAdapter())
