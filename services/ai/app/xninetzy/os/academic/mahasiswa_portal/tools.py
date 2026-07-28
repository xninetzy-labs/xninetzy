from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager
from app.xninetzy.os.web_analysis.session_manager import SessionEncryptionUnavailable, SessionManager
from app.xninetzy.os.web_analysis.snapshot_manager import SnapshotManager


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
