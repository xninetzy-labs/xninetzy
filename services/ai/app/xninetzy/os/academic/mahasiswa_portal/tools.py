from __future__ import annotations

import base64
from datetime import UTC, datetime

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.identity import normalize_whatsapp_jid
from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    LOGIN_COORDINATOR,
    CampusLoginError,
)
from app.xninetzy.os.academic.mahasiswa_portal.grade_token import (
    GRADE_TOKEN_COORDINATOR,
)
from app.xninetzy.os.academic.mahasiswa_portal.grade_snapshots import (
    GRADE_SNAPSHOT_REPOSITORY,
    GradeSnapshotOutcome,
)
from app.xninetzy.os.academic.mahasiswa_portal.krs_war import (
    KrsPlan,
    KrsWarStore,
    krs_war_status_text,
    load_krs_plan,
    take_krs_plan,
)
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import KrsWatcherStore
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    ACADEMIC_PORTAL_READER,
    AcademicProfile,
    AcademicStatusEntry,
    CurrentKrsResult,
    GradeResult,
    ScheduleResult,
)
from app.xninetzy.os.academic.mahasiswa_portal.runtime_analyzer import (
    PortalRuntimeAnalyzer,
)
from app.xninetzy.os.hitl.approval_service import request_approval, validate_approval
from app.xninetzy.os.notifications.admin_notifier import admin_jid, notify_admin_approval
from app.xninetzy.os.research.permissions import is_owner_admin
from app.xninetzy.os.policy.action_policy import evaluate_action
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
async def portal_session_status() -> str:
    """Validasi session Cyber Campus ke portal tanpa mengekspos cookie."""
    try:
        valid, state = await ACADEMIC_PORTAL_READER.session_status()
    except SessionEncryptionUnavailable as exc:
        return f"Session belum siap: {exc}"
    if valid:
        return "Session Cyber Campus aktif dan dapat dipakai."
    if state == "missing":
        return "Session Cyber Campus belum tersedia."
    if state == "expired":
        return "Session Cyber Campus tersedia secara lokal, tetapi kedaluwarsa di portal. Jalankan /cyber-login."
    return "Session Cyber Campus belum dapat divalidasi. Jalankan /cyber-login jika pembacaan portal gagal."


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


def _format_academic_profile(profile: AcademicProfile) -> str:
    return "\n".join(
        [
            "*Profil Akademik Cyber Campus*",
            f"• Nama: {profile.name}",
            f"• NIM: {profile.student_id}",
            f"• Fakultas: {profile.faculty or '-'}",
            f"• Program studi: {profile.study_program or '-'}",
        ]
    )


def _format_academic_status(entries: tuple[AcademicStatusEntry, ...]) -> str:
    lines = ["*Status Akademik Cyber Campus*", f"Total semester: {len(entries)}"]
    for entry in entries:
        details = [entry.status]
        if entry.decree_number and entry.decree_number != "-":
            details.append(f"SK {entry.decree_number}")
        if entry.decree_date and entry.decree_date != "-":
            details.append(entry.decree_date)
        if entry.description and entry.description != "-":
            details.append(entry.description)
        lines.append(f"• {entry.semester}: {' — '.join(details)}")
    return "\n".join(lines)


def _format_current_krs(result: CurrentKrsResult) -> str:
    lines = [
        "*KRS Aktif Cyber Campus*",
        f"Total mata kuliah: {len(result.entries)}",
        f"Total SKS: {result.total_credits}",
    ]
    for index, entry in enumerate(result.entries, start=1):
        lines.append(
            f"{index}. *{entry.course_name}* ({entry.course_code}) — "
            f"{entry.credits} SKS, kelas {entry.class_code}, {entry.status}"
        )
    return "\n".join(lines)


def _format_grades(
    result: GradeResult,
    snapshot: GradeSnapshotOutcome | None = None,
) -> str:
    lines = ["*Nilai Cyber Campus*", f"Periode: {result.period}"]
    for index, entry in enumerate(result.entries, start=1):
        values = [(key, value) for key, value in entry.values if value]
        if not values:
            continue
        lines.append("")
        lines.append(f"{index}. " + " | ".join(f"{key}: {value}" for key, value in values))
    if snapshot:
        lines.extend(["", f"Snapshot lokal: #{snapshot.snapshot_id}"])
        if snapshot.changes:
            lines.append(f"Perubahan sejak snapshot sebelumnya: {len(snapshot.changes)}")
        elif snapshot.created:
            lines.append("Perubahan sejak snapshot sebelumnya: tidak ada")
        else:
            lines.append("Snapshot sama dengan pembacaan terakhir")
    return "\n".join(lines)


