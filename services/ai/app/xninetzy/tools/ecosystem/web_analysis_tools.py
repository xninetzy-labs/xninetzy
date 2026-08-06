from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager
from app.xninetzy.os.web_analysis.security import detect_human_verification
from app.xninetzy.os.web_analysis.sites import _canonical_seed_url, get_site


@tool
def web_analysis_status(site_slug: str = "hebat") -> str:
    """Lihat status cache struktur situs akademik lokal tanpa melakukan crawl."""
    cache = AnalysisCacheManager()
    analysis = cache.load(site_slug)
    if not analysis:
        return f"Belum ada cache analisis untuk `{site_slug}`."
    modules = ", ".join(sorted({module.name for module in analysis.modules})) or "-"
    return (
        f"*Web Analysis: {analysis.site_name}*\n"
        f"• Auth status: {analysis.auth_status}\n"
        f"• Dianalisis: {analysis.analyzed_at}\n"
        f"• Modul: {modules}\n"
        f"• Cache stale: {'ya' if cache.is_stale(site_slug) else 'tidak'}\n"
        "• Cache struktur tidak memuat credential/cookie/data akademik."
    )


@tool
def web_analysis_catalog(site_slug: str = "hebat") -> str:
    """Tampilkan seluruh seed route read-only yang akan dianalisis per portal."""
    site = get_site(site_slug)
    lines = [
        f"*Web Analysis Catalog: {site.name}*",
        f"• Host: `{site.hostname}`",
        "• Public routes:",
    ]
    lines.extend(f"  - `{path}`" for path in site.public_paths)
    lines.append("• Authenticated routes:")
    lines.extend(f"  - `{path}`" for path in site.authenticated_paths)
    lines.append("• Policy: GET/HEAD-only; mutation and human verification tetap diblokir.")
    return "\n".join(lines)


@tool
async def web_analysis_refresh(site_slug: str = "hebat", authenticated: bool = False) -> str:
    """Refresh cache struktur situs allowlisted secara GET/HEAD-only.

    Args:
        site_slug: hebat, mahasiswa, atau qa
        authenticated: gunakan session manual local-owner; default false
    """
    result = await AnalyzerService().analyze_site(
        site_slug,
        authenticated=authenticated,
        force=True,
    )
    return (
        f"*Web Analysis {result.site_slug}*\n"
        f"• Status: {result.status}\n"
        f"• Auth: {result.auth_status}\n"
        f"• Halaman: {result.pages_analyzed}\n"
        f"• Pesan: {result.message}"
    )


@tool
async def web_discover(
    source_url: str,
    depth: int = 1,
    max_pages: int = 10,
    ingest_to_knowledge: bool = False,
    capture_visual: bool = False,
) -> str:
    """Jelajahi URL HTTPS publik secara bounded dan simpan evidence terpilih.

    Discovery hanya memakai GET/HEAD, memblokir mutation, berhenti saat human
    verification terdeteksi, dan menjaga host tetap sama dengan URL awal.
    Knowledge ingestion dan capture visual harus diminta eksplisit.
    """
    from app.xninetzy.os.web_analysis.discovery import WebDiscoveryService

    result = await WebDiscoveryService().discover(
        source_url,
        depth=depth,
        max_pages=max_pages,
        ingest_to_knowledge=ingest_to_knowledge,
        capture_visual=capture_visual,
    )
    lines = [
        "*Web Discovery*",
        f"• Status: {result.status}",
        f"• Source: {result.source_url}",
        f"• Halaman: {len(result.pages)} | Link: {result.links}",
        f"• Graph: {result.graph_nodes} node / {result.graph_edges} edge",
        f"• Knowledge baru: {result.knowledge_sources}",
        f"• Human verification: {'ya' if result.human_verification else 'tidak'}",
    ]
    if result.captures:
        lines.append(f"• PixelRAG capture: {len(result.captures)}")
    if result.errors:
        lines.append(f"• Error aman: {', '.join(result.errors[:3])}")
    return "\n".join(lines)


@tool
async def web_fetch(url: str, max_chars: int = 8000) -> str:
    """Ambil konten teks satu URL HTTPS publik secara bounded (GET-only).

    Args:
        url: URL HTTPS publik lengkap
        max_chars: batas karakter teks yang dikembalikan (500-20000)
    """
    if max_chars < 500 or max_chars > 20000:
        raise ValueError("max_chars harus berada di antara 500 dan 20000.")
    canonical, _hostname, _port = _canonical_seed_url(url)
    settings = get_settings()
    timeout = settings.WEB_ANALYSIS_TIMEOUT_MS / 1000
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": "Xninetzy-WebFetch/1.0 (read-only)"},
    ) as client:
        response = await client.get(canonical)
    if response.status_code >= 400:
        return (
            f"*Web Fetch*\n"
            f"• URL: {canonical}\n"
            f"• Status: {response.status_code}\n"
            "• Tidak ada konten."
        )
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.casefold():
        return (
            f"*Web Fetch*\n"
            f"• URL: {canonical}\n"
            f"• Tipe: {content_type or 'unknown'}\n"
            "• Konten non-HTML tidak diambil."
        )
    html = response.text
    if detect_human_verification(html, canonical):
        return (
            f"*Web Fetch*\n"
            f"• URL: {canonical}\n"
            "• Human verification terdeteksi; konten tidak diambil."
        )
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return f"*Web Fetch*\n• URL: {canonical}\n• Status: {response.status_code}\n\n{text}"
