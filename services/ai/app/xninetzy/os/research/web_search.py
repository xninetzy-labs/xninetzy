from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


async def web_search(query: str, limit: int = 5) -> list[dict]:
    s = get_settings()
    policy = (s.WEB_SEARCH_PROVIDER or "hybrid").strip().lower()
    calls = []
    if policy in {"hybrid", "auto", "tavily"} and s.TAVILY_API_KEY:
        calls.append(("tavily", _tavily_search(query, s.TAVILY_API_KEY, limit)))
    if policy in {"hybrid", "auto", "serper"} and s.SERPER_API_KEY:
        calls.append(("serper", _serper_search(query, s.SERPER_API_KEY, limit)))
    if policy in {"hybrid", "auto", "searxng"} and s.SEARXNG_BASE_URL:
        calls.append(("searxng", _searxng_search(query, s.SEARXNG_BASE_URL, limit)))
    if policy in {"hybrid", "auto", "open", "ddgs", "tavily", "serper"}:
        calls.append(("ddgs", _ddgs_search(query, limit)))
    if not calls:
        calls.append(("ddgs", _ddgs_search(query, limit)))
    results = await asyncio.gather(*(call for _, call in calls), return_exceptions=True)
    merged: list[dict] = []
    for (provider, _), provider_results in zip(calls, results, strict=True):
        if isinstance(provider_results, Exception):
            logger.warning("%s search failed: %s", provider, provider_results)
            continue
        for rank, result in enumerate(provider_results, 1):
            merged.append({**result, "provider": result.get("provider") or provider, "providers": list(dict.fromkeys([*(result.get("providers") or []), provider])), "raw_rank": result.get("raw_rank") or rank, "source_type": result.get("source_type") or "web", "evidence_level": result.get("evidence_level") or "snippet"})
    return _fuse_results(merged, limit)


def _fuse_results(results: list[dict], limit: int) -> list[dict]:
    fused: dict[str, dict] = {}
    for result in results:
        key = str(result.get("url") or result.get("video_id") or result.get("title") or "").rstrip("/").lower()
        if not key:
            continue
        current = fused.get(key)
        if current is None:
            fused[key] = {**result, "canonical_url": key, "fusion_score": 1 / (60 + int(result.get("raw_rank") or 1))}
            continue
        providers = [*(current.get("providers") or []), *(result.get("providers") or []), result.get("provider", "")]
        current["providers"] = list(dict.fromkeys(provider for provider in providers if provider))
        current["fusion_score"] = float(current.get("fusion_score") or 0) + 1 / (60 + int(result.get("raw_rank") or 1))
    ranked = list(fused.values())
    ranked.sort(key=lambda item: (-float(item.get("fusion_score") or 0), str(item.get("title") or "")))
    return ranked[: max(1, limit)]


async def _tavily_search(query: str, api_key: str, limit: int) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=get_settings().RESEARCH_PROVIDER_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": limit,
                      "search_depth": "basic", "include_answer": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", "?"), "url": r.get("url", ""), "snippet": r.get("content", "")[:500], "provider": "tavily"}
                for r in data.get("results", [])[:limit]
            ]
    except Exception as e:
        logger.warning("Tavily search failed: %s", e)
        return []


async def _serper_search(query: str, api_key: str, limit: int) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=get_settings().RESEARCH_PROVIDER_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", "?"), "url": r.get("link", ""), "snippet": r.get("snippet", "")[:500], "provider": "serper"}
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
                "snippet": (hit.get("body", "") or "")[:500], "provider": "ddgs",
            }
            for hit in hits[:limit]
        ]

    return await asyncio.to_thread(_run)


async def _searxng_search(query: str, base_url: str, limit: int) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=get_settings().RESEARCH_PROVIDER_TIMEOUT_SECONDS, trust_env=False) as client:
            response = await client.get(f"{base_url.rstrip('/')}/search", params={"q": query, "format": "json", "categories": "general"})
            response.raise_for_status()
            payload = response.json()
    except Exception as error:
        logger.warning("SearXNG search failed: %s", error)
        return []
    return [{"title": item.get("title", "?"), "url": item.get("url", ""), "snippet": (item.get("content", "") or "")[:500], "provider": "searxng"} for item in payload.get("results", [])[:limit] if item.get("url")]


def research_capabilities() -> dict:
    settings = get_settings()
    return {"policy": (settings.WEB_SEARCH_PROVIDER or "hybrid").strip().lower(), "providers": {"ddgs": {"configured": True, "source": "open"}, "searxng": {"configured": bool(settings.SEARXNG_BASE_URL), "source": "open"}, "tavily": {"configured": bool(settings.TAVILY_API_KEY), "source": "paid"}, "serper": {"configured": bool(settings.SERPER_API_KEY), "source": "paid"}, "youtube": {"configured": bool(settings.YOUTUBE_API_KEY), "source": "paid_quota"}, "arxiv": {"configured": True, "source": "open"}, "crossref": {"configured": True, "source": "open"}}}


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