def _format_grade_changes(snapshot: GradeSnapshotOutcome | None) -> str:
    if snapshot is None:
        return "Belum ada snapshot nilai lokal. Jalankan /nilai terlebih dahulu."
    lines = [
        "*Perubahan Nilai Cyber Campus*",
        f"Periode: {snapshot.period}",
        f"Snapshot: #{snapshot.snapshot_id}",
    ]
    if not snapshot.changes:
        lines.append("Belum ada perubahan antar-snapshot untuk periode ini.")
        return "\n".join(lines)
    for change in snapshot.changes:
        identity = change.course_name or change.course_code or change.course_key
        if change.kind == "added":
            detail = f"baru: {change.current_grade or 'belum tersedia'}"
        elif change.kind == "removed":
            detail = f"dihapus dari snapshot, sebelumnya: {change.previous_grade or '-'}"
        else:
            detail = f"{change.previous_grade or '-'} → {change.current_grade or '-'}"
        lines.append(f"• {identity}: {detail}")
    return "\n".join(lines)


@tool
async def portal_schedule() -> str:
    """Baca jadwal kuliah real-time dari session Cyber Campus owner."""
    try:
        return _format_schedule(await ACADEMIC_PORTAL_READER.read_schedule())
    except Exception as exc:
        return f"Jadwal Cyber Campus belum dapat dibaca: {exc}"


@tool
async def portal_profile() -> str:
    """Baca identitas akademik minimal dari session Cyber Campus owner."""
    try:
        return _format_academic_profile(await ACADEMIC_PORTAL_READER.read_profile())
    except Exception as exc:
        return f"Profil Cyber Campus belum dapat dibaca: {exc}"


@tool
async def portal_academic_status() -> str:
    """Baca riwayat status akademik dari session Cyber Campus owner."""
    try:
        return _format_academic_status(
            await ACADEMIC_PORTAL_READER.read_academic_status()
        )
    except Exception as exc:
        return f"Status akademik Cyber Campus belum dapat dibaca: {exc}"


@tool
async def portal_current_krs() -> str:
    """Baca mata kuliah KRS aktif tanpa mengubah pilihan portal."""
    try:
        return _format_current_krs(await ACADEMIC_PORTAL_READER.read_current_krs())
    except Exception as exc:
        return f"KRS aktif Cyber Campus belum dapat dibaca: {exc}"


@tool
def portal_grade_changes(academic_period: str = "") -> str:
    """Bandingkan dua snapshot nilai lokal terbaru untuk satu periode."""
    try:
        return _format_grade_changes(
            GRADE_SNAPSHOT_REPOSITORY.latest_changes(academic_period)
        )
    except Exception as exc:
        return f"Perubahan nilai belum dapat dibaca: {exc}"


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
    challenge_id: str = "",
    token: str = "",
    sender_id: str = "",
    sender_name: str | None = None,
) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Token nilai hanya dapat dikirim oleh WhatsApp admin."
    try:
        if challenge_id:
            clean_token, academic_period = await GRADE_TOKEN_COORDINATOR.consume(
                challenge_id,
                _notification_jid(),
                token,
            )
        else:
            challenge_id, clean_token, academic_period = (
                await GRADE_TOKEN_COORDINATOR.consume_owner_token(
                    _notification_jid(),
                    token,
                )
            )
        result = await ACADEMIC_PORTAL_READER.read_grades(
            clean_token,
            academic_period,
            challenge_id,
        )
        snapshot = GRADE_SNAPSHOT_REPOSITORY.save(result)
        return _format_grades(result, snapshot)
    except Exception as exc:
        return f"Nilai Cyber Campus belum dapat dibaca: {exc}"
    finally:
        token = ""


@tool
async def portal_grade_token_submit(
    challenge_id: str = "",
    token: str = "",
    sender_id: str = "",
    sender_name: str | None = None,
) -> str:
    """Kirim token KHS sekali pakai untuk challenge aktif yang sudah diverifikasi.

    challenge_id opsional: jika kosong, challenge aktif milik owner lokal yang
    dipakai. Token bersifat sekali pakai, tidak pernah disimpan, dan tidak
    ditulis ke log. Hanya owner lokal terautentikasi yang dapat menggunakannya.
    """
    return await submit_grade_token(
        challenge_id=challenge_id,
        token=token,
        sender_id=sender_id,
        sender_name=sender_name,
    )


