from __future__ import annotations

import base64

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool
from app.xninetzy.os.notifications.admin_notifier import admin_jid
from app.xninetzy.os.research.permissions import is_owner_admin
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    LOGIN_COORDINATOR,
    CampusLoginError,
)
from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager
from app.xninetzy.os.web_analysis.session_manager import (
    SessionEncryptionUnavailable,
    SessionManager,
)
from app.xninetzy.os.web_analysis.snapshot_manager import SnapshotManager


def _owner_id(sender_id: str | None, chat_id: str) -> str:
    return (sender_id or chat_id or "local-owner").strip()


def _notification_jid() -> str:
    return admin_jid()


async def _send_captcha(chat_id: str, owner_id: str, challenge: dict) -> None:
    jid = _notification_jid()
    if not jid:
        raise CampusLoginError(
            "Target WhatsApp owner belum dikonfigurasi untuk mengirim CAPTCHA."
        )
    png = await LOGIN_COORDINATOR.captcha_png(
        challenge["challenge_id"], owner_id
    )
    source = base64.b64encode(png).decode("ascii")
    caption = (
        "Login Cyber Campus\n\n"
        f"Balas: /captcha {challenge['challenge_id']} JAWABAN\n"
        f"Berlaku sampai: {challenge['expires_at']}\n\n"
        "CAPTCHA harus dijawab manual oleh owner."
    )
    try:
        await call_wa_tool(
            "send_image", {"jid": jid, "source": source, "caption": caption}
        )
    except WaToolError as exc:
        raise CampusLoginError(f"Gagal mengirim CAPTCHA ke WhatsApp owner: {exc}") from exc


@tool
async def portal_login_start(
    chat_id: str = "system", sender_id: str | None = None
) -> str:
    """Mulai login Cyber Campus dan kirim CAPTCHA ke WhatsApp owner untuk dijawab manual."""
    owner_id = _owner_id(sender_id, chat_id)
    if not is_owner_admin(sender_id or chat_id, None):
        return "Login Cyber Campus hanya dapat dimulai oleh admin."
    challenge: dict | None = None
    try:
        challenge = await LOGIN_COORDINATOR.start(owner_id)
        await _send_captcha(chat_id, owner_id, challenge)
    except Exception as exc:
        if challenge:
            try:
                await LOGIN_COORDINATOR.cancel(
                    challenge["challenge_id"],
                    owner_id,
                )
            except Exception:
                pass
        return f"Login Cyber Campus belum dapat dimulai: {exc}"
    return (
        "CAPTCHA Cyber Campus sudah dikirim ke WhatsApp owner.\n"
        f"Challenge: `{challenge['challenge_id']}`\n"
        f"Kedaluwarsa: {challenge['expires_at']}"
    )


