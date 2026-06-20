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

    logger.info("No web search API key configured")
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


async def read_url(url: str, max_chars: int = 3000) -> str:
    """Fetch and extract text from a URL."""
    try:
        import httpx
        from bs4 import BeautifulSoup
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text("\n", strip=True)
            return text[:max_chars]
    except Exception as e:
        return f"Gagal membaca URL: {e}"