@tool
def portal_krs_watcher_status() -> str:
    """Status watcher slot KRS yang hanya membaca dan mengirim notifikasi.

    Tool ini hanya membaca status ketersediaan slot dan mengirim notifikasi
    WhatsApp. Tidak melakukan klik/submit otomatis pada form KRS; tindakan final
    tetap manual oleh owner instalasi lokal.
    """
    state = KrsWatcherStore().get()
    interval_seconds = int(state["interval_seconds"] or 0)
    interval_label = (
        f"{interval_seconds // 60} menit" if interval_seconds >= 60 else f"{interval_seconds} detik"
    )
    lines = [
        "*Watcher Slot KRS*",
        f"• Aktif: {'ya' if state['enabled'] else 'tidak'}",
        f"• Interval: {interval_label}",
        f"• Mulai: {state['started_at'] or '-'}",
        f"• Tick terakhir: {state['last_tick_at'] or '-'}",
        f"• Status: {state['last_status']}",
    ]
    if state.get("last_announcement"):
        start, _, end = str(state["last_announcement"]).partition("|")
        lines.append(f"• Jadwal pengumuman: {start} s.d. {end}")
    lines.append(f"• MK terambil: {state['last_mk_count']}")
    if state.get("last_error"):
        lines.append(f"• Error terakhir: {state['last_error']}")
    lines.append("• Batas permanen: READ + NOTIFY saja, tidak pernah klik/submit.")
    return "\n".join(lines)


@tool
def portal_krs_watcher_start(
    interval_minutes: int | None = None,
    interval_seconds: int | None = None,
) -> str:
    """Aktifkan watcher slot KRS dengan polling READ-only dan notifikasi WhatsApp."""
    if interval_seconds is not None and interval_minutes is not None:
        return "Pilih interval_minutes atau interval_seconds, bukan keduanya."
    if interval_seconds is None:
        interval_seconds = (
            interval_minutes * 60
            if interval_minutes is not None
            else get_settings().KRS_WATCHER_DEFAULT_INTERVAL_SECONDS
        )
    if not 5 <= interval_seconds <= 3600:
        return "Interval harus antara 5-3600 detik."
    KrsWatcherStore().set_enabled(True, interval_seconds)
    return (
        f"Watcher KRS aktif: polling tiap {interval_seconds} detik. "
        "Interval menjadi lebih rapat saat pengumuman/window terdeteksi. "
        "READ + NOTIFY saja; tidak pernah klik/submit."
    )


@tool
def portal_krs_watcher_stop() -> str:
    """Nonaktifkan watcher slot KRS."""
    KrsWatcherStore().set_enabled(False)
    return "Watcher KRS dinonaktifkan."


def _plan_summary(plan: KrsPlan) -> str:
    total_sks = sum(
        int(course.credits) for course in plan.courses if course.credits.isdigit()
    )
    return f"{len(plan.courses)} MK, {total_sks} SKS"


def _krs_war_approval_payload(plan: KrsPlan) -> dict:
    return {
        "source_hash": plan.source_hash,
        "semester_label": plan.semester_label,
        "courses": [
            {
                "code": course.code,
                "target_class": course.target_class,
                "fallback_classes": list(course.fallback_classes),
            }
            for course in plan.courses
        ],
    }


@tool
async def portal_krs_war_status(
    chat_id: str = "system", sender_id: str | None = None
) -> str:
    """Status KRS War: armed, plan hash, dan riwayat run terakhir."""
    try:
        body = await krs_war_status_text()
    except Exception as exc:
        return f"Status KRS War belum dapat dibaca: {exc}"
    return "\n".join(["*KRS War Mode*", body])


@tool
async def portal_krs_war_arm(
    chat_id: str = "system",
    sender_id: str | None = None,
    approval_id: int | None = None,
) -> str:
    """Aktifkan KRS War: submit otomatis sesuai plan saat window KRS terbuka."""
    if not is_owner_admin(sender_id or chat_id, None):
        return "KRS War hanya dapat diaktifkan oleh admin."
    try:
        plan = await load_krs_plan()
    except Exception as exc:
        return f"Plan KRS belum dapat dimuat: {exc}"
    if plan is None or not plan.courses:
        return (
            "Plan KRS tidak ditemukan atau kosong. KRS War tidak diaktifkan.\n"
            "Periksa file KRS_Plan_Semester_5.md di vault Obsidian."
        )
    payload = _krs_war_approval_payload(plan)
    policy = evaluate_action("portal_krs_war_arm", payload)
    if not policy.allowed:
        return f"KRS War ditahan policy: {policy.reason}"
    if policy.requires_approval:
        if approval_id is None:
            requested_id = request_approval(
                chat_id,
                sender_id,
                "portal_krs_war_arm",
                "Aktifkan KRS War",
                f"{plan.semester_label or plan.source_path} ({_plan_summary(plan)})",
                payload,
            )
            delivered = await notify_admin_approval(
                requested_id,
                "portal_krs_war_arm",
                "Aktifkan KRS War",
                f"{plan.semester_label or plan.source_path} ({_plan_summary(plan)})",
            )
            delivery = "Tombol approval dikirim ke WhatsApp admin." if delivered else "Tombol approval gagal dikirim."
            return f"KRS War membutuhkan approval #{requested_id}. {delivery}"
        try:
            validate_approval(approval_id, "portal_krs_war_arm", policy.action_hash)
        except ValueError as exc:
            return f"KRS War ditahan approval: {exc}"
    KrsWarStore().set_armed(True, plan)
    return (
        "*KRS War Aktif*\n"
        f"• Plan: {plan.semester_label or plan.source_path} ({_plan_summary(plan)})\n"
        "• Saat window KRS terbuka, MK dalam plan akan disubmit otomatis.\n"
        "• Aksi ini bisa dibatalkan kapan saja: /krs-war disarm"
    )


