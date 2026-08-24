from __future__ import annotations

import asyncio
import time

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.notifications.admin_notifier import notify_admin
from app.xninetzy.os.web_analysis.session_manager import (
    SessionEncryptionUnavailable,
    SessionManager,
)

logger = logging.getLogger(__name__)

MIN_LOOP_INTERVAL_SECONDS = 300
MIN_NOTIFY_COOLDOWN_SECONDS = 600

WATCHED_SITES: tuple[tuple[str, str, str, str], ...] = (
    ("mahasiswa", "Cyber Campus", "/cyber-login", "CYBER_CAMPUS_ENABLED"),
    ("uacc", "UACC SSO", "/uacc-login", "UACC_ENABLED"),
)

_last_notified_at: dict[str, float] = {}


def evaluate_session_health(info: dict, stale_after_seconds: int) -> str:
    if not info.get("exists"):
        return "missing"
    age = info.get("age_seconds")
    if age is None:
        return "unknown_age"
    if age > stale_after_seconds:
        return "stale"
    return "fresh"


def format_session_age(age_seconds: int | None) -> str:
    if age_seconds is None:
        return "tidak diketahui"
    hours = age_seconds // 3600
    minutes = (age_seconds % 3600) // 60
    if hours >= 1:
        return f"{hours} jam {minutes} menit"
    return f"{minutes} menit"


def build_watchdog_message(
    label: str,
    status: str,
    command: str,
    age_seconds: int | None,
) -> str:
    if status == "missing":
        reason = "session belum ada"
    elif status == "stale":
        reason = "session sudah melewati batas umur"
    else:
        reason = "umur session tidak dapat dibaca"
    return (
        f"*Session {label} perlu login ulang*\n\n"
        f"• Status: {reason}\n"
        f"• Umur session: {format_session_age(age_seconds)}\n\n"
        f"Balas dengan `{command}` untuk mulai login. "
        "CAPTCHA akan dikirim ke chat ini dan dijawab manual oleh Anda."
    )


async def _notify_once(key: str, text: str, cooldown_seconds: int) -> bool:
    now = time.monotonic()
    last = _last_notified_at.get(key)
    if last is not None and now - last < cooldown_seconds:
        return False
    delivered = await notify_admin("academic_session_watchdog", {"text": text})
    if delivered:
        _last_notified_at[key] = now
    return bool(delivered)


async def run_session_watchdog() -> list[str]:
    settings = get_settings()
    try:
        manager = SessionManager()
    except SessionEncryptionUnavailable as exc:
        logger.info("Session watchdog idle: %s", exc)
        return []
    stale_after_seconds = max(1, settings.ACADEMIC_SESSION_STALE_HOURS * 3600)
    cooldown_seconds = max(
        MIN_NOTIFY_COOLDOWN_SECONDS,
        settings.ACADEMIC_SESSION_WATCHDOG_NOTIFY_COOLDOWN_HOURS * 3600,
    )
    notified: list[str] = []
    for site_slug, label, command, enabled_setting in WATCHED_SITES:
        if not getattr(settings, enabled_setting, False):
            continue
        info = manager.session_info(site_slug)
        status = evaluate_session_health(info, stale_after_seconds)
        if status == "fresh":
            continue
        message = build_watchdog_message(
            label, status, command, info.get("age_seconds")
        )
        if await _notify_once(f"{site_slug}:{status}", message, cooldown_seconds):
            notified.append(f"{site_slug}:{status}")
    return notified


async def session_watchdog_loop() -> None:
    settings = get_settings()
    interval = max(
        MIN_LOOP_INTERVAL_SECONDS,
        settings.ACADEMIC_SESSION_WATCHDOG_INTERVAL_SECONDS,
    )
    while True:
        try:
            await run_session_watchdog()
        except Exception as exc:
            logger.error("Session watchdog loop failed: %s", exc)
        await asyncio.sleep(interval)
