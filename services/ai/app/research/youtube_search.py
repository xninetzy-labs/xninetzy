from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import logging

logger = logging.getLogger(__name__)


async def youtube_search(query: str, limit: int = 5) -> list[dict]:
    """Search YouTube. Returns list of {title, video_id, url, channel, description}."""
    s = get_settings()
    if not s.YOUTUBE_API_KEY:
        return []

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": s.YOUTUBE_API_KEY,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": limit,
                    "relevanceLanguage": "id",
                    "order": "relevance",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("items", []):
                vid_id = item["id"].get("videoId", "")
                snippet = item.get("snippet", {})
                results.append({
                    "title": snippet.get("title", "?"),
                    "video_id": vid_id,
                    "url": f"https://youtube.com/watch?v={vid_id}",
                    "channel": snippet.get("channelTitle", "?"),
                    "description": snippet.get("description", "")[:200],
                    "published_at": snippet.get("publishedAt", ""),
                })
            return results
    except Exception as e:
        logger.warning("YouTube search failed: %s", e)
        return []
