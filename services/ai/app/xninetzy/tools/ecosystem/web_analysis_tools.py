from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager


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
async def web_analysis_refresh(site_slug: str = "hebat", authenticated: bool = False) -> str:
    """Refresh cache struktur situs allowlisted secara GET/HEAD-only.

    Args:
        site_slug: hebat atau mahasiswa
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
