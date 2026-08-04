from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.identity import normalize_whatsapp_jid
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    LOGIN_COORDINATOR,
    CampusLoginError,
)
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    AcademicPortalReadError,
    PORTAL_READ_FETCH_SCRIPT,
    parse_current_krs_html,
)
from app.xninetzy.os.notifications.admin_notifier import admin_jid, notify_admin
from app.xninetzy.os.web_analysis.security import looks_like_login
from app.xninetzy.os.web_analysis.session_manager import SessionManager

logger = logging.getLogger(__name__)

OWNER_SCOPE = "local-owner"
DEFAULT_INTERVAL_SECONDS = 600
WINDOW_INTERVAL_SECONDS = 60
_ANNOUNCEMENT_RE = re.compile(
    r"di mulai tanggal\s+(\d{2}-\d{2}-\d{4})\s*-\s*(\d{2}-\d{2}-\d{4})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"(\d{2})-(\d{2})-(\d{4})")
_KPRS_CLOSED_RE = re.compile(r"belum\s+(?:di\s+)?buka", re.IGNORECASE)
_KPRS_OPEN_MARKERS = (
    "penawaran",
    "pilih kelas",
    "ambil kelas",
    "daftar kelas",
    "kode kelas",
)


@dataclass(frozen=True, slots=True)
class KrsAnnouncement:
    period_start: str
    period_end: str

    def contains(self, now: datetime) -> bool:
        return self.period_start <= now.date().isoformat() <= self.period_end


@dataclass(frozen=True, slots=True)
class KrsWatchSignal:
    announcement: KrsAnnouncement | None
    mk_count: int
    fingerprint: str
    kprs_opened: bool | None = None


def _normalize_date(value: str) -> str:
    day, month, year = _DATE_RE.fullmatch(value).groups()
    return f"{year}-{month}-{day}"


def parse_kprs_status(text: str) -> bool | None:
    lowered = (text or "").lower()
    if _KPRS_CLOSED_RE.search(lowered):
        return False
    if any(marker in lowered for marker in _KPRS_OPEN_MARKERS):
        return True
    return None


def parse_krs_announcement(text: str) -> KrsAnnouncement | None:
    match = _ANNOUNCEMENT_RE.search(text or "")
    if not match:
        return None
    try:
        return KrsAnnouncement(
            period_start=_normalize_date(match.group(1)),
            period_end=_normalize_date(match.group(2)),
        )
    except (AttributeError, ValueError):
        return None


def krs_fingerprint(
    announcement: KrsAnnouncement | None,
    mk_codes: tuple[str, ...],
    kprs_opened: bool | None = None,
) -> str:
    payload = {
        "announcement": (
            {"start": announcement.period_start, "end": announcement.period_end}
            if announcement
            else None
        ),
        "mk": sorted(mk_codes),
        "kprs_opened": kprs_opened,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class KrsWatcherStore:
    def __init__(self, owner_scope: str = OWNER_SCOPE) -> None:
        self.owner_scope = owner_scope

    def get(self) -> dict:
        default_interval = max(
            5,
            int(get_settings().KRS_WATCHER_DEFAULT_INTERVAL_SECONDS),
        )
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM krs_watcher_state WHERE owner_scope = ?",
                (self.owner_scope,),
            ).fetchone()
        if row is None:
            return {
                "enabled": 0,
                "interval_seconds": default_interval,
                "started_at": None,
                "last_tick_at": None,
                "last_fingerprint": None,
                "last_notified_fingerprint": None,
                "last_announcement": None,
                "last_mk_count": 0,
                "last_status": "idle",
                "last_error": None,
                "session_expired_notified": 0,
            }
        return dict(row)

    def set_enabled(self, enabled: bool, interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> None:
        interval_seconds = max(5, min(int(interval_seconds), 3600))
        now = datetime.now(UTC).isoformat()
        with connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO krs_watcher_state(
                    owner_scope, enabled, interval_seconds, started_at,
                    last_status, session_expired_notified, updated_at
                ) VALUES(?,0,?,NULL,'idle',0,?)
                """,
                (self.owner_scope, interval_seconds, now),
            )
            if enabled:
                conn.execute(
                    """
                    UPDATE krs_watcher_state
                    SET enabled = 1, interval_seconds = ?, started_at = ?,
                        session_expired_notified = 0, updated_at = ?
                    WHERE owner_scope = ?
                    """,
                    (interval_seconds, now, now, self.owner_scope),
                )
            else:
                conn.execute(
                    """
                    UPDATE krs_watcher_state
                    SET enabled = 0, started_at = NULL,
                        session_expired_notified = 0, updated_at = ?
                    WHERE owner_scope = ?
                    """,
                    (now, self.owner_scope),
                )

    def update_tick(
        self,
        *,
        fingerprint: str | None,
        announcement: str | None,
        mk_count: int,
        status: str,
        error: str | None = None,
        notified_fingerprint: str | None = None,
        session_expired_notified: int | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with connect() as conn:
            conn.execute(
                """
                UPDATE krs_watcher_state
                SET last_tick_at = ?, last_fingerprint = ?, last_announcement = ?,
                    last_mk_count = ?, last_status = ?, last_error = ?,
                    last_notified_fingerprint = COALESCE(?, last_notified_fingerprint),
                    session_expired_notified = COALESCE(?, session_expired_notified),
                    updated_at = ?
                WHERE owner_scope = ?
                """,
                (
                    now,
                    fingerprint,
                    announcement,
                    mk_count,
                    status,
                    error,
                    notified_fingerprint,
                    session_expired_notified,
                    now,
                    self.owner_scope,
                ),
            )


async def capture_krs_signal() -> KrsWatchSignal:
    settings = get_settings()
    state = SessionManager().load_storage_state("mahasiswa")
    if not state:
        raise AcademicPortalReadError("Session Cyber Campus belum tersedia.")
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=settings.CYBER_CAMPUS_BROWSER_HEADLESS
    )
    context = await browser.new_context(storage_state=state)
    try:
        page = await context.new_page()
        target = urljoin(
            settings.CYBER_CAMPUS_BASE_URL,
            "/modul/mhs/akademik-krs.php",
        )
        response = await page.goto(
            target,
            wait_until="domcontentloaded",
            timeout=settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
        )
        page_html = await page.content()
        if not response or response.status >= 400 or looks_like_login(page_html):
            raise AcademicPortalReadError(
                "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
            )
        page_text = await page.evaluate(
            "document.body ? document.body.innerText : ''"
        )
        announcement = parse_krs_announcement(page_text)
        kprs_html = await page.evaluate(
            PORTAL_READ_FETCH_SCRIPT,
            {
                "target": "proses/_akademik-krs_dilihat.php",
                "payload": {"aksi": "tampil"},
            },
        )
        if looks_like_login(kprs_html):
            raise AcademicPortalReadError(
                "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
            )
        krs = parse_current_krs_html(kprs_html)
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
    codes = tuple(entry.course_code for entry in krs.entries)
    return KrsWatchSignal(
        announcement=announcement,
        mk_count=len(krs.entries),
        fingerprint=krs_fingerprint(announcement, codes, parse_kprs_status(page_text)),
        kprs_opened=parse_kprs_status(page_text),
    )


async def _request_login_captcha() -> None:
    from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool

    jid = admin_jid()
    if not jid:
        raise CampusLoginError(
            "Target WhatsApp owner belum dikonfigurasi untuk mengirim CAPTCHA."
        )
    owner_id = normalize_whatsapp_jid(jid) or jid
    challenge = await LOGIN_COORDINATOR.start(owner_id)
    try:
        png = await LOGIN_COORDINATOR.captcha_png(
            challenge["challenge_id"], owner_id
        )
        source = base64.b64encode(png).decode("ascii")
        caption = (
            "Login Cyber Campus — session watcher kedaluwarsa\n\n"
            f"Balas: /captcha {challenge['challenge_id']} JAWABAN\n"
            f"Berlaku sampai: {challenge['expires_at']}\n\n"
            "CAPTCHA harus dijawab manual oleh owner."
        )
        await call_wa_tool(
            "send_image", {"jid": jid, "source": source, "caption": caption}
        )
    except WaToolError as exc:
        await LOGIN_COORDINATOR.cancel(challenge["challenge_id"], owner_id)
        raise CampusLoginError(f"Gagal mengirim CAPTCHA ke WhatsApp owner: {exc}") from exc


async def krs_watcher_tick(now: datetime | None = None) -> dict:
    store = KrsWatcherStore()
    state = store.get()
    if not state["enabled"]:
        return {"enabled": False}
    current = now or datetime.now(UTC)
    try:
        signal = await capture_krs_signal()
        announcement_text = (
            f"{signal.announcement.period_start}|{signal.announcement.period_end}"
            if signal.announcement
            else None
        )
        in_window = bool(
            signal.announcement and signal.announcement.contains(current)
        ) or signal.kprs_opened is True
        near_window = bool(
            signal.announcement
            and current.date()
            >= datetime.fromisoformat(signal.announcement.period_start).date()
            - timedelta(days=1)
            and current.date()
            <= datetime.fromisoformat(signal.announcement.period_end).date()
        )
        calibration = {"skipped": "no_announcement"}
        war = {"skipped": "not_in_window"}
        if signal.announcement is not None or signal.kprs_opened is True:
            from app.xninetzy.os.academic.mahasiswa_portal.krs_war import (
                auto_calibrate_if_needed,
                run_krs_war_if_armed,
            )

            calibration_result = await auto_calibrate_if_needed(
                announcement=signal.announcement, now=current
            )
            calibration = calibration_result.get("calibration", calibration)
            if in_window:
                war_result = await run_krs_war_if_armed(
                    now=current,
                    announcement=signal.announcement,
                    kprs_opened=signal.kprs_opened is True,
                )
                war = war_result.get("war", war)
        changed = signal.fingerprint != state["last_notified_fingerprint"]
        notified = None
        if changed:
            sent = await notify_admin(
                "krs_watcher_change",
                {
                    "announcement": announcement_text or "belum ada pengumuman",
                    "mk_count": signal.mk_count,
                    "in_window": in_window,
                    "kprs_opened": signal.kprs_opened,
                },
                impact="high",
            )
            if sent:
                notified = signal.fingerprint
        store.update_tick(
            fingerprint=signal.fingerprint,
            announcement=announcement_text,
            mk_count=signal.mk_count,
            status="ok",
            notified_fingerprint=notified,
            session_expired_notified=0,
        )
        return {
            "enabled": True,
            "changed": changed,
            "in_window": in_window,
            "near_window": near_window,
            "announcement": announcement_text,
            "mk_count": signal.mk_count,
            "war": war,
            "calibration": calibration,
        }
    except AcademicPortalReadError as exc:
        message = str(exc)
        expired = "kedaluwarsa" in message
        session_expired_notified = None
        if expired and not state["session_expired_notified"]:
            session_expired_notified = 1
            try:
                await _request_login_captcha()
            except Exception as login_error:
                await notify_admin(
                    "krs_watcher_session_expired",
                    {"detail": message, "login_error": str(login_error)},
                    impact="high",
                )
        store.update_tick(
            fingerprint=None,
            announcement=state["last_announcement"],
            mk_count=state["last_mk_count"],
            status="error",
            error=message,
            session_expired_notified=session_expired_notified,
        )
        return {
            "enabled": True,
            "error": message,
            "expired": expired,
            "war": {"skipped": "capture_failed"},
            "calibration": {"skipped": "capture_failed"},
        }


def _next_interval(tick_result: dict, store: KrsWatcherStore | None = None) -> int:
    settings = get_settings()
    if not tick_result.get("enabled"):
        return max(5, int(settings.KRS_WATCHER_DEFAULT_INTERVAL_SECONDS))
    if tick_result.get("in_window"):
        return max(5, int(settings.KRS_WATCHER_WINDOW_INTERVAL_SECONDS))
    if tick_result.get("near_window"):
        return max(5, int(settings.KRS_WATCHER_ANNOUNCEMENT_INTERVAL_SECONDS))
    current = (store or KrsWatcherStore()).get()
    return max(
        5,
        min(
            int(current.get("interval_seconds") or settings.KRS_WATCHER_DEFAULT_INTERVAL_SECONDS),
            3600,
        ),
    )


async def krs_watcher_loop() -> None:
    store = KrsWatcherStore()
    while True:
        try:
            result = await krs_watcher_tick()
        except Exception as exc:
            logger.warning("krs_watcher_tick failed: %s", exc)
            result = {"enabled": True}
        await asyncio.sleep(_next_interval(result, store))
