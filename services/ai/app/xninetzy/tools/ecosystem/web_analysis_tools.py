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
