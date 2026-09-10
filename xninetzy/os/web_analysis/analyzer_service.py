from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.web_analysis.cache_manager import AnalysisBusyError, AnalysisCacheManager
from app.xninetzy.os.web_analysis.models import AnalysisResult, EndpointRecord, ModuleRecord, SiteAnalysis
from app.xninetzy.os.web_analysis.security import (
    detect_human_verification,
    has_sensitive_query,
    is_safe_request_method,
    looks_like_login,
    sanitize_endpoint,
)
from app.xninetzy.os.web_analysis.selectors_registry import extract_module_structure
from app.xninetzy.os.web_analysis.session_manager import (
    SessionEncryptionUnavailable,
    SessionManager,
)
from app.xninetzy.os.web_analysis.sites import SiteDefinition, get_site, is_allowed_url

logger = logging.getLogger(__name__)

_DENIED_PATH_MARKERS = (
    "/logout",
    "/delete",
    "/remove",
    "/submit",
    "/action/",
    "/proses/",
    "editsubmission",
    "sesskey=",
)


class AnalyzerService:
    """Allowlisted, GET/HEAD-only Playwright structure analyzer.

    The analyzer never fills a field, clicks a control, solves a CAPTCHA, or
    persists visible academic values. Personal snapshots are a separate,
    encrypted concern.
    """

    def __init__(self, cache: AnalysisCacheManager | None = None) -> None:
        self.cache = cache or AnalysisCacheManager()

    async def analyze_site(
        self,
        site_slug: str,
        *,
        authenticated: bool = False,
        profile_id: str | None = None,
        force: bool = False,
    ) -> AnalysisResult:
        site = get_site(site_slug)
        settings = get_settings()
        if not settings.WEB_ANALYSIS_ENABLED:
            return AnalysisResult(
                status="configuration_required",
                site_slug=site.slug,
                auth_status="configuration_required",
                message="WEB_ANALYSIS_ENABLED=false",
            )
        cached = self.cache.load(site.slug)
        if (
            cached
            and not force
            and not self.cache.is_stale(site.slug)
            and self._cache_satisfies_request(cached, authenticated)
        ):
            return AnalysisResult(
                status="cache_fresh",
                site_slug=site.slug,
                analysis_path=str(self.cache.markdown_path(site.slug)),
                pages_analyzed=len(cached.modules),
                auth_status=cached.auth_status,
                message="Cache struktur masih fresh; crawl dilewati.",
            )

        storage_state: dict | None = None
        landing_url: str | None = None
        if authenticated:
            if not settings.WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED:
                return AnalysisResult(
                    status="configuration_required",
                    site_slug=site.slug,
                    auth_status="configuration_required",
                    message="Authenticated crawl belum diaktifkan oleh admin.",
                )
            try:
                sessions = SessionManager()
                storage_state = sessions.load_storage_state(site.slug, profile_id)
                landing_url = sessions.load_landing_url(site.slug, profile_id)
            except SessionEncryptionUnavailable as exc:
                return AnalysisResult(
                    status="configuration_required",
                    site_slug=site.slug,
                    auth_status="configuration_required",
                    message=str(exc),
                )
            if not storage_state:
                return AnalysisResult(
                    status="configuration_required",
                    site_slug=site.slug,
                    auth_status="auth_required",
                    message="Session terenkripsi belum ada; lakukan login manual lebih dulu.",
                )

        try:
            with self.cache.lease(site.slug):
                return await self._crawl(
                    site,
                    storage_state=storage_state,
                    landing_url=landing_url,
                )
        except AnalysisBusyError as exc:
            return AnalysisResult(
                status="busy",
                site_slug=site.slug,
                auth_status="authenticated" if storage_state else "public",
                message=str(exc),
            )

    async def _crawl(
        self,
        site: SiteDefinition,
        storage_state: dict | None,
        landing_url: str | None = None,
    ) -> AnalysisResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return AnalysisResult(
                status="failed",
                site_slug=site.slug,
                auth_status="error",
                message="Playwright tidak tersedia.",
            )

        settings = get_settings()
        auth_status = "authenticated" if storage_state else "public"
        page_limit = (
            settings.WEB_ANALYSIS_PORTAL_MAX_PAGES
            if site.slug in {"hebat", "mahasiswa", "qa", "uacc"}
            else settings.WEB_ANALYSIS_MAX_PAGES
        )
        seed_paths = site.authenticated_paths if storage_state else site.public_paths
        queue = []
        if storage_state and landing_url:
            queue.append(self._canonical_url(landing_url))
        login_url = self._canonical_url(site.absolute_url(site.login_path))
        for path in seed_paths:
            target = self._canonical_url(site.absolute_url(path))
            if target != login_url and target not in queue:
                queue.append(target)
        visited: set[str] = set()
        modules: dict[tuple[str, str], ModuleRecord] = {}
        endpoints: dict[tuple[str, str, tuple[str, ...]], EndpointRecord] = {}
        errors: list[str] = []
        human_verification = False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=settings.WEB_ANALYSIS_HEADLESS)
            try:
                context = await browser.new_context(storage_state=storage_state)

                async def block_mutations(route) -> None:
                    if is_safe_request_method(route.request.method):
                        await route.continue_()
                    else:
                        await route.abort("blockedbyclient")

                await context.route("**/*", block_mutations)
                page = await context.new_page()

                async def capture_response(response) -> None:
                    if not is_allowed_url(site, response.url):
                        return
                    if response.request.resource_type not in {"document", "xhr", "fetch"}:
                        return
                    try:
                        headers = await response.all_headers()
                        endpoint = sanitize_endpoint(
                            response.request.method,
                            response.url,
                            response.status,
                            headers.get("content-type"),
                        )
                        if endpoint:
                            key = (endpoint.method, endpoint.path, tuple(endpoint.query_keys))
                            endpoints[key] = endpoint
                    except Exception:
                        return

                page.on("response", capture_response)

                while queue and len(visited) < page_limit:
                    target = self._canonical_url(queue.pop(0))
                    if target in visited or not self._safe_to_visit(site, target):
                        continue
                    visited.add(target)
                    try:
                        await page.goto(
                            target,
                            wait_until="domcontentloaded",
                            timeout=settings.WEB_ANALYSIS_TIMEOUT_MS,
                        )
                        await asyncio.sleep(settings.WEB_ANALYSIS_REQUEST_DELAY_SECONDS)
                        html = await page.content()
                        current_url = page.url
                        module = extract_module_structure(current_url, html)
                        modules[(module.name, module.path)] = module

                        if detect_human_verification(html, current_url):
                            human_verification = True
                            auth_status = "human_verification_required"
                            break
                        if looks_like_login(html, current_url):
                            auth_status = "auth_required"
                            if storage_state:
                                break

                        discovered = await self._discover_links(page)
                        for link in discovered:
                            canonical = self._canonical_url(str(link))
                            if canonical not in visited and self._safe_to_visit(site, canonical):
                                queue.append(canonical)
                    except Exception as exc:
                        logger.warning(
                            "web_analysis_page_failed site=%s error_type=%s",
                            site.slug,
                            type(exc).__name__,
                        )
                        errors.append(f"Page gagal dianalisis ({type(exc).__name__}); detail sensitif tidak disimpan.")
            finally:
                await browser.close()

        now = datetime.now(timezone.utc).isoformat()
        analysis = SiteAnalysis(
            site_slug=site.slug,
            site_name=site.name,
            base_url=site.base_url,
            analyzed_at=now,
            auth_status=auth_status,
            modules=list(modules.values()),
            endpoints=list(endpoints.values()),
            protection_flags=list(site.protection_flags),
            login_notes=[
                "Session hanya berasal dari login manual owner dan disimpan terenkripsi untuk local profile.",
                "Credential, cookie, token, query value, dan isi data akademik tidak ditulis ke analisis_web.md.",
                "Saat human verification terdeteksi, crawl dihentikan tanpa solve atau retry otomatis.",
            ],
            errors=errors[:10],
        )
        path = self.cache.save(analysis)
        status = "human_verification_required" if human_verification else "completed"
        message = (
            "Human verification terdeteksi; analisis dihentikan dan butuh tindakan manual."
            if human_verification
            else "Analisis struktur read-only selesai."
        )
        return AnalysisResult(
            status=status,
            site_slug=site.slug,
            analysis_path=str(path),
            pages_analyzed=len(visited),
            auth_status=auth_status,
            message=message,
        )

    @staticmethod
    def _canonical_url(url: str) -> str:
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))

    @staticmethod
    def _cache_satisfies_request(
        cached: SiteAnalysis, authenticated: bool
    ) -> bool:
        return not authenticated or cached.auth_status == "authenticated"

    @classmethod
    async def _discover_links(cls, page) -> list[str]:
        candidates: dict[str, str] = {}
        for frame in page.frames:
            try:
                items = await frame.eval_on_selector_all(
                    "a[href], form[action]",
                    """
                    elements => elements.map(element => ({
                      href: element.href || element.action,
                      text: (element.textContent || element.getAttribute("aria-label") || "").trim().slice(0, 200),
                      method: (element.method || "GET").toUpperCase()
                    })).filter(item => item.href && item.method === "GET")
                    """,
                )
            except Exception:
                continue
            for item in items:
                href = str(item.get("href") or "")
                if href:
                    candidates[href] = str(item.get("text") or "")
        return sorted(
            candidates,
            key=lambda href: cls._link_priority(href, candidates[href]),
        )

    @staticmethod
    def _link_priority(href: str, text: str = "") -> tuple[int, str]:
        value = f"{href} {text}".casefold()
        groups = (
            ("krs", "rencana studi"),
            ("kprs",),
            ("nilai", "khs", "transkrip"),
            ("jadwal",),
            ("mata kuliah", "registrasi", "semester", "kuliah", "draft"),
            ("akademik",),
        )
        for index, keywords in enumerate(groups):
            if any(keyword in value for keyword in keywords):
                return (index, href)
        return (len(groups), href)

    @staticmethod
    def _safe_to_visit(site: SiteDefinition, url: str) -> bool:
        if not is_allowed_url(site, url):
            return False
        if has_sensitive_query(url):
            return False
        lowered = url.lower()
        return not any(marker in lowered for marker in _DENIED_PATH_MARKERS)