@tool
async def portal_login_submit_captcha(
    challenge_id: str,
    captcha_answer: str,
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Masukkan jawaban CAPTCHA yang diberikan manual oleh owner dan selesaikan login."""
    owner_id = _owner_id(sender_id, chat_id)
    if not is_owner_admin(sender_id or chat_id, None):
        return "Jawaban CAPTCHA hanya dapat dikirim oleh admin."
    try:
        result = await LOGIN_COORDINATOR.submit(
            challenge_id, owner_id, captcha_answer
        )
        if result.get("retry_required"):
            await _send_captcha(chat_id, owner_id, result)
            return (
                "CAPTCHA salah atau login belum berhasil. CAPTCHA baru sudah dikirim.\n"
                f"Sisa percobaan: {result['remaining_attempts']}"
            )
    except Exception as exc:
        return f"Login Cyber Campus gagal: {exc}"
    jid = _notification_jid()
    if jid:
        try:
            await call_wa_tool(
                "send_text_message",
                {
                    "jid": jid,
                    "text": "Cyber Campus berhasil login dan session terenkripsi sudah disimpan.",
                },
            )
        except WaToolError:
            pass
    return "Cyber Campus berhasil login dan session terenkripsi sudah disimpan."


@tool
async def portal_login_cancel(
    challenge_id: str,
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Batalkan challenge login Cyber Campus milik owner lokal."""
    if not is_owner_admin(sender_id or chat_id, None):
        return "Challenge login hanya dapat dibatalkan oleh admin."
    try:
        await LOGIN_COORDINATOR.cancel(
            challenge_id, _owner_id(sender_id, chat_id)
        )
    except Exception as exc:
        return f"Challenge tidak dapat dibatalkan: {exc}"
    return "Challenge login Cyber Campus dibatalkan."


@tool
def portal_session_status() -> str:
    """Periksa keberadaan session Cyber Campus terenkripsi tanpa mengekspos cookie."""
    try:
        present = SessionManager().has_session("mahasiswa")
    except SessionEncryptionUnavailable as exc:
        return f"Session belum siap: {exc}"
    return "Session Cyber Campus tersedia." if present else "Session Cyber Campus belum tersedia."


@tool
def portal_logout() -> str:
    """Hapus session Cyber Campus terenkripsi milik instalasi lokal."""
    try:
        removed = SessionManager().clear_session("mahasiswa")
    except SessionEncryptionUnavailable as exc:
        return f"Session tidak dapat dihapus: {exc}"
    return "Session Cyber Campus dihapus." if removed else "Session Cyber Campus memang tidak ada."


def _session_present() -> tuple[bool, str | None]:
    try:
        return SessionManager().has_session("mahasiswa"), None
    except SessionEncryptionUnavailable as exc:
        return False, str(exc)


@tool
def portal_info() -> str:
    """Lihat kesiapan cache dan session portal mahasiswa local-owner."""
    analysis = AnalysisCacheManager().load("mahasiswa")
    has_session, session_error = _session_present()
    lines = ["*Portal Mahasiswa (local-owner)*"]
    lines.append(f"• Cache struktur: {'ada' if analysis else 'belum ada'}")
    lines.append(f"• Status struktur: {analysis.auth_status if analysis else '-'}")
    lines.append(f"• Session terenkripsi: {'ada' if has_session else 'belum ada'}")
    if session_error:
        lines.append("• Setup: isi WEB_ANALYSIS_ENCRYPTION_KEY lalu jalankan login manual lokal.")
    lines.append("• CAPTCHA/OTP tidak pernah disolve oleh agent.")
    lines.append("• Submit KRS tidak diotomasi; monitoring hanya read/notify.")
    return "\n".join(lines)


@tool
def portal_schedule() -> str:
    """Baca snapshot jadwal terenkripsi milik owner instalasi lokal."""
    try:
        snapshot = SnapshotManager().load("mahasiswa", "schedule")
    except SessionEncryptionUnavailable:
        snapshot = None
    if not snapshot:
        return (
            "Belum ada snapshot jadwal lokal. Isi `WEB_ANALYSIS_ENCRYPTION_KEY`, "
            "login manual portal, lalu jalankan collector read-only setelah selector tervalidasi."
        )
    items = snapshot.get("items") or []
    if not items:
        return "Snapshot jadwal ada tetapi kosong."
    lines = [f"*Jadwal Lokal* (snapshot {snapshot.get('captured_at', '-')})"]
    for item in items[:20]:
        label = item.get("label") or item.get("course") or "Jadwal"
        when = item.get("when") or item.get("start") or "-"
        lines.append(f"• {when} — {label}")
    return "\n".join(lines)


@tool
def portal_krs_watcher_status() -> str:
    """Status watcher slot KRS yang hanya membaca dan mengirim notifikasi.

    Tool ini hanya membaca status ketersediaan slot dan mengirim notifikasi
    WhatsApp. Tidak melakukan klik/submit otomatis pada form KRS; tindakan final
    tetap manual oleh owner instalasi lokal.
    """
    return (
        "Watcher KRS belum diaktifkan sampai selector portal tervalidasi manual. "
        "Batas permanen: READ + NOTIFY saja, tidak pernah klik/submit."
    )
