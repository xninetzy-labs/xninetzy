from __future__ import annotations

import re
from pathlib import Path

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

ARXIV_ENDPOINT = "http://export.arxiv.org/api/query"
ARXIV_PDF_ENDPOINT = "https://arxiv.org/pdf"
CROSSREF_ENDPOINT = "https://api.crossref.org/works"

_ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


async def _fetch_text(
    url: str, params: dict | None = None, headers: dict | None = None
) -> str:
    import httpx

    async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.text


async def _fetch_json(
    url: str, params: dict | None = None, headers: dict | None = None
) -> dict:
    import json

    return json.loads(await _fetch_text(url, params, headers))


async def _fetch_bytes(url: str) -> bytes:
    import httpx

    async with httpx.AsyncClient(timeout=60, trust_env=False, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def normalize_identifier(identifier: str) -> tuple[str, str]:
    raw = (identifier or "").strip()
    if "doi.org/" in raw:
        return "doi", raw.split("doi.org/", 1)[1].strip()
    if raw.startswith("10.") and "/" in raw:
        return "doi", raw
    arxiv_url = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+)", raw)
    if arxiv_url:
        return "arxiv", arxiv_url.group(1)
    if _ARXIV_ID_PATTERN.match(raw):
        return "arxiv", raw
    return "unknown", raw


def _year_from(value: str) -> int | None:
    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None


def _crossref_year(item: dict) -> int | None:
    parts = (item.get("issued") or {}).get("date-parts") or []
    if parts and parts[0] and isinstance(parts[0][0], int):
        return parts[0][0]
    return None


def parse_arxiv_response(xml_text: str, limit: int) -> list[dict]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(xml_text, "xml")
    results: list[dict] = []
    for entry in soup.find_all("entry"):
        title = (entry.title.get_text(strip=True) if entry.title else "").strip()
        link = entry.id.get_text(strip=True) if entry.id else ""
        summary = entry.summary.get_text(strip=True) if entry.summary else ""
        published = entry.published.get_text(strip=True) if entry.published else ""
        authors = [a.get_text(strip=True) for a in entry.find_all("name")]
        pdf_link = ""
        for tag in entry.find_all("link"):
            if tag.get("title") == "pdf" or str(tag.get("type", "")) == "application/pdf":
                pdf_link = tag.get("href", "")
                break
        arxiv_id = link.rsplit("/abs/", 1)[-1] if link else ""
        if not title or not link:
            continue
        results.append(
            {
                "title": title,
                "url": link,
                "identifier": arxiv_id,
                "identifier_kind": "arxiv",
                "pdf_url": pdf_link or f"{ARXIV_PDF_ENDPOINT}/{arxiv_id}",
                "snippet": summary[:300],
                "source_type": "academic",
                "evidence_level": "abstract",
                "authors": authors,
                "year": _year_from(published),
            }
        )
        if len(results) >= limit:
            break
    return results


def parse_crossref_items(data: dict, limit: int) -> list[dict]:
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
                "identifier": doi,
                "identifier_kind": "doi",
                "snippet": (item.get("abstract", "") or "")[:300],
                "source_type": "academic",
                "evidence_level": "abstract" if item.get("abstract") else "metadata",
                "authors": [a for a in authors if a],
                "year": _crossref_year(item),
                "doi": doi,
            }
        )
    return results


async def academic_search(query: str, limit: int = 5) -> list[dict]:
    arxiv = await _arxiv_search(query, limit)
    crossref = await _crossref_search(query, limit)
    combined = arxiv + crossref
    return combined[: limit * 2]


async def _arxiv_search(query: str, limit: int) -> list[dict]:
    try:
        xml_text = await _fetch_text(
            ARXIV_ENDPOINT,
            params={"search_query": f"all:{query}", "start": 0, "max_results": limit},
        )
    except Exception as error:
        logger.warning("arXiv search failed: %s", error)
        return []
    return parse_arxiv_response(xml_text, limit)


async def _crossref_search(query: str, limit: int) -> list[dict]:
    try:
        data = await _fetch_json(
            CROSSREF_ENDPOINT,
            params={"query": query, "rows": limit},
            headers={"User-Agent": "Xninetzy-Research/1.0"},
        )
    except Exception as error:
        logger.warning("Crossref search failed: %s", error)
        return []
    return parse_crossref_items(data, limit)


