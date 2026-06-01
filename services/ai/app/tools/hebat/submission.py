from __future__ import annotations

import asyncio
import secrets
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logging
from app.tools.hebat.models import EditSubmissionFields, UploadStatus
from app.tools.hebat.parsers import parse_assignment_page, parse_edit_submission_page
from app.tools.hebat.storage import (
    audit_log,
    create_submission,
    get_assignment_by_activity,
    get_submission_by_token,
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
    from app.tools.hebat.browser_session import _storage_state_path

    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        return {"status": "failed", "error": "Session tidak ditemukan — login dulu", "verification_text": None}

    update_submission_status(token, UploadStatus.UPLOADING)
    audit_log(chat_id, "upload_start", "started", target_type="submission", target_id=token)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(storage_state=str(storage_path))
            page = await ctx.new_page()

            # Go to assignment page
            await page.goto(assignment_url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            # Click Add/Edit submission
            add_btn = await page.query_selector("button:has-text('Add submission'), button:has-text('Edit submission')")
            if not add_btn:
                form = await page.query_selector("form[action*='mod/assign']")
                if form:
                    await form.evaluate("el => el.submit()")
                else:
                    return {"status": "failed", "error": "Tombol Add submission tidak ditemukan", "verification_text": None}
            else:
                await add_btn.click()

            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            # Try to upload via file chooser
            upload_success = False
            try:
                async with page.expect_file_chooser(timeout=5_000) as fc_info:
                    upload_trigger = await page.query_selector(
                        "a.fp-btn-add, button.fp-btn-add, input[type='file'], .yui3-moodledialog-hd a"
                    )
                    if upload_trigger:
                        await upload_trigger.click()
                    else:
                        # Try clicking any "Upload" or "Add" link in the filemanager
                        await page.click(".fp-btn-add, .yui3-button:has-text('Upload')", timeout=3_000)

                file_chooser = await fc_info.value
                await file_chooser.set_files(local_file_path)
                upload_success = True
                await asyncio.sleep(1)

            except Exception as e:
                logger.warning("File chooser approach failed: %s — trying direct input", e)

            # Fallback: find hidden file input and set directly
            if not upload_success:
                file_input = await page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(local_file_path)
                    upload_success = True
                    await asyncio.sleep(1)

            if not upload_success:
                return {"status": "failed", "error": "Tidak bisa menemukan file upload widget", "verification_text": None}

            # Submit the form (Save changes)
            save_btn = await page.query_selector(
                "input[type='submit'][value*='Save'], button:has-text('Save changes')"
            )
            if save_btn:
                await save_btn.click()
            else:
                await page.evaluate("document.querySelector('form').submit()")

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
