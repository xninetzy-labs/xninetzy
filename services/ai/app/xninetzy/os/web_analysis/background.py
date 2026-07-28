from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.sites import get_site

logger = logging.getLogger(__name__)


def _configured_sites() -> list[str]:
    raw = get_settings().WEB_ANALYSIS_BACKGROUND_SITES
    sites: list[str] = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        sites.append(get_site(value).slug)
    return list(dict.fromkeys(sites))


async def run_background_refresh_once() -> list[dict]:
    """Refresh stale structural caches for this single local installation."""
    settings = get_settings()
    service = AnalyzerService()
    results: list[dict] = []
    for site_slug in _configured_sites():
        try:
            result = await service.analyze_site(
                site_slug,
                authenticated=settings.WEB_ANALYSIS_BACKGROUND_AUTHENTICATED,
            )
            results.append(result.model_dump())
            logger.info(
                "web_analysis_background site=%s status=%s",
                site_slug,
                result.status,
            )
        except Exception as exc:
            logger.warning(
                "web_analysis_background_failed site=%s error_type=%s",
                site_slug,
                type(exc).__name__,
            )
            results.append({"site_slug": site_slug, "status": "failed"})
    return results


async def web_analysis_loop() -> None:
    settings = get_settings()
    if not settings.WEB_ANALYSIS_BACKGROUND_ENABLED:
        return
    await asyncio.sleep(15)
    interval = max(5, settings.WEB_ANALYSIS_BACKGROUND_INTERVAL_MINUTES) * 60
    while True:
        await run_background_refresh_once()
        await asyncio.sleep(interval)
