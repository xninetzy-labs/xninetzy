from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.security import detect_human_verification, looks_like_login
from app.xninetzy.os.web_analysis.session_manager import SessionManager
from app.xninetzy.os.web_analysis.sites import get_site, is_allowed_url


async def capture_manual_session(site_slug: str, profile_id: str | None = None) -> dict[str, str]:
    """Open a headed browser and save session only after the human finishes login.

    This function never fills credentials, clicks submit, handles OTP, or solves
    CAPTCHA. It is intentionally unsuitable for unattended server execution.
    """
    from playwright.async_api import async_playwright

    site = get_site(site_slug)
    manager = SessionManager()
    existing = manager.load_storage_state(site.slug, profile_id)
    settings = get_settings()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        try:
            context = await browser.new_context(storage_state=existing)
            page = await context.new_page()
            await page.goto(
                site.absolute_url(site.login_path),
                wait_until="domcontentloaded",
                timeout=settings.WEB_ANALYSIS_TIMEOUT_MS,
            )
            print(
                "Login manual di browser yang terbuka. Selesaikan CAPTCHA/OTP sendiri. "
                "Kembali ke terminal dan tekan Enter setelah dashboard situs tampil."
            )
            await asyncio.to_thread(input)
            html = await page.content()
            if detect_human_verification(html, page.url):
                return {
                    "status": "human_verification_required",
                    "message": "Human verification masih tampil; session tidak disimpan.",
                }
            if looks_like_login(html, page.url) or not is_allowed_url(site, page.url):
                return {
                    "status": "manual_login_required",
                    "message": "Login belum terverifikasi pada origin target; session tidak disimpan.",
                }
            storage_state = await context.storage_state()
            manager.save_storage_state(site.slug, storage_state, profile_id)
            return {
                "status": "saved",
                "message": "Session terenkripsi berhasil disimpan.",
            }
        finally:
            await browser.close()
