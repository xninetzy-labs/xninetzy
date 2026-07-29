from __future__ import annotations

import base64

from langchain_core.tools import tool

from app.xninetzy.core.identity import normalize_whatsapp_jid
from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    LOGIN_COORDINATOR,
    CampusLoginError,
)
from app.xninetzy.os.academic.mahasiswa_portal.grade_token import (
    GRADE_TOKEN_COORDINATOR,
)
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    ACADEMIC_PORTAL_READER,
    GradeResult,
    ScheduleResult,
)
from app.xninetzy.os.academic.mahasiswa_portal.runtime_analyzer import (
    PortalRuntimeAnalyzer,
)
from app.xninetzy.os.notifications.admin_notifier import admin_jid
from app.xninetzy.os.research.permissions import is_owner_admin
from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager
from app.xninetzy.os.web_analysis.session_manager import (
    SessionEncryptionUnavailable,
    SessionManager,
)


def _owner_id(sender_id: str | None, chat_id: str) -> str:
    raw = (sender_id or chat_id or "local-owner").strip()
    return normalize_whatsapp_jid(raw) or raw


def _notification_jid() -> str:
    return admin_jid()


async def _send_captcha(owner_id: str, challenge: dict) -> None:
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
        await _send_captcha(owner_id, challenge)
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
            await _send_captcha(owner_id, result)
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


def _format_schedule(result: ScheduleResult) -> str:
    lines = [f"*{result.period}*", f"Total mata ajar: {len(result.entries)}"]
    for index, item in enumerate(result.entries, start=1):
        lines.extend(
            [
                "",
                f"{index}. *{item.course}* ({item.credits} SKS, kelas {item.class_code})",
                f"   {item.schedule} — {item.room}",
                f"   Petugas: {item.lecturers}",
            ]
        )
    return "\n".join(lines)


def _format_grades(result: GradeResult) -> str:
    lines = ["*Nilai Cyber Campus*", f"Periode: {result.period}"]
    for index, entry in enumerate(result.entries, start=1):
        values = [(key, value) for key, value in entry.values if value]
        if not values:
            continue
        lines.append("")
        lines.append(f"{index}. " + " | ".join(f"{key}: {value}" for key, value in values))
    return "\n".join(lines)


@tool
async def portal_schedule() -> str:
    """Baca jadwal kuliah real-time dari session Cyber Campus owner."""
    try:
        return _format_schedule(await ACADEMIC_PORTAL_READER.read_schedule())
    except Exception as exc:
        return f"Jadwal Cyber Campus belum dapat dibaca: {exc}"


@tool
async def portal_grades(
    academic_period: str = "latest",
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Minta token KHS melalui WhatsApp admin untuk pembacaan nilai sekali pakai."""
    if not is_owner_admin(sender_id or chat_id, None):
        return "Pembacaan nilai hanya dapat dimulai oleh owner."
    jid = _notification_jid()
    if not jid:
        return "ADMIN_JID WhatsApp belum dikonfigurasi."
    challenge: dict | None = None
    try:
        challenge = await GRADE_TOKEN_COORDINATOR.start(jid, academic_period)
        period = await ACADEMIC_PORTAL_READER.prepare_grade_request(
            challenge["challenge_id"], academic_period
        )
        text = (
            "*Verified Token Cyber Campus*\n\n"
            "Halaman KHS sudah dibuka. Cyber Campus menyatakan token dikirim "
            "ke akun Telegram yang terdaftar pada portal.\n\n"
            f"Periode nilai: *{period.label}*\n\n"
            "Balas pesan ini dengan token nilai saja, atau kirim:\n"
            f"`/grade-token {challenge['challenge_id']} TOKEN`\n\n"
            f"Berlaku sampai: {challenge['expires_at']}\n"
            "Token dipakai sekali, tidak masuk LLM, dan tidak disimpan."
        )
        await call_wa_tool("send_text_message", {"jid": jid, "text": text})
    except Exception as exc:
        if challenge:
            await GRADE_TOKEN_COORDINATOR.cancel(challenge["challenge_id"])
            await ACADEMIC_PORTAL_READER.cancel_grade_request(
                challenge["challenge_id"]
            )
        return f"Permintaan token nilai gagal dibuat: {exc}"
    return (
        f"Halaman KHS periode {period.label} sudah dibuka dan permintaan "
        "verified token sudah dikirim ke WhatsApp admin."
    )


async def submit_grade_token(
    challenge_id: str,
    token: str,
    sender_id: str,
    sender_name: str | None = None,
) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Token nilai hanya dapat dikirim oleh WhatsApp admin."
    try:
        clean_token, academic_period = await GRADE_TOKEN_COORDINATOR.consume(
            challenge_id,
            _notification_jid(),
            token,
        )
        result = await ACADEMIC_PORTAL_READER.read_grades(
            clean_token,
            academic_period,
            challenge_id,
        )
        return _format_grades(result)
    except Exception as exc:
        return f"Nilai Cyber Campus belum dapat dibaca: {exc}"
    finally:
        token = ""


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


@tool
async def portal_navigation(verify: bool = True) -> str:
    """Inventaris navigasi Cyber Campus dari session owner secara GET/HEAD-only."""
    try:
        manifest = await PortalRuntimeAnalyzer().inspect(verify_navigation=verify)
    except Exception as exc:
        return f"Navigasi Cyber Campus belum dapat dianalisis: {exc}"
    lines = [
        "*Navigasi Cyber Campus*",
        f"• Snapshot: `{manifest.structure_hash[:16]}`",
        f"• Total: {len(manifest.navigation)}",
    ]
    if verify:
        lines.append(f"• Reachable: {len(manifest.verified_paths)}")
        lines.append(f"• Unreachable: {len(manifest.unreachable_paths)}")
    for item in manifest.navigation[:120]:
        lines.append(f"• [{item.policy}] {item.label} — `{item.path}`")
    return "\n".join(lines)


@tool
async def portal_krs_capabilities() -> str:
    """Analisis capability KRS runtime tanpa mengeksekusi action portal."""
    try:
        manifest = await PortalRuntimeAnalyzer().inspect()
    except Exception as exc:
        return f"Capability KRS belum dapat dianalisis: {exc}"
    tabs = ", ".join(manifest.krs_tabs) or "-"
    methods = ", ".join(manifest.form_methods) or "-"
    targets = ", ".join(manifest.internal_targets) or "-"
    return (
        "*KRS Runtime Capability*\n"
        f"• Snapshot: `{manifest.structure_hash}`\n"
        f"• Tab: {tabs}\n"
        f"• Form methods: {methods}\n"
        f"• Internal targets: {targets}\n"
        f"• Write controls aktif: {'ya' if manifest.write_controls_present else 'tidak'}\n"
        "• JavaScript mentah tidak pernah dieksekusi dari output LLM."
    )
