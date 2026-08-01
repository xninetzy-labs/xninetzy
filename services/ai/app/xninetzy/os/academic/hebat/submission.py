from __future__ import annotations

import asyncio
import secrets

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.models import UploadStatus
from app.xninetzy.os.academic.hebat.parsers import parse_assignment_page
from app.xninetzy.os.academic.hebat.storage import (
    audit_log,
    update_submission_status,
)

logger = logging.getLogger(__name__)

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


def generate_token() -> str:
    return "HBT-" + secrets.token_hex(3).upper()


async def upload_submission_via_playwright(
    chat_id: str,
    assignment_url: str,
    local_file_path: str,
    token: str,
) -> dict:
    """
    Upload a file to a Moodle assignment using Playwright.
    Returns {status, verification_text, error}.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return {"status": "failed", "error": "Playwright tidak tersedia", "verification_text": None}

    s = get_settings()
    from app.xninetzy.os.academic.hebat.browser_session import _storage_state_path

    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        return {"status": "failed", "error": "Session tidak ditemukan — login dulu", "verification_text": None}

    update_submission_status(token, UploadStatus.UPLOADING)
    audit_log(chat_id, "upload_start", "started", target_type="submission", target_id=token)

    def failed_result(message: str) -> dict:
        update_submission_status(token, UploadStatus.FAILED, error=message)
        audit_log(
            chat_id,
            "upload_failed",
            "failed",
            target_type="submission",
            target_id=token,
            detail={"error": message},
        )
        return {"status": "failed", "error": message, "verification_text": None}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(storage_state=str(storage_path))
            page = await ctx.new_page()

            # Go to assignment page
            await page.goto(assignment_url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            add_selector = (
                "button:has-text('Add submission'), "
                "button:has-text('Edit submission')"
            )
            try:
                add_btn = await page.wait_for_selector(
                    add_selector,
                    state="visible",
                    timeout=30_000,
                )
                await add_btn.click(timeout=15_000)
            except Exception:
                try:
                    form = await page.wait_for_selector(
                        "form[action*='mod/assign']",
                        state="visible",
                        timeout=5_000,
                    )
                except Exception:
                    return failed_result("Tombol Add submission tidak ditemukan")
                await form.evaluate("el => el.submit()")

            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await page.locator(".filemanager").last.wait_for(
                state="visible",
                timeout=30_000,
            )
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            file_manager = page.locator(".filemanager:visible").last
            file_input = file_manager.locator("input[type='file']").last
            if await file_input.count() == 0:
                add_links = file_manager.locator(
                    ".fp-btn-add a[title='Add...']:visible"
                )
                try:
                    await add_links.first.wait_for(
                        state="visible",
                        timeout=30_000,
                    )
                except Exception:
                    return failed_result(
                        "File manager sudah berisi file atau kontrol Add belum tersedia; "
                        "upload pengganti memerlukan penghapusan/approval eksplisit."
                    )
                await add_links.first.click(timeout=15_000)
                dialog_file_input = page.locator(
                    ".moodle-dialogue-base[aria-hidden='false'] "
                    "input[type='file']"
                ).last
                await dialog_file_input.wait_for(
                    state="attached",
                    timeout=15_000,
                )
                file_input = dialog_file_input

            if await file_input.count() != 1:
                return failed_result("Tidak bisa menemukan file upload widget")

            await file_input.set_input_files(local_file_path)
            await page.wait_for_timeout(500)
            upload_dialog = page.locator(
                ".moodle-dialogue-base[aria-hidden='false']"
            ).last
            upload_button = upload_dialog.get_by_role(
                "button", name="Upload this file", exact=True
            )
            if await upload_button.count() != 1:
                return failed_result("Dialog Upload this file tidak ditemukan")
            await upload_button.wait_for(state="visible", timeout=15_000)
            await upload_button.click(force=True, timeout=15_000)
            try:
                await upload_dialog.wait_for(state="hidden", timeout=15_000)
            except Exception:
                await page.wait_for_timeout(1000)

            save_selector = (
                "input[type='submit'][value*='Save'], "
                "button:has-text('Save changes')"
            )
            try:
                save_btn = await page.wait_for_selector(
                    save_selector,
                    state="visible",
                    timeout=30_000,
                )
                await save_btn.click(timeout=15_000)
            except Exception:
                form = await page.wait_for_selector(
                    "form[action*='mod/assign']",
                    state="visible",
                    timeout=5_000,
                )
                await form.evaluate("el => el.submit()")

            await page.wait_for_load_state("domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            # Re-open assignment page to verify
            await page.goto(assignment_url, wait_until="domcontentloaded", timeout=20_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            html_after = await page.content()
            parsed = parse_assignment_page(html_after)

            verification = (
                f"Submission status: {parsed.get('submission_status', '?')}\n"
                f"Last modified: {parsed.get('last_modified', '?')}"
            )
            update_submission_status(token, UploadStatus.UPLOADED, verification_text=verification)
            audit_log(chat_id, "upload_complete", "success",
                      target_type="submission", target_id=token,
                      detail={"submission_status": parsed.get("submission_status")})

            return {"status": "uploaded", "verification_text": verification, "error": None}

        except Exception as e:
            logger.error("Upload failed for token=%s: %s", token, e)
            update_submission_status(token, UploadStatus.FAILED, error=str(e))
            audit_log(chat_id, "upload_failed", "failed",
                      target_type="submission", target_id=token,
                      detail={"error": str(e)})
            return {"status": "failed", "error": str(e), "verification_text": None}
        finally:
            await browser.close()
