from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse

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

DEFAULT_FEEDS: tuple[str, ...] = (
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://news.ycombinator.com/rss",
    "https://github.blog/feed/",
)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_text(entry: ET.Element, name: str) -> str | None:
    for child in entry.iter():
        if _strip_ns(child.tag) == name and child.text:
            return child.text.strip()
    return None


def _entry_url(entry: ET.Element) -> str | None:
    link = _find_text(entry, "link")
    if link:
        return link
    for child in entry.iter():
        if _strip_ns(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return None


def _from_entry(entry: ET.Element, feed_url: str) -> SourceRecord | None:
    title = _find_text(entry, "title")
    if not title:
        return None
    url = _entry_url(entry) or feed_url
    summary = _find_text(entry, "description") or _find_text(entry, "summary")
    author = _find_text(entry, "author") or _find_text(entry, "dc:creator")
    published = _find_text(entry, "pubDate") or _find_text(entry, "published")
    guid = _find_text(entry, "guid") or url
    identifiers: dict[str, str] = {"guid": guid, "feed": feed_url}
    domain = urlparse(feed_url).netloc
    return SourceRecord(
        title=title[:300],
        url=url,
        source="rss",
        source_type="news",
        published_at=published,
        updated_at=published,
        author=author,
        snippet=(summary or "")[:600],
        content=None,
        language="en",
        license=None,
        retrieved_at=make_retrieved_at(),
        confidence=0.6,
        primary_source=bool(url and url != feed_url),
        citation=f"RSS:{domain} - {title[:80]}",
        identifiers=identifiers,
    )


class RSSAdapter(SourceAdapter):
    id = "rss"
    category = SourceCategory.NEWS
    base_url = "https://example.invalid/rss"
    requires_api_key = False
    rate_limit = RateLimit(requests_per_minute=30, burst=3)
    retry = RetryPolicy(max_attempts=2, backoff_base_seconds=0.5, backoff_max_seconds=4.0)
    circuit_breaker = CircuitBreaker(failure_threshold=5, open_duration_seconds=60.0)

    def __init__(self) -> None:
        self._limiter: RateLimiter = build_rate_limiter(self)
        self._breaker: CircuitBreakerGuard = build_breaker(self)
        self._feeds: tuple[str, ...] = DEFAULT_FEEDS

    def configure(self, feeds: list[str] | tuple[str, ...]) -> None:
        if feeds:
            self._feeds = tuple(feeds)

    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        feeds_arg = kwargs.get("feeds")
        feeds = tuple(feeds_arg) if isinstance(feeds_arg, (list, tuple)) and feeds_arg else self._feeds
        if not feeds:
            return []
        needle = query.strip().lower()
        results: list[SourceRecord] = []
        for feed_url in feeds:
            records = await self._fetch_feed(feed_url)
            for record in records:
                if not needle or needle in record.title.lower() or needle in record.snippet.lower():
                    results.append(record)
                    if len(results) >= limit:
                        return results
        return results[:limit]

    async def fetch(self, identifier: str) -> SourceRecord | None:
        cleaned = identifier.strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            return None
        return await self._fetch_feed(cleaned, single=True)

    async def health(self) -> HealthStatus:
        if not await self._breaker.allow():
            return HealthStatus.UNREACHABLE
        if not self._feeds:
            return HealthStatus.DEGRADED
        try:
            await self._fetch_xml(self._feeds[0])
        except Exception:
            return HealthStatus.UNREACHABLE
        return HealthStatus.HEALTHY

    async def _fetch_feed(
        self, feed_url: str, single: bool = False
    ) -> list[SourceRecord]:
        if not await self._breaker.allow():
            return []
        await self._limiter.acquire()
        try:
            xml_text = await retry_async(self.retry, self._fetch_xml, feed_url)
        except Exception as exc:
            logger.warning("rss fetch failed for %s: %s", feed_url, exc)
            await self._breaker.record_failure()
            return []
        await self._breaker.record_success()
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("rss parse failed: %s", exc)
            return []
        records: list[SourceRecord] = []
        for entry in root.iter():
            if _strip_ns(entry.tag) != "item":
                continue
            try:
                rec = _from_entry(entry, feed_url)
            except Exception as exc:
                logger.warning("rss entry parse failed: %s", exc)
                continue
            if rec is None:
                continue
            records.append(rec)
            if single:
                return records[:1]
        return records

    async def _fetch_xml(self, url: str) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            resp = await client.get(url, headers={"User-Agent": "xninetzy-research/1.0"})
            resp.raise_for_status()
            return resp.text


register_adapter(RSSAdapter())
