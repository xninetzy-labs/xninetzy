from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from xninetzy.os.research.sources.base import (
    CircuitBreaker,
    RateLimit,
    RetryPolicy,
    SourceCategory,
)
from xninetzy.os.research.sources.browser_scraper import BrowserScrapingAdapter
from xninetzy.os.research.sources.browser_session import quote_url as _quote

from xninetzy.os.research.sources.registry import register_adapter


logger = logging.getLogger(__name__)


class DeallsAdapter(BrowserScrapingAdapter):
    id = "dealls"
    category = SourceCategory.COMPANY
    base_url = "https://dealls.com"
    rate_limit = RateLimit(requests_per_minute=3, burst=1)
    retry = RetryPolicy(max_attempts=2, backoff_base_seconds=2.0, backoff_max_seconds=8.0)
    circuit_breaker = CircuitBreaker(failure_threshold=3, open_duration_seconds=600.0)

    SEARCH_URL = "https://dealls.com/?searchJob=__QUERY__&curatedJobs=true"

    def build_search_url(self, query: str, **kwargs) -> str:
        return self.SEARCH_URL.replace("__QUERY__", _quote(query))

    @property
    def wait_selector(self) -> str:
        return "a[href*='/loker/']"

    def parse_jobs(self, html: str, *, query: str, limit: int) -> list:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("a[href*='/loker/']")
        records = []
        for card in cards:
            a = card if card.name == "a" else card.select_one("a[href*='/loker/']")
            if a is None:
                continue
            title_el = a.select_one("h1, h2, h3, h4, .job-title, .DeallsCardTitle")
            title = (title_el or a).get_text(strip=True)
            href = a.get("href", "")
            if not title:
                continue
            if not href or "~" not in href:
                if href in ("/loker", "/loker/") or len(href.split("/")[-1]) < 15:
                    continue
            slug = href.rstrip("/").split("/")[-1] if href else ""
            full_url = (
                f"https://dealls.com{href}" if href.startswith("/") else href
            ) or "https://dealls.com"
            company_el = card.select_one(".company-name, .DeallsCardCompany")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = card.select_one(".job-location, .DeallsCardLocation")
            location = loc_el.get_text(strip=True) if loc_el else ""
            posted_el = card.select_one(".posted-date, time")
            posted_at = posted_el.get_text(strip=True) if posted_el else None
            desc_el = card.select_one(".job-snippet, .DeallsCardDescription, p")
            snippet = (desc_el.get_text(" ", strip=True) if desc_el else "") + f" | Location: {location}"
            identifiers = {"dealls_slug": slug, "location": location}
            records.append(
                self.make_record(
                    title=title,
                    company=company,
                    url=full_url,
                    snippet=snippet,
                    posted_at=posted_at,
                    identifiers=identifiers,
                    confidence=0.5,
                )
            )
            if len(records) >= max(1, min(limit, 100)):
                break
        return records


register_adapter(DeallsAdapter())
