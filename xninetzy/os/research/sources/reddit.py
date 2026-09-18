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


def _from_post(post: dict[str, Any]) -> SourceRecord:
    title = (post.get("title") or "").strip() or "(untitled)"
    permalink = post.get("permalink") or ""
    url = post.get("url_overridden_by_dest") or (f"https://www.reddit.com{permalink}" if permalink else "")
    subreddit = post.get("subreddit")
    author = post.get("author")
    score = post.get("score") or 0
    num_comments = post.get("num_comments") or 0
    created_utc = post.get("created_utc")
    created_at = (
        f"{int(created_utc):.0f}".rjust(13, "0") if isinstance(created_utc, (int, float)) else None
    )
    iso = None
    if isinstance(created_utc, (int, float)):
        try:
            from datetime import datetime, timezone

            iso = datetime.fromtimestamp(float(created_utc), tz=timezone.utc).isoformat()
        except Exception:
            iso = None
    selftext = (post.get("selftext") or "")[:600]
    identifiers: dict[str, str] = {}
    if post.get("id"):
        identifiers["reddit"] = str(post["id"])
    if subreddit:
        identifiers["subreddit"] = str(subreddit)
    snippet_parts = []
    if subreddit:
        snippet_parts.append(f"r/{subreddit}")
    if score:
        snippet_parts.append(f"score={score}")
    if num_comments:
        snippet_parts.append(f"comments={num_comments}")
    if selftext:
        snippet_parts.append(selftext)
    snippet = " | ".join(snippet_parts)
    return SourceRecord(
        title=title,
        url=url,
        source="reddit",
        source_type="social",
        published_at=iso,
        updated_at=iso,
        author=author,
        snippet=snippet[:600],
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.5 + min(0.4, score * 0.0001),
        primary_source=bool(url),
        citation=f"Reddit:{post.get('id')} r/{subreddit}" if post.get("id") else None,
        identifiers=identifiers,
    )


class RedditAdapter(SourceAdapter):
    id = "reddit"
    category = SourceCategory.NEWS
    base_url = "https://www.reddit.com"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=3, backoff_base_seconds=0.5, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._user_agent = "xninetzy-research/1.0"

    def _load_user_agent(self) -> str:
        settings = get_settings()
        custom = str(getattr(settings, "REDDIT_USER_AGENT", "") or "")
        return custom or self._user_agent

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            logger.warning("reddit breaker open; skipping search")
            return []
        await self._limiter.acquire()
        params: dict[str, Any] = {
            "q": query,
            "limit": max(1, min(limit, 100)),
            "sort": "relevance",
        }
        headers = {"User-Agent": self._load_user_agent()}
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, "/search.json", params, headers
            )
        except Exception as exc:
            logger.warning("reddit search failed: %s", exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        children = (payload.get("data") or {}).get("children") or []
        records: list[SourceRecord] = []
        for entry in children:
            post = entry.get("data") if isinstance(entry, dict) else None
            if not isinstance(post, dict):
                continue
            try:
                records.append(_from_post(post))
            except Exception as exc:
                logger.warning("reddit parse failed: %s", exc)
        return records

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if cleaned.startswith("https://"):
            if "/comments/" in cleaned:
                idx = cleaned.find("/comments/")
                tail = cleaned[idx + len("/comments/"):]
                post_id = tail.split("/")[0]
                cleaned = post_id
            else:
                cleaned = cleaned.rstrip("/").split("/")[-1]
        if not cleaned.isdigit():
            return None
        if not await self._breaker.allow():
            return None
        await self._limiter.acquire()
        headers = {"User-Agent": self._load_user_agent()}
        try:
            payload = await retry_async(
                self.retry, self._fetch_json, f"/comments/{cleaned}.json", None, headers
            )
        except Exception as exc:
            logger.warning("reddit fetch failed: %s", exc)
            await self._breaker.record_failure()
            return None
        if not isinstance(payload, list) or not payload:
            await self._breaker.record_success()
            return None
        first = payload[0]
        post = (first.get("data") or {}).get("children") or [{}]
        post_data = post[0].get("data") if post else None
        if not isinstance(post_data, dict):
            await self._breaker.record_success()
            return None
        await self._breaker.record_success()
        try:
            return _from_post(post_data)
        except Exception as exc:
            logger.warning("reddit fetch parse failed: %s", exc)
            return None

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        try:
            await self._fetch_json(
                "/r/programming/hot.json",
                {"limit": 1},
                {"User-Agent": self._load_user_agent()},
            )
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

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


register_adapter(RedditAdapter())
