from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.browser_session import check_session_valid, debug_login_with_credentials, login_with_credentials
from app.xninetzy.os.academic.hebat.models import ActivityType, HebatActivity, HebatAssignment, HebatCourse, HebatFile, UploadStatus
from app.xninetzy.os.academic.hebat.moodle_client import (
    download_file,
    fetch_assignment_detail,
    fetch_course_activities,
    fetch_courses,
)
from app.xninetzy.os.academic.hebat.pdf_reader import summarize_pdf
from app.xninetzy.os.academic.hebat.storage import (
    audit_log,
    create_submission,
    get_activity_by_cmid,
    get_assignment_by_activity,
    get_session,
    get_submission_by_token,
    has_reminder_for_assignment,
    list_activities,
    list_assignments,
    list_courses,
    mark_session_checked,
    update_submission_status,
    upsert_activity,
    upsert_assignment,
    upsert_course,
    upsert_session,
)
from app.xninetzy.os.academic.hebat.submission import generate_token, upload_submission_via_playwright

logger = logging.getLogger(__name__)


def _now(s=None) -> datetime:
    s = s or get_settings()
    return datetime.now(ZoneInfo(s.APP_TIMEZONE))


def _parse_due_dt(due_str: str | None) -> datetime | None:
    if not due_str:
        return None
    for fmt in ["%d %B %Y, %I:%M %p", "%d %B %Y %H:%M", "%Y-%m-%dT%H:%M:%S%z",
                "%d %B %Y", "%A, %d %B %Y, %I:%M %p"]:
        try:
            return datetime.strptime(due_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _ensure_session_or_msg(chat_id: str) -> str | None:
    """Return error message if session not active, else None."""
    s = get_session(chat_id)
    if not s or not s.get("is_active"):
        return "Session HEBAT belum aktif. Ketik 'login hebat' dulu."
    return None


# ─── 1. Login Status ─────────────────────────────────────────────────────────

@tool
async def hebat_login_status(chat_id: str) -> str:
    """Cek apakah session HEBAT/Moodle masih aktif.

    Args:
        chat_id: WhatsApp chat ID (dari context)
    """
    is_valid, profile_name = await check_session_valid(chat_id)
    if is_valid:
        return f"✅ Sudah login HEBAT sebagai *{profile_name or 'User'}*."
    return "❌ Belum login HEBAT. Ketik 'login hebat' untuk memulai."


@tool
async def hebat_login_status_verbose(chat_id: str) -> str:
    """Cek status session HEBAT dengan detail aman."""
    is_valid, profile_name = await check_session_valid(chat_id)
    session = get_session(chat_id)
    lines = ["*HEBAT Login Status*"]
    lines.append(f"• Session aktif: {'ya' if is_valid else 'tidak'}")
    lines.append(f"• Profile: {profile_name or (session or {}).get('profile_name') or '-'}")
    lines.append(f"• Storage state: {'ada' if (session or {}).get('storage_state_path') else 'tidak ada'}")
    lines.append("• Secret/cookie/token: disembunyikan")
    return "\n".join(lines)


@tool
async def hebat_debug_login(chat_id: str = "system") -> str:
    """Debug login HEBAT secara aman tanpa menampilkan password/cookie/token."""
    s = get_settings()
    result = await debug_login_with_credentials(chat_id, s.HEBAT_USERNAME, s.HEBAT_PASSWORD)
    lines = ["*HEBAT Debug Login*"]
    lines.append(f"• Env username: {'terbaca' if result['env_username_read'] else 'kosong'}")
    lines.append(f"• Env password: {'tersedia' if result['env_password_available'] else 'kosong'}")
    lines.append(f"• Login URL: {result['login_url']}")
    lines.append(f"• HTTP status: {result.get('http_status') or '-'}")
    lines.append(f"• Redirect chain: {'ada' if result.get('redirect_chain') else 'tidak'}")
    lines.append(f"• Token ditemukan: {'ya' if result.get('login_token_found') else 'tidak'}")
    lines.append(f"• Cookie session: {'ada' if result.get('session_cookie_saved') else 'tidak'}")
    lines.append(f"• Login success indicator: {'ya' if result.get('login_success_indicator') else 'tidak'}")
    if result.get("parser_error"):
        lines.append(f"• Error parser: {result['parser_error'][:180]}")
    lines.append(f"• Dugaan masalah: {result.get('problem_guess') or '-'}")
    try:
        from app.xninetzy.os.notifications.admin_notifier import notify_admin
        event = "hebat_login_debug_done" if result.get("login_success_indicator") else "hebat_login_debug_failed"
        await notify_admin(event, {"status": result.get("problem_guess")}, "high" if event.endswith("failed") else "medium")
    except Exception:
        pass
    return "\n".join(lines)


# ─── 2. Start Login ───────────────────────────────────────────────────────────

@tool
async def hebat_start_login(chat_id: str) -> str:
    """Login ke HEBAT menggunakan kredensial yang sudah dikonfigurasi.

    Tidak meminta password lewat WhatsApp — dibaca dari konfigurasi server.

    Args:
        chat_id: WhatsApp chat ID (dari context)
    """
    s = get_settings()
    if not s.HEBAT_USERNAME:
        return (
            "⚠️ Username HEBAT belum dikonfigurasi di server.\n"
            "Minta admin set HEBAT_USERNAME dan HEBAT_PASSWORD di .env"
        )

    # Try credentials login
    success = await login_with_credentials(chat_id, s.HEBAT_USERNAME, s.HEBAT_PASSWORD)
    if success:
        session = get_session(chat_id)
        name = session.get("profile_name") if session else None
        return (
            f"✅ Login HEBAT berhasil!\n"
            f"Profil: *{name or s.HEBAT_USERNAME}*\n\n"
            "Ketik 'cek course hebat' untuk melihat daftar mata kuliah."
        )
    return (
        "❌ Login HEBAT gagal. Kemungkinan:\n"
        "• Username/password salah\n"
        "• Akun terkunci\n"
        "• HEBAT sedang maintenance\n\n"
        "Coba login manual di browser dan periksa kredensial."
    )


# ─── 3. Sync Courses ─────────────────────────────────────────────────────────

@tool
async def hebat_sync_courses(chat_id: str) -> str:
    """Sinkronisasi daftar course dari HEBAT ke database lokal.

    Args:
        chat_id: WhatsApp chat ID (dari context)
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    courses = await fetch_courses(chat_id)
    if not courses:
        return "Tidak bisa mengambil course — session mungkin sudah expired. Coba login ulang."

    for c in courses:
        upsert_course(HebatCourse(**c))

    lines = [f"📚 Ditemukan *{len(courses)}* course:\n"]
    for i, c in enumerate(courses[:20], 1):
        lines.append(f"{i}. {c['fullname']}")
    if len(courses) > 20:
        lines.append(f"... dan {len(courses)-20} lainnya")
    return "\n".join(lines)


# ─── 4. List Courses ─────────────────────────────────────────────────────────

@tool
def hebat_list_courses(query: str | None = None) -> str:
    """Tampilkan daftar course HEBAT dari database. Bisa filter by nama.

    Args:
        query: Kata kunci pencarian nama course (opsional)
    """
    courses = list_courses(query)
    if not courses:
        msg = "Belum ada data course." if not query else f"Tidak ada course yang cocok dengan '{query}'."
        return msg + " Ketik 'sync course hebat' untuk mengambil dari HEBAT."

    lines = [f"📚 Course HEBAT ({len(courses)} ditemukan):\n"]
    for i, c in enumerate(courses[:25], 1):
        lines.append(f"{i}. *{c['fullname']}* `(ID: {c['moodle_course_id']})`")
    return "\n".join(lines)


# ─── 5. Sync Course Activities ───────────────────────────────────────────────

@tool
async def hebat_sync_course_activities(chat_id: str, course_id: str) -> str:
    """Sinkronisasi section dan activity dari satu course HEBAT.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        course_id: Moodle course ID (angka)
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    activities = await fetch_course_activities(chat_id, course_id)
    if not activities:
        return f"Tidak ada activity ditemukan untuk course {course_id}."

    counts: dict[str, int] = {}
    for a in activities:
        act = HebatActivity(
            course_id=course_id,
            cmid=a["cmid"],
            type=a["type"],
            title=a["title"],
            section_title=a.get("section_title"),
            activity_url=a["activity_url"],
        )
        upsert_activity(act)
        counts[a["type"].value if hasattr(a["type"], "value") else str(a["type"])] = (
            counts.get(a["type"].value if hasattr(a["type"], "value") else str(a["type"]), 0) + 1
        )

    summary = ", ".join(f"{v} {k}" for k, v in counts.items())
    lines = [f"✅ Sync selesai: {summary}\n"]
    for a in activities[:15]:
        section = a.get("section_title", "")
        lines.append(f"• [{section}] {a['title']} (`{a['type'].value if hasattr(a['type'], 'value') else a['type']}`)")
    if len(activities) > 15:
        lines.append(f"... dan {len(activities)-15} activity lainnya")
    return "\n".join(lines)


# ─── 6. Download Material ────────────────────────────────────────────────────

@tool
async def hebat_download_material(chat_id: str, activity_id_or_url: str,
                                   save_to_obsidian: bool = False) -> str:
    """Download materi PDF/resource dari HEBAT dan buat ringkasan.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        activity_id_or_url: cmid activity atau URL lengkap
        save_to_obsidian: Simpan ringkasan ke Obsidian vault
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    s = get_settings()

    # Resolve URL
    if activity_id_or_url.startswith("http"):
        url = activity_id_or_url
        # Extract cmid from URL
        m = re.search(r"id=(\d+)", url)
        cmid = m.group(1) if m else "0"
    else:
        cmid = activity_id_or_url
        url = f"{s.HEBAT_BASE_URL}/mod/resource/view.php?id={cmid}"

    activity = get_activity_by_cmid(cmid)
    title = activity["title"] if activity else f"Activity {cmid}"
    course_id = activity["course_id"] if activity else "unknown"

    # Destination
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:50]
    dest_dir = Path(s.HEBAT_DOWNLOAD_DIR) / course_id / safe_title
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{safe_title}.pdf"

    # Download
    result = await download_file(chat_id, url, dest_path)
    if not result:
        return f"Gagal mengunduh materi dari `{url}`."

    # Read PDF
    pdf_data = summarize_pdf(result["local_path"])
    pages = pdf_data.get("pages", 0)
    preview = pdf_data.get("text_preview", "")[:1500]

    # Save to Obsidian if requested
    obsidian_path = None
    if save_to_obsidian and preview:
        try:
            from app.xninetzy.os.notes.vault_service import ObsidianVaultService
            note_content = (
                f"# {title}\n\n"
                f"*Sumber:* HEBAT Course ID `{course_id}`\n"
                f"*File:* `{result['filename']}`\n"
                f"*Halaman:* {pages}\n\n"
                f"---\n\n## Isi / Ringkasan\n\n{preview}"
            )
            obs_path = f"HEBAT/{course_id}/{safe_title}.md"
            ObsidianVaultService().create_note(obs_path, note_content, overwrite=True)
            obsidian_path = obs_path
        except Exception as e:
            logger.warning("Obsidian save failed: %s", e)

    lines = [
        f"📄 *{title}*",
        f"File: `{result['filename']}`",
        f"Ukuran: {result['size_bytes']//1024} KB | {pages} halaman",
    ]
    if obsidian_path:
        lines.append(f"Disimpan ke Obsidian: `{obsidian_path}`")
    if preview:
        lines.append(f"\n*Preview:*\n{preview[:800]}")
    lines.append(f"\n_Mau aku kirimkan PDF-nya ke sini? Balas 'kirim pdf {cmid}'_")
    return "\n".join(lines)


# ─── 7. Read PDF ─────────────────────────────────────────────────────────────

@tool
def hebat_read_pdf(file_path: str, mode: str = "summary",
                   question: str | None = None) -> str:
    """Baca dan ringkas PDF yang sudah diunduh dari HEBAT.

    Args:
        file_path: Path lokal file PDF
        mode: "summary" (default) | "outline" | "qa"
        question: Pertanyaan spesifik jika mode=qa
    """
    data = summarize_pdf(file_path)
    if data.get("error"):
        return f"Gagal membaca PDF: {data['error']}"

    pages = data["pages"]
    preview = data.get("text_preview", "")
    headings = data.get("headings", [])

    if mode == "outline" and headings:
        return f"*Outline PDF ({pages} hal):*\n" + "\n".join(f"• {h}" for h in headings[:20])

    if mode == "qa" and question:
        # Find relevant section
        text = preview.lower()
        q_lower = question.lower()
        idx = text.find(q_lower[:20])
        excerpt = preview[max(0, idx-200):idx+500] if idx >= 0 else preview[:800]
        return (
            f"*Pertanyaan:* {question}\n\n"
            f"*Konten relevan dari PDF ({pages} hal):*\n{excerpt}"
        )

    return (
        f"📄 *Ringkasan PDF* ({pages} halaman)\n\n"
        f"{preview[:1800]}"
        + ("\n\n_[konten dipotong]_" if len(preview) > 1800 else "")
    )


# ─── 8. Sync Assignments ─────────────────────────────────────────────────────

@tool
async def hebat_sync_assignments(chat_id: str, course_id: str | None = None) -> str:
    """Sinkronisasi semua tugas (assignment) dari HEBAT, buat reminder otomatis.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        course_id: Filter ke satu course (opsional)
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    s = get_settings()
    assign_activities = list_activities(course_id=course_id, activity_type="assign")
    if not assign_activities:
        return "Tidak ada assignment ditemukan di database. Sync course activities dulu."

    synced = 0
    reminders_created = 0
    now = _now(s)

    for act in assign_activities:
        cmid = act["cmid"]
        detail = await fetch_assignment_detail(chat_id, cmid)
        if not detail:
            continue

        activity_id = act["id"]
        assign = HebatAssignment(
            activity_id=activity_id,
            title=detail.get("title") or act["title"],
            instruction_text=detail.get("instruction"),
            opened_at=detail.get("opened_at"),
            due_at=detail.get("due_at"),
            time_remaining_text=detail.get("time_remaining"),
            submission_status=detail.get("submission_status"),
            grading_status=detail.get("grading_status"),
            last_modified_text=detail.get("last_modified"),
        )
        upsert_assignment(assign)
        synced += 1

        # Auto-create reminders for upcoming deadlines
        due_dt = _parse_due_dt(detail.get("due_at"))
        if due_dt and detail.get("submission_status", "").lower() not in ("submitted for grading",):
            for hours in s.hebat_reminder_hours():
                remind_at = due_dt - timedelta(hours=hours)
                if remind_at > now and not has_reminder_for_assignment(activity_id, hours):
                    try:
                        from app.xninetzy.os.reminders.reminder_service import ReminderService
                        from app.xninetzy.os.reminders.reminder_store import ReminderStore
                        store = ReminderStore()
                        store.create(
                            chat_id=chat_id,
                            sender_id=None,
                            title=f"⏰ Deadline HEBAT: {assign.title}",
                            description=f"hebat_assign_{activity_id}_h{hours}",
                            remind_at=remind_at.isoformat(),
                        )
                        reminders_created += 1
                    except Exception as e:
                        logger.warning("Failed to create reminder: %s", e)

        await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

    return (
        f"✅ Sync assignment selesai.\n"
        f"• {synced} tugas diperbarui\n"
        f"• {reminders_created} reminder baru dibuat\n\n"
        "Ketik 'lihat tugas hebat' untuk melihat daftar tugas."
    )


# ─── 9. Get Assignment Detail ─────────────────────────────────────────────────

@tool
async def hebat_get_assignment_detail(chat_id: str, assignment_id_or_url: str) -> str:
    """Lihat detail lengkap satu tugas HEBAT: instruksi, deadline, status, attachment.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        assignment_id_or_url: cmid assignment atau URL lengkap
    """
    s = get_settings()

    if assignment_id_or_url.startswith("http"):
        url = assignment_id_or_url
        m = re.search(r"id=(\d+)", url)
        cmid = m.group(1) if m else "0"
    else:
        cmid = assignment_id_or_url
        url = f"{s.HEBAT_BASE_URL}/mod/assign/view.php?id={cmid}"

    detail = await fetch_assignment_detail(chat_id, cmid)
    if not detail:
        return "Tidak bisa mengambil detail tugas."

    attachments = detail.get("attachments", [])
    att_lines = "\n".join(f"  • {a['filename']}" for a in attachments) if attachments else "  (tidak ada)"

    return (
        f"📋 *{detail.get('title', '?')}*\n\n"
        f"*Dibuka:* {detail.get('opened_at', '?')}\n"
        f"*Deadline:* {detail.get('due_at', '?')}\n"
        f"*Sisa waktu:* {detail.get('time_remaining', '?')}\n"
        f"*Status submit:* {detail.get('submission_status', '?')}\n"
        f"*Status nilai:* {detail.get('grading_status', '?')}\n\n"
        f"*Instruksi:*\n{detail.get('instruction', '?')[:600]}\n\n"
        f"*Attachment:*\n{att_lines}\n\n"
        f"_URL: {url}_"
    )


# ─── 10. Prepare Submission ───────────────────────────────────────────────────

@tool
async def hebat_prepare_submission_from_whatsapp_file(
    chat_id: str,
    local_file_path: str,
    assignment_query: str,
    source_message_id: str | None = None,
) -> str:
    """Persiapkan upload tugas dari file yang sudah didownload dari WhatsApp.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        local_file_path: Path lokal file yang akan diupload
        assignment_query: Nama atau kata kunci tugas yang dituju
        source_message_id: Message ID WhatsApp (opsional)
    """
    s = get_settings()
    path = Path(local_file_path)

    # Validate file
    warnings: list[str] = []
    if not path.exists():
        return f"File tidak ditemukan: `{local_file_path}`"

    mime = path.suffix.lower()
    if mime not in [".pdf"]:
        return f"File harus PDF. File kamu: `{path.suffix}`"

    size = path.stat().st_size
    if size > s.HEBAT_MAX_UPLOAD_BYTES:
        return (
            f"File terlalu besar: {size//1024} KB. "
            f"Maksimal {s.HEBAT_MAX_UPLOAD_BYTES//1024//1024} MB."
        )

    # Search assignment
    all_assignments = list_assignments()
    candidates = [
        a for a in all_assignments
        if assignment_query.lower() in a.get("title", "").lower()
        or assignment_query.lower() in (a.get("section_title") or "").lower()
    ]

    if not candidates:
        return (
            f"Tidak ada tugas yang cocok dengan '{assignment_query}'.\n"
            "Ketik 'sync tugas hebat' dulu untuk memperbarui data."
        )

    if len(candidates) > 1:
        lines = [f"Ditemukan beberapa tugas yang cocok dengan '{assignment_query}':"]
        for i, c in enumerate(candidates[:5], 1):
            lines.append(f"{i}. *{c['title']}* — deadline: {c.get('due_at', '?')}")
        lines.append("\nTentukan tugas mana yang dimaksud lebih spesifik.")
        return "\n".join(lines)

    assign = candidates[0]

    # Check deadline
    now = _now(s)
    due_dt = _parse_due_dt(assign.get("due_at"))
    if due_dt:
        if hasattr(due_dt, "tzinfo") and due_dt.tzinfo is None:
            due_dt = due_dt.replace(tzinfo=ZoneInfo(s.APP_TIMEZONE))
        if due_dt < now:
            warnings.append(f"⚠️ Deadline sudah lewat ({assign.get('due_at')})")

    # Check submission status
    sub_status = (assign.get("submission_status") or "").lower()
    if "submitted" in sub_status:
        warnings.append("⚠️ Tugas ini sudah pernah disubmit sebelumnya")

    token = generate_token()
    create_submission(
        assignment_id=assign["activity_id"],
        source_chat_id=chat_id,
        source_message_id=source_message_id,
        local_file_path=str(path),
        uploaded_filename=path.name,
        confirmation_token=token,
    )

    warning_text = "\n".join(warnings) + "\n" if warnings else ""
    due_text = assign.get("due_at") or "tidak ada deadline"

    return (
        f"📎 Siap upload ke HEBAT:\n\n"
        f"*Tugas:* {assign['title']}\n"
        f"*Deadline:* {due_text}\n"
        f"*File:* `{path.name}` ({size//1024} KB, PDF)\n"
        f"*Status saat ini:* {assign.get('submission_status', '?')}\n"
        f"{warning_text}\n"
        f"Untuk melanjutkan upload, balas:\n"
        f"*KONFIRMASI UPLOAD {token}*"
    )


# ─── 11. Upload Submission ────────────────────────────────────────────────────

@tool
async def hebat_upload_submission(chat_id: str, confirmation_token: str) -> str:
    """Upload tugas ke HEBAT setelah user konfirmasi token.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        confirmation_token: Token konfirmasi dari hebat_prepare_submission_from_whatsapp_file
    """
    s = get_settings()
    sub = get_submission_by_token(confirmation_token)
    if not sub:
        return f"Token `{confirmation_token}` tidak valid atau sudah digunakan."

    if sub["upload_status"] not in ("pending_confirmation",):
        return f"Submission ini sudah dalam status: *{sub['upload_status']}*"

    if sub["source_chat_id"] != chat_id:
        return "Token ini bukan milik chat kamu."

    # Find assignment URL
    all_assigns = list_assignments()
    assign = next(
        (a for a in all_assigns if a.get("activity_id") == sub["assignment_id"]), None
    )
    if not assign:
        return "Data tugas tidak ditemukan."

    assignment_url = assign.get("activity_url") or f"{s.HEBAT_BASE_URL}/mod/assign/view.php?id={assign.get('cmid', '')}"

    result = await upload_submission_via_playwright(
        chat_id=chat_id,
        assignment_url=assignment_url,
        local_file_path=sub["local_file_path"],
        token=confirmation_token,
    )

    if result["status"] == "uploaded":
        return (
            f"✅ *Berhasil upload ke HEBAT!*\n\n"
            f"*Tugas:* {assign['title']}\n"
            f"*File:* `{sub['uploaded_filename']}`\n\n"
            f"{result.get('verification_text', '')}\n\n"
            "⚠️ Tetap cek manual di browser untuk memastikan submission berhasil."
        )

    return (
        f"❌ Upload gagal.\n"
        f"Error: {result.get('error', 'Unknown error')}\n\n"
        "Coba lagi atau upload manual di browser."
    )


# ─── 12. Cancel Submission ────────────────────────────────────────────────────

@tool
def hebat_cancel_submission(chat_id: str, confirmation_token: str) -> str:
    """Batalkan pending upload tugas HEBAT.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        confirmation_token: Token yang ingin dibatalkan
    """
    sub = get_submission_by_token(confirmation_token)
    if not sub:
        return f"Token `{confirmation_token}` tidak ditemukan."
    if sub["source_chat_id"] != chat_id:
        return "Token ini bukan milik chat kamu."
    update_submission_status(confirmation_token, UploadStatus.CANCELLED)
    return f"✅ Upload dibatalkan. Token `{confirmation_token}` tidak bisa dipakai lagi."


# ─── 13. Academic Digest ──────────────────────────────────────────────────────

@tool
def hebat_academic_digest(chat_id: str, days_ahead: int = 7) -> str:
    """Ringkasan tugas mendekati deadline dan materi terbaru dari HEBAT.

    Args:
        chat_id: WhatsApp chat ID (dari context)
        days_ahead: Berapa hari ke depan yang dilihat (default 7)
    """
    s = get_settings()
    now = _now(s)
    cutoff = now + timedelta(days=days_ahead)

    all_assigns = list_assignments()
    if not all_assigns:
        return (
            "Belum ada data tugas. Ketik:\n"
            "1. 'sync course hebat' — ambil daftar course\n"
            "2. 'sync tugas hebat' — ambil semua tugas"
        )

    overdue, urgent, upcoming, no_date = [], [], [], []
    for a in all_assigns:
        due_dt = _parse_due_dt(a.get("due_at"))
        sub_status = (a.get("submission_status") or "").lower()
        already_submitted = "submitted" in sub_status

        if already_submitted:
            continue

        if not due_dt:
            no_date.append(a)
            continue

        if hasattr(due_dt, "tzinfo") and due_dt.tzinfo is None:
            due_dt = due_dt.replace(tzinfo=ZoneInfo(s.APP_TIMEZONE))

        if due_dt < now:
            overdue.append((a, due_dt))
        elif due_dt <= now + timedelta(days=2):
            urgent.append((a, due_dt))
        elif due_dt <= cutoff:
            upcoming.append((a, due_dt))

    lines = [f"📚 *Digest HEBAT — {days_ahead} hari ke depan*\n"]

    if overdue:
        lines.append("🔴 *Overdue (segera hubungi dosen):*")
        for a, dt in overdue[:5]:
            lines.append(f"• {a['title']} — {a.get('due_at', '?')}")

    if urgent:
        lines.append("\n🟠 *Sangat mendesak (< 2 hari):*")
        for a, dt in urgent[:5]:
            lines.append(f"• {a['title']} — {a.get('due_at', '?')}")

    if upcoming:
        lines.append("\n🟡 *Mendatang:*")
        for a, dt in upcoming[:10]:
            lines.append(f"• {a['title']} — {a.get('due_at', '?')}")

    if no_date:
        lines.append(f"\n⚪ {len(no_date)} tugas tanpa deadline")

    if not overdue and not urgent and not upcoming:
        lines.append("✅ Tidak ada tugas mendesak dalam periode ini.")

    return "\n".join(lines)