async def search_papers(
    query: str, sources: str = "arxiv,crossref", max_results: int = 5
) -> list[dict]:
    chosen = {s.strip().casefold() for s in sources.split(",") if s.strip()}
    combined: list[dict] = []
    if "arxiv" in chosen:
        combined.extend(await _arxiv_search(query, max_results))
    if "crossref" in chosen:
        combined.extend(await _crossref_search(query, max_results))
    return combined[: max_results * 2]


def _parse_crossref_work(item: dict) -> dict:
    title_list = item.get("title") or []
    doi = item.get("DOI", "")
    oa_links = [
        link.get("URL", "")
        for link in item.get("link", [])
        if link.get("content-type") == "application/pdf" and link.get("URL")
    ]
    return {
        "title": title_list[0].strip() if title_list else "",
        "identifier": doi,
        "identifier_kind": "doi",
        "url": item.get("URL", "") or (f"https://doi.org/{doi}" if doi else ""),
        "container": (item.get("container-title") or [""])[0],
        "authors": [
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in item.get("author", [])
        ],
        "year": _crossref_year(item),
        "abstract": (item.get("abstract", "") or "")[:2000],
        "type": item.get("type", ""),
        "license": (item.get("license") or [{}])[0].get("URL", ""),
        "oa_pdf_urls": oa_links,
    }


async def get_paper(identifier: str, source: str = "auto") -> dict:
    kind, value = normalize_identifier(identifier)
    if source != "auto":
        kind = source.strip().casefold()
    try:
        if kind == "doi":
            data = await _fetch_json(
                f"{CROSSREF_ENDPOINT}/{value}",
                headers={"User-Agent": "Xninetzy-Research/1.0"},
            )
            paper = _parse_crossref_work(data.get("message", {}))
            paper["status"] = "ok"
            return paper
        if kind == "arxiv":
            xml_text = await _fetch_text(
                ARXIV_ENDPOINT, params={"id_list": value, "max_results": 1}
            )
            entries = parse_arxiv_response(xml_text, 1)
            if not entries:
                return {"status": "not_found", "error": f"Paper arXiv `{value}` tidak ditemukan."}
            paper = dict(entries[0])
            paper["abstract"] = paper.pop("snippet", "")
            paper["status"] = "ok"
            return paper
    except Exception as error:
        logger.warning("get_paper failed for %s: %s", identifier, error)
        return {"status": "error", "error": f"Gagal mengambil metadata: {error}"}
    return {
        "status": "invalid_identifier",
        "error": f"`{identifier}` bukan DOI atau ID arXiv yang dikenali.",
    }


def default_papers_dir() -> Path:
    from app.xninetzy.core.config import get_settings

    path = Path(get_settings().DATA_DIR) / "research" / "papers"
    path.mkdir(parents=True, exist_ok=True)
    return path


async def download_paper_pdf(
    identifier: str, source: str = "auto", save_dir: Path | None = None
) -> dict:
    paper = await get_paper(identifier, source)
    if paper.get("status") != "ok":
        return {"status": paper["status"], "error": paper.get("error", "Metadata gagal diambil.")}

    pdf_url = paper.get("pdf_url") or ""
    if not pdf_url and paper.get("oa_pdf_urls"):
        pdf_url = paper["oa_pdf_urls"][0]
    if not pdf_url:
        return {
            "status": "no_oa_pdf",
            "error": (
                "Tidak ada PDF open-access legal untuk paper ini "
                "(Sci-Hub sengaja tidak didukung). Coba akses via institusi."
            ),
            "title": paper.get("title", ""),
            "url": paper.get("url", ""),
        }

    target_dir = save_dir or default_papers_dir()
    safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", paper.get("title", "paper"))[:80]
    suffix = paper.get("identifier", "paper").replace("/", "-")
    target = target_dir / f"{safe_title or 'paper'}__{suffix}.pdf"
    try:
        content = await _fetch_bytes(pdf_url)
        target.write_bytes(content)
    except Exception as error:
        logger.warning("download_paper_pdf failed: %s", error)
        return {"status": "error", "error": f"Unduhan gagal: {error}"}

    return {
        "status": "downloaded",
        "path": str(target),
        "bytes": len(content),
        "title": paper.get("title", ""),
        "source_url": pdf_url,
    }
