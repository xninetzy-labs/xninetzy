from __future__ import annotations

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

ARXIV_ENDPOINT = "http://export.arxiv.org/api/query"
CROSSREF_ENDPOINT = "https://api.crossref.org/works"


async def academic_search(query: str, limit: int = 5) -> list[dict]:
    arxiv = await _arxiv_search(query, limit)
    crossref = await _crossref_search(query, limit)
    combined = arxiv + crossref
    return combined[: limit * 2]


async def _arxiv_search(query: str, limit: int) -> list[dict]:
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return []
    try:
        async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
            resp = await client.get(
                ARXIV_ENDPOINT,
                params={
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": limit,
                },
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "xml")
    except Exception as error:
        logger.warning("arXiv search failed: %s", error)
        return []
    results: list[dict] = []
    for entry in soup.find_all("entry"):
        title = (entry.title.get_text(strip=True) if entry.title else "").strip()
        link = entry.id.get_text(strip=True) if entry.id else ""
        summary = entry.summary.get_text(strip=True) if entry.summary else ""
        published = entry.published.get_text(strip=True) if entry.published else ""
        authors = [a.get_text(strip=True) for a in entry.find_all("name")]
        if not title or not link:
            continue
        results.append(
            {
                "title": title,
                "url": link,
                "snippet": summary[:300],
                "source_type": "academic",
                "evidence_level": "abstract",
                "authors": authors,
                "year": _year_from(published),
            }
        )
    return results[:limit]


async def _crossref_search(query: str, limit: int) -> list[dict]:
    try:
        import httpx
    except ImportError:
        return []
    try:
        async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
            resp = await client.get(
                CROSSREF_ENDPOINT,
                params={"query": query, "rows": limit},
                headers={"User-Agent": "Xninetzy-Research/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as error:
        logger.warning("Crossref search failed: %s", error)
        return []
    results: list[dict] = []
    for item in data.get("message", {}).get("items", [])[:limit]:
        title_list = item.get("title") or []
        title = title_list[0].strip() if title_list else ""
        doi = item.get("DOI", "")
        url = item.get("URL", "") or (f"https://doi.org/{doi}" if doi else "")
        if not title or not url:
            continue
        authors = [
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in item.get("author", [])
        ]
        results.append(
            {
                "title": title,
                "url": url,
                "snippet": (item.get("abstract", "") or "")[:300],
                "source_type": "academic",
                "evidence_level": "abstract" if item.get("abstract") else "metadata",
                "authors": [a for a in authors if a],
                "year": _crossref_year(item),
                "doi": doi,
            }
        )
    return results


def _year_from(value: str) -> int | None:
    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None


def _crossref_year(item: dict) -> int | None:
    parts = (item.get("issued") or {}).get("date-parts") or []
    if parts and parts[0] and isinstance(parts[0][0], int):
        return parts[0][0]
    return None
