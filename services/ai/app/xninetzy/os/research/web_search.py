from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


async def web_search(query: str, limit: int = 5) -> list[dict]:
    """Search the web via Tavily or Serper. Returns list of {title, url, snippet}."""
    s = get_settings()

    if s.TAVILY_API_KEY:
        return await _tavily_search(query, s.TAVILY_API_KEY, limit)
    if s.SERPER_API_KEY:
        return await _serper_search(query, s.SERPER_API_KEY, limit)

    fallback = await _ddgs_search(query, limit)
    if fallback:
        return fallback

    logger.info("No web search API key configured and DDGS returned nothing")
    return []


async def _tavily_search(query: str, api_key: str, limit: int) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": limit,
                      "search_depth": "basic", "include_answer": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", "?"), "url": r.get("url", ""),
                 "snippet": r.get("content", "")[:300]}
                for r in data.get("results", [])[:limit]
            ]
    except Exception as e:
        logger.warning("Tavily search failed: %s", e)
        return []


async def _serper_search(query: str, api_key: str, limit: int) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", "?"), "url": r.get("link", ""),
                 "snippet": r.get("snippet", "")[:300]}
                for r in data.get("organic", [])[:limit]
            ]
    except Exception as e:
        logger.warning("Serper search failed: %s", e)
        return []


async def _ddgs_search(query: str, limit: int) -> list[dict]:
    import asyncio

    def _run() -> list[dict]:
        try:
            from ddgs import DDGS
        except ImportError:
            logger.info("ddgs not installed; skipping free web fallback")
            return []
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=limit))
        except Exception as error:
            logger.warning("DDGS search failed: %s", error)
            return []
        return [
            {
                "title": hit.get("title", "?"),
                "url": hit.get("href", "") or hit.get("url", ""),
                "snippet": (hit.get("body", "") or "")[:300],
            }
            for hit in hits[:limit]
        ]

    return await asyncio.to_thread(_run)


async def read_url(url: str, max_chars: int = 3000) -> str:
    """Fetch and extract text from a URL."""
    from bs4 import BeautifulSoup

    from app.xninetzy.os.research.safe_fetch import safe_get

    try:
        html = await safe_get(url)
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        return f"Gagal membaca URL: {e}"
