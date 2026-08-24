from __future__ import annotations

import asyncio
import secrets

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.models import UploadStatus
from app.xninetzy.os.academic.hebat.parsers import (
    is_logged_out,
    parse_assignment_page,
)
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


async def _open_healed_page(browser, chat_id: str, url: str) -> tuple[object, str | None]:
    """Open ``url`` with stored cookies, healing an expired session once."""
    from app.xninetzy.os.academic.hebat.browser_session import (
        _storage_state_path,
        relogin_hebat,
    )

    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        return None, "Session tidak ditemukan — login dulu"

    rate_limit = get_settings().HEBAT_RATE_LIMIT_SECONDS
    for attempt in (1, 2):
        ctx = await browser.new_context(storage_state=str(storage_path))
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(rate_limit)
        html = await page.content()
        if not is_logged_out(html):
            return page, None
        await ctx.close()
        if attempt == 1 and not await relogin_hebat(chat_id):
            return None, "Session HEBAT kedaluwarsa dan relogin gagal — jalankan login HEBAT dulu"
    return None, "Session HEBAT tetap kedaluwarsa setelah relogin — login ulang manual"


def _classify_upload(parsed: dict) -> tuple[bool, str | None]:
    """Decide upload outcome from the parsed post-save page; never fake success."""
    status = (parsed.get("submission_status") or "").strip()
    lowered = status.lower()
    verification = (
        f"Submission status: {parsed.get('submission_status', '?')}\n"
        f"Last modified: {parsed.get('last_modified', '?')}"
    )
    if not status:
        return False, "Tidak bisa memverifikasi status submission setelah upload"
    if "no submission" in lowered or "not submitted" in lowered or lowered.startswith("draft"):
        return False, f"File belum terkirim final menurut HEBAT. Status: {status}"
    if "submitted" in lowered:
        return True, verification
    return False, f"Status submission tidak dikenal setelah upload: {status}"


def _classify_removal(parsed: dict) -> tuple[bool, str]:
    status = (parsed.get("submission_status") or "").strip()
    verification = f"Submission status: {status or 'No submissions have been made yet'}"
    if status and "no submission" in status.lower():
        return True, verification
    return False, f"Status submission masih terbaca: {status or 'tidak terbaca'}"


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
            page, session_error = await _open_healed_page(browser, chat_id, assignment_url)
            if page is None:
                return failed_result(session_error or "Session HEBAT tidak tersedia")

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
                    return failed_result(
                        "Tombol Add submission tidak ditemukan — pastikan tugas "
                        "tersebut menerima upload file dan sesi masih berlaku"
                    )
                await form.evaluate("el => el.submit()")

            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await page.locator(".filemanager").last.wait_for(
                state="visible",
                timeout=30_000,
            )
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            file_manager = page.locator(".filemanager:visible").last
            direct_input = file_manager.locator("input[type='file']").last
            file_input = direct_input
            try:
                await direct_input.wait_for(state="attached", timeout=5_000)
            except Exception:
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
                try:
                    await dialog_file_input.wait_for(
                        state="attached",
                        timeout=15_000,
                    )
                except Exception:
                    return failed_result("Dialog file picker tidak muncul")
                file_input = dialog_file_input

            await file_input.set_input_files(local_file_path)
            await page.wait_for_timeout(500)
            upload_dialog = page.locator(
                ".moodle-dialogue-base[aria-hidden='false']"
            ).last
            upload_button = upload_dialog.get_by_role(
                "button", name="Upload this file", exact=True
            )
            try:
                await upload_button.wait_for(state="visible", timeout=15_000)
            except Exception:
                return failed_result("Dialog Upload this file tidak ditemukan")
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

            await page.goto(assignment_url, wait_until="domcontentloaded", timeout=20_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            html_after = await page.content()
            parsed = parse_assignment_page(html_after)

            uploaded, outcome = _classify_upload(parsed)
            if not uploaded:
                return failed_result(outcome or "Verifikasi upload gagal")

            audit_log(chat_id, "upload_complete", "success",
                      target_type="submission", target_id=token,
                      detail={"submission_status": parsed.get("submission_status")})
            update_submission_status(token, UploadStatus.UPLOADED, verification_text=outcome)

            return {"status": "uploaded", "verification_text": outcome, "error": None}

        except Exception as e:
            logger.error("Upload failed for token=%s: %s", token, e)
            update_submission_status(token, UploadStatus.FAILED, error=str(e))
            audit_log(chat_id, "upload_failed", "failed",
                      target_type="submission", target_id=token,
                      detail={"error": str(e)})
            return {"status": "failed", "error": str(e), "verification_text": None}
        finally:
            await browser.close()


async def remove_submission_via_playwright(
    chat_id: str,
    assignment_url: str,
    token: str,
) -> dict:
    """
    Remove an existing Moodle assignment submission using Playwright.
    Flow: click "Remove submission" -> confirm page -> click "Continue".
    Returns {status, verification_text, error}.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return {"status": "failed", "error": "Playwright tidak tersedia", "verification_text": None}

    s = get_settings()
    update_submission_status(token, UploadStatus.UPLOADING)
    audit_log(chat_id, "remove_start", "started", target_type="submission", target_id=token)

    def failed_result(message: str) -> dict:
        update_submission_status(token, UploadStatus.FAILED, error=message)
        audit_log(
            chat_id,
            "remove_failed",
            "failed",
            target_type="submission",
            target_id=token,
            detail={"error": message},
        )
        return {"status": "failed", "error": message, "verification_text": None}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page, session_error = await _open_healed_page(browser, chat_id, assignment_url)
            if page is None:
                return failed_result(session_error or "Session HEBAT tidak tersedia")

            remove_selector = "button:has-text('Remove submission')"
            try:
                remove_btn = await page.wait_for_selector(
                    remove_selector, state="visible", timeout=30_000
                )
                await remove_btn.click(timeout=15_000)
            except Exception:
                return failed_result(
                    "Tombol Remove submission tidak ditemukan — mungkin belum ada submission."
                )

            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            confirm_selector = (
                "button:has-text('Continue'), "
                "button:has-text('Yes'), "
                "input[type='submit'][value*='Continue'], "
                "input[type='submit'][value*='Yes'], "
                "form[action*='removesubmission'] button[type='submit']"
            )
            try:
                confirm_btn = await page.wait_for_selector(
                    confirm_selector, state="visible", timeout=20_000
                )
                await confirm_btn.click(timeout=15_000)
            except Exception:
                form = await page.wait_for_selector(
                    "form[action*='removesubmission']", state="visible", timeout=5_000
                )
                await form.evaluate("el => el.submit()")

            await page.wait_for_load_state("domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            await page.goto(assignment_url, wait_until="domcontentloaded", timeout=20_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            html_after = await page.content()
            parsed = parse_assignment_page(html_after)

            removed, outcome = _classify_removal(parsed)
            if not removed:
                return failed_result(outcome or "Verifikasi penghapusan gagal")

            audit_log(chat_id, "remove_complete", "success",
                      target_type="submission", target_id=token,
                      detail={"submission_status": parsed.get("submission_status")})
            update_submission_status(token, UploadStatus.REMOVED, verification_text=outcome)
            return {"status": "removed", "verification_text": outcome, "error": None}

        except Exception as e:
            logger.error("Remove failed for token=%s: %s", token, e)
            update_submission_status(token, UploadStatus.FAILED, error=str(e))
            audit_log(chat_id, "remove_failed", "failed",
                      target_type="submission", target_id=token,
                      detail={"error": str(e)})
            return {"status": "failed", "error": str(e), "verification_text": None}
        finally:
            await browser.close()