@tool
def portal_krs_war_disarm(
    chat_id: str = "system", sender_id: str | None = None
) -> str:
    """Nonaktifkan KRS War: tidak ada submit otomatis lagi."""
    if not is_owner_admin(sender_id or chat_id, None):
        return "KRS War hanya dapat dinonaktifkan oleh admin."
    KrsWarStore().set_armed(False)
    return "KRS War dinonaktifkan. Tidak ada submit otomatis lagi."


@tool
async def portal_krs_war_plan(
    chat_id: str = "system", sender_id: str | None = None
) -> str:
    """Tampilkan plan KRS War: kode, nama, SKS, kelas target, dan fallback."""
    try:
        plan = await load_krs_plan()
    except Exception as exc:
        return f"Plan KRS belum dapat dimuat: {exc}"
    if plan is None or not plan.courses:
        return (
            "Plan KRS belum tersedia. Pastikan file KRS_Plan_Semester_5.md "
            "ada di vault atau /krs-war arm sudah pernah dijalankan."
        )
    lines = [
        "*KRS War Plan*",
        f"• {plan.semester_label or '-'} ({plan.source_path})",
    ]
    for index, course in enumerate(plan.courses, start=1):
        fallbacks = ", ".join(course.fallback_classes) or "-"
        lines.append(
            f"{index}. *{course.code}* {course.name} — {course.credits} SKS, "
            f"target {course.target_class}, fallback {fallbacks}"
        )
    return "\n".join(lines)


@tool
async def portal_krs_war_dry_run(
    chat_id: str = "system", sender_id: str | None = None
) -> str:
    """Jalankan simulasi KRS War tanpa submit: tampilkan apa yang akan terjadi."""
    if not is_owner_admin(sender_id or chat_id, None):
        return "Simulasi KRS War hanya dapat dijalankan oleh admin."
    try:
        plan = await load_krs_plan()
    except Exception as exc:
        return f"Plan KRS belum dapat dimuat: {exc}"
    if plan is None or not plan.courses:
        return (
            "Plan KRS belum tersedia. Pastikan file KRS_Plan_Semester_5.md "
            "ada di vault atau /krs-war arm sudah pernah dijalankan."
        )
    watcher_state = KrsWatcherStore().get()
    raw = str(watcher_state.get("last_announcement") or "")
    if "|" in raw:
        start, _, end = raw.partition("|")
        window = f"{start}|{end}" if end else f"{start}|{start}"
    else:
        today = datetime.now(UTC).date().isoformat()
        window = f"{today}|{today}"
    try:
        result = await take_krs_plan(plan, window, dry_run=True)
    except Exception as exc:
        return f"Simulasi KRS War gagal: {exc}"
    already = set(result.get("already_taken") or [])
    skipped_map = {
        item["code"]: item["reason"] for item in result.get("skipped") or []
    }
    lines = [
        "*KRS War Dry Run*",
        f"• Window: {window.replace('|', ' s.d. ')}",
        f"• Total MK dalam plan: {len(plan.courses)}",
    ]
    for index, course in enumerate(plan.courses, start=1):
        if course.code in already:
            status = "sudah terambil"
        elif course.code in skipped_map:
            status = f"dilewati: {skipped_map[course.code]}"
        else:
            status = f"akan diambil → kelas {course.target_class}"
        lines.append(f"{index}. {course.code} — {status}")
    lines.append(f"• Ringkasan: {result.get('summary') or '-'}")
    lines.append("• Tidak ada submit yang benar-benar dilakukan (dry run).")
    return "\n".join(lines)


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
