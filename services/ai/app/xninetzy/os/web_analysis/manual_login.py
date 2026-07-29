from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.security import detect_human_verification, looks_like_login
from app.xninetzy.os.web_analysis.session_manager import (
    SessionEncryptionUnavailable,
    SessionManager,
)
from app.xninetzy.os.web_analysis.sites import get_site, is_allowed_url


async def capture_manual_session(
    site_slug: str,
    profile_id: str | None = None,
    credential_source: str | None = None,
) -> dict[str, str]:
    """Open headed login; a human handles CAPTCHA, submit, and OTP."""
    from playwright.async_api import async_playwright

    site = get_site(site_slug)
    try:
        manager = SessionManager()
        existing = manager.load_storage_state(site.slug, profile_id)
    except SessionEncryptionUnavailable:
        manager = None
        existing = None
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
            if credential_source:
                from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
                    resolve_campus_credentials,
                )

                credentials = resolve_campus_credentials(credential_source)
                username = page.locator("input[name='username']")
                password = page.locator("input[name='password']")
                if await username.count() != 1 or await password.count() != 1:
                    return {
                        "status": "login_form_changed",
                        "message": "Field username/password tidak ditemukan secara unik.",
                    }
                await username.fill(credentials.username)
                await password.fill(credentials.password.get_secret_value())
            import os
            auto_seconds = int(os.environ.get("WAIT_SECONDS") or "0")
            if auto_seconds > 0:
                print(
                    "Credential telah diprefill bila diminta. Selesaikan CAPTCHA/OTP dan submit sendiri. "
                    f"Menunggu {auto_seconds} detik... ({auto_seconds // 60}m{auto_seconds % 60:02d}s)"
                )
                await asyncio.sleep(auto_seconds)
            else:
                print(
                    "Credential telah diprefill bila diminta. Selesaikan CAPTCHA/OTP dan submit sendiri. "
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
            if manager is None:
                return {
                    "status": "verified_not_saved",
                    "message": "Login terverifikasi, tetapi session tidak disimpan karena encryption key belum tersedia.",
                }
            storage_state = await context.storage_state()
            manager.save_storage_state(site.slug, storage_state, profile_id)
            return {
                "status": "saved",
                "message": "Session terenkripsi berhasil disimpan.",
            }
        finally:
            await browser.close()
