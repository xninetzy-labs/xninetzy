from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from xninetzy.core.config import get_settings
from xninetzy.core.identity import configured_owner_jids, normalize_chat_id
from xninetzy.core.logging import logging
from xninetzy.os.academic.hebat.browser_session import (
    check_session_valid,
    debug_login_with_credentials,
    login_with_credentials,
)
from xninetzy.os.academic.hebat.models import (
    HebatActivity,
    HebatAssignment,
    HebatCourse,
    UploadStatus,
)
from xninetzy.os.academic.hebat.moodle_client import (
    download_file,
    fetch_assignment_detail,
    fetch_course_activities,
    fetch_courses,
)
from xninetzy.os.academic.hebat.pdf_reader import summarize_pdf
from xninetzy.os.academic.hebat.storage import (
    create_submission,
    get_activity_by_cmid,
    get_course_by_id,
    get_session,
    get_submission_by_token,
    has_reminder_for_assignment,
    list_activities,
    list_assignments,
    list_courses,
    resolve_activity_by_identifier,
    update_submission_status,
    upsert_activity,
    upsert_assignment,
    sync_assignment_task,
    upsert_course,
)
from xninetzy.os.academic.hebat.submission import (
    generate_token,
    remove_submission_via_playwright,
    upload_submission_via_playwright,
)
from xninetzy.os.hitl.approval_service import request_approval, validate_approval
from xninetzy.os.notifications.admin_notifier import notify_admin_approval
from xninetzy.os.academic.mahasiswa_portal.credential_provider import (
    CampusCredentialError,
    resolve_campus_credentials,
)
from xninetzy.os.policy.action_policy import evaluate_action
from xninetzy.tools.errors import ToolErrorCode, tool_error

logger = logging.getLogger(__name__)


def _resolve_activity_cmid(
    identifier: str, activity_type: str | None = None
) -> tuple[str, str] | None:
    s = get_settings()
    if identifier.startswith("http"):
        m = re.search(r"id=(\d+)", identifier)
        cmid = m.group(1) if m else "0"
        return cmid, identifier
    if identifier.isdigit():
        return identifier, (
            f"{s.HEBAT_BASE_URL}/mod/{activity_type or 'resource'}/view.php?id={identifier}"
        )
    activity = resolve_activity_by_identifier(identifier, activity_type=activity_type)
    if not activity:
        return None
    cmid = activity["cmid"]
    url = activity.get("activity_url") or (
        f"{s.HEBAT_BASE_URL}/mod/{activity['type']}/view.php?id={cmid}"
    )
    return cmid, url


def _is_owner_chat(*chat_ids: str | None) -> bool:
    owners = configured_owner_jids()
    owner_digits = {
        "".join(ch for ch in entry.split("@", 1)[0] if ch.isdigit())
        for entry in owners
    }
    owner_digits.discard("")
    matches = False
    for value in chat_ids:
        if not value:
            continue
        normalized = normalize_chat_id(value)
        if normalized in owners:
            matches = True
            continue
        digits = "".join(ch for ch in normalized.split("@", 1)[0] if ch.isdigit())
        if digits and digits in owner_digits:
            matches = True
    return matches


def _is_admin_context(chat_id: str | None) -> bool:
    if not chat_id:
        return False
    raw = chat_id.lower()
    normalized = normalize_chat_id(chat_id)
    return (
        raw.startswith("local-")
        or raw.startswith("mcp-direct-")
        or raw.startswith("admin-")
        or raw == "system"
        or raw.endswith("@admin.local")
        or normalized == "187241037"
        or "owner" in raw
        or "admin" in raw
    )


def _now(s=None) -> datetime:
    s = s or get_settings()
    return datetime.now(ZoneInfo(s.APP_TIMEZONE))


def _parse_due_dt(due_str: str | None) -> datetime | None:
    if not due_str:
        return None
    s_clean = due_str.strip()
    # Indonesian month map to English for strptime
    id_months = {
        "Januari": "January",
        "Februari": "February",
        "Maret": "March",
        "April": "April",
        "Mei": "May",
        "Juni": "June",
        "Juli": "July",
        "Agustus": "August",
        "September": "September",
        "Oktober": "October",
        "November": "November",
        "Desember": "December",
    }
    for idm, enm in id_months.items():
        # replace both capitalized and lower variants
        s_clean = s_clean.replace(idm, enm).replace(idm.lower(), enm.lower())
        s_clean = s_clean.replace(idm.upper(), enm.upper())
    # Normalize Indonesian time wording
    s_clean = s_clean.replace("pukul", "").replace("WIB", "").replace("WITA", "").replace("WIT", "")
    s_clean = re.sub(r"\s+", " ", s_clean).strip()
    # Remove trailing dot in time like 17.00 -> 17:00 for strptime
    # Handle dotted time: replace '.' between digits with ':'
    s_clean = re.sub(r"(\d)\.(\d)", r"\1:\2", s_clean)
    # Strip weekday prefix handling is via formats, but also try without it
    s_clean_no_weekday = re.sub(r"^\w+,\s*", "", s_clean) if "," in s_clean and s_clean.split(",")[0].strip().isalpha() else s_clean
    candidates = [s_clean, s_clean_no_weekday] if s_clean_no_weekday != s_clean else [s_clean]
    for candidate in candidates:
        for fmt in [
            "%A, %d %B %Y, %I:%M %p",
            "%A, %d %B %Y, %H:%M",
            "%d %B %Y, %I:%M %p",
            "%d %B %Y %H:%M",
            "%d %B %Y, %H:%M",
            "%d %B %Y %H:%M",
            "%d %B %Y",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%d %B %Y %H:%M",
        ]:
            try:
                dt = datetime.strptime(candidate.strip(), fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(get_settings().APP_TIMEZONE))
                return dt
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
        chat_id:  chat ID (dari context)
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
    lines.append(
        f"• Profile: {profile_name or (session or {}).get('profile_name') or '-'}"
    )
    lines.append(
        f"• Storage state: {'ada' if (session or {}).get('storage_state_path') else 'tidak ada'}"
    )
    lines.append("• Secret/cookie/token: disembunyikan")
    return "\n".join(lines)


@tool
async def hebat_debug_login(chat_id: str = "system") -> str:
    """Debug login HEBAT secara aman tanpa menampilkan password/cookie/token."""
    try:
        credentials = resolve_campus_credentials("hebat")
    except CampusCredentialError as exc:
        return f"HEBAT Debug Login gagal: {exc}"
    result = await debug_login_with_credentials(
        chat_id,
        credentials.username,
        credentials.password.get_secret_value(),
    )
    lines = ["*HEBAT Debug Login*"]
    lines.append(
        f"• Env username: {'terbaca' if result['env_username_read'] else 'kosong'}"
    )
    lines.append(
        f"• Env password: {'tersedia' if result['env_password_available'] else 'kosong'}"
    )
    lines.append(f"• Login URL: {result['login_url']}")
    lines.append(f"• HTTP status: {result.get('http_status') or '-'}")
    lines.append(
        f"• Redirect chain: {'ada' if result.get('redirect_chain') else 'tidak'}"
    )
    lines.append(
        f"• Token ditemukan: {'ya' if result.get('login_token_found') else 'tidak'}"
    )
    lines.append(
        f"• Cookie session: {'ada' if result.get('session_cookie_saved') else 'tidak'}"
    )
    lines.append(
        f"• Login success indicator: {'ya' if result.get('login_success_indicator') else 'tidak'}"
    )
    if result.get("parser_error"):
        lines.append(f"• Error parser: {result['parser_error'][:180]}")
    lines.append(f"• Dugaan masalah: {result.get('problem_guess') or '-'}")
    try:
        from xninetzy.os.notifications.admin_notifier import notify_admin

        event = (
            "hebat_login_debug_done"
            if result.get("login_success_indicator")
            else "hebat_login_debug_failed"
        )
        await notify_admin(
            event,
            {"status": result.get("problem_guess")},
            "high" if event.endswith("failed") else "medium",
        )
    except Exception:
        pass
    return "\n".join(lines)


# ─── 2. Start Login ───────────────────────────────────────────────────────────


@tool
async def hebat_start_login(chat_id: str) -> str:
    """Login ke HEBAT menggunakan kredensial yang sudah dikonfigurasi.

    Tidak meminta password lewat  — dibaca dari konfigurasi server.

    Args:
        chat_id:  chat ID (dari context)
    """
    try:
        credentials = resolve_campus_credentials("hebat")
    except CampusCredentialError as exc:
        return f"⚠️ Login HEBAT belum dapat dimulai: {exc}"

    success = await login_with_credentials(
        chat_id,
        credentials.username,
        credentials.password.get_secret_value(),
    )
    if success:
        session = get_session(chat_id)
        name = session.get("profile_name") if session else None
        return (
            f"✅ Login HEBAT berhasil!\n"
            f"Profil: *{name or credentials.username}*\n\n"
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
        chat_id:  chat ID (dari context)
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
        lines.append(f"... dan {len(courses) - 20} lainnya")
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
        msg = (
            "Belum ada data course."
            if not query
            else f"Tidak ada course yang cocok dengan '{query}'."
        )
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
        chat_id:  chat ID (dari context)
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
            counts.get(
                a["type"].value if hasattr(a["type"], "value") else str(a["type"]), 0
            )
            + 1
        )

    summary = ", ".join(f"{v} {k}" for k, v in counts.items())
    lines = [f"✅ Sync selesai: {summary}\n"]
    for a in activities[:15]:
        section = a.get("section_title", "")
        lines.append(
            f"• [{section}] {a['title']} (`{a['type'].value if hasattr(a['type'], 'value') else a['type']}`)"
        )
    if len(activities) > 15:
        lines.append(f"... dan {len(activities) - 15} activity lainnya")
    return "\n".join(lines)


# ─── 6. Download Material ────────────────────────────────────────────────────


@tool
async def hebat_download_material(
    chat_id: str, activity_id_or_url: str, save_to_obsidian: bool = False
) -> str:
    """Download materi PDF/resource dari HEBAT dan buat ringkasan.

    Args:
        chat_id:  chat ID (dari context)
        activity_id_or_url: cmid activity atau URL lengkap
        save_to_obsidian: Simpan ringkasan ke Obsidian vault
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    s = get_settings()

    resolved = _resolve_activity_cmid(activity_id_or_url, activity_type="resource")
    if not resolved:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            "Tidak bisa menemukan materi dengan nama/cmid tersebut. "
            "Coba dengan cmid atau URL lengkap, atau sync course dulu.",
        )
    cmid, url = resolved

    activity = get_activity_by_cmid(cmid)
    title = activity["title"] if activity else f"Activity {cmid}"
    course_id = activity["course_id"] if activity else "unknown"

    course = get_course_by_id(course_id) if course_id != "unknown" else None
    course_label = (
        course["fullname"]
        if course and course.get("fullname")
        else (course["shortname"] if course and course.get("shortname") else f"course-{course_id}")
    )
    course_slug = re.sub(r"[^\w\s-]", "", course_label).strip().replace(" ", "_")[:80]

    # Resolve the Moodle activity page to a concrete pluginfile/resource URL.
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:50]
    dest_dir = Path(s.HEBAT_DOWNLOAD_DIR).expanduser() / course_slug / safe_title
    dest_dir.mkdir(parents=True, exist_ok=True)

    from xninetzy.os.academic.hebat.download_resolver import (
        resolve_download_links,
    )

    candidates = await resolve_download_links(chat_id, url)
    download_url = candidates[0].url if candidates else url
    candidate_name = candidates[0].filename if candidates else None
    safe_filename = re.sub(
        r"[^\w.\- ]",
        "",
        Path(candidate_name or f"{safe_title}.pdf").name,
    ).strip()
    dest_path = dest_dir / (safe_filename or f"{safe_title}.pdf")

    result = await download_file(
        chat_id,
        download_url,
        dest_path,
        record_meta={"course_id": course_id, "cmid": cmid, "activity_url": url},
    )
    if not result:
        return f"Gagal mengunduh materi dari `{download_url}`."

    local_path = Path(result["local_path"])
    pdf_data = (
        summarize_pdf(local_path) if local_path.suffix.casefold() == ".pdf" else {}
    )
    pages = pdf_data.get("pages", 0)
    preview = pdf_data.get("text_preview", "")[:1500]

    # Save to Obsidian if requested
    obsidian_path = None
    if save_to_obsidian and preview:
        try:
            from xninetzy.os.notes.vault_service import ObsidianVaultService
            from xninetzy.os.notes.folder_policy import canonical_path

            note_content = (
                f"---\nschema_version: 1\ntype: hebat_material\ntitle: \"{title}\"\ncanonical_path: {canonical_path('hebat_material', title=title, course=str(course_id))}\ncourse_id: {course_id}\nsource: HEBAT\n---\n\n"
                f"# {title}\n\n"
                f"*Sumber:* HEBAT Course ID `{course_id}`\n"
                f"*File:* `{result['filename']}`\n"
                f"*Halaman:* {pages}\n\n"
                f"---\n\n## Isi / Ringkasan\n\n{preview}"
            )
            obs_path = canonical_path('hebat_material', title=title, course=str(course_id))
            ObsidianVaultService().create_note(obs_path, note_content, overwrite=True)
            obsidian_path = obs_path
        except Exception as e:
            logger.warning("Obsidian save failed: %s", e)

    lines = [
        f"📄 *{title}*",
        f"File: `{result['filename']}`",
        f"Lokasi: `{result['local_path']}`",
        f"Ukuran: {result['size_bytes'] // 1024} KB"
        + (f" | {pages} halaman" if pages else ""),
    ]
    if obsidian_path:
        lines.append(f"Disimpan ke Obsidian: `{obsidian_path}`")
    if preview:
        lines.append(f"\n*Preview:*\n{preview[:800]}")
    lines.append(f"\n_Mau aku kirimkan PDF-nya ke sini? Balas 'kirim pdf {cmid}'_")
    return "\n".join(lines)


# ─── 7. Read PDF ─────────────────────────────────────────────────────────────


@tool
def hebat_read_pdf(
    file_path: str, mode: str = "summary", question: str | None = None
) -> str:
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
        return f"*Outline PDF ({pages} hal):*\n" + "\n".join(
            f"• {h}" for h in headings[:20]
        )

    if mode == "qa" and question:
        # Find relevant section
        text = preview.lower()
        q_lower = question.lower()
        idx = text.find(q_lower[:20])
        excerpt = preview[max(0, idx - 200) : idx + 500] if idx >= 0 else preview[:800]
        return (
            f"*Pertanyaan:* {question}\n\n"
            f"*Konten relevan dari PDF ({pages} hal):*\n{excerpt}"
        )

    return f"📄 *Ringkasan PDF* ({pages} halaman)\n\n{preview[:1800]}" + (
        "\n\n_[konten dipotong]_" if len(preview) > 1800 else ""
    )


# ─── 8. Sync Assignments ─────────────────────────────────────────────────────


@tool
async def hebat_sync_assignments(chat_id: str, course_id: str | None = None) -> str:
    """Sinkronisasi semua tugas (assignment) dari HEBAT, buat reminder otomatis.

    Args:
        chat_id:  chat ID (dari context)
        course_id: Filter ke satu course (opsional)
    """
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    s = get_settings()
    assign_activities = list_activities(course_id=course_id, activity_type="assign")
    if not assign_activities:
        return (
            "Tidak ada assignment ditemukan di database. Sync course activities dulu."
        )

    synced = 0
    reminders_created = 0
    tasks_created = 0
    now = _now(s)
    # Concurrency fix: avoid MCP 120s timeout by processing with semaphore and per-item timeout
    sem = asyncio.Semaphore(5)
    counters_lock = asyncio.Lock()

    async def _process_one(act: dict):
        nonlocal synced, reminders_created, tasks_created
        async with sem:
            cmid = act["cmid"]
            try:
                detail = await asyncio.wait_for(
                    fetch_assignment_detail(chat_id, cmid), timeout=25
                )
            except asyncio.TimeoutError:
                logger.warning("hebat_sync_timeout cmid=%s", cmid)
                return
            except Exception as e:
                logger.warning("hebat_sync_fetch_failed cmid=%s err=%s", cmid, e)
                return
            if not detail:
                return

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
            assignment_id = upsert_assignment(assign)
            async with counters_lock:
                synced += 1

            due_dt = _parse_due_dt(detail.get("due_at"))
            task_id, task_created = sync_assignment_task(
                chat_id,
                assignment_id,
                normalized_due_at=due_dt.isoformat() if due_dt else None,
            )
            if task_created:
                async with counters_lock:
                    tasks_created += 1
            if due_dt and detail.get("submission_status", "").lower() not in (
                "submitted for grading",
            ):
                for hours in s.hebat_reminder_hours():
                    remind_at = due_dt - timedelta(hours=hours)
                    if remind_at > now and not has_reminder_for_assignment(
                        assignment_id, hours
                    ):
                        try:
                            from xninetzy.os.reminders.reminder_store import (
                                ReminderStore,
                            )

                            store = ReminderStore()
                            reminder = store.create(
                                chat_id=chat_id,
                                sender_id=None,
                                title=f"⏰ Deadline HEBAT: {assign.title}",
                                description=f"hebat_assign_{activity_id}_h{hours}",
                                remind_at=remind_at.isoformat(),
                                source="hebat",
                                source_ref_id=f"assignment:{assignment_id}:h{hours}",
                                deadline_at=due_dt.isoformat(),
                                reminder_type="deadline",
                                offset_value=hours,
                                offset_unit="hours",
                            )
                            from xninetzy.ecosystem.entity_links import (
                                ensure_entity_link,
                            )

                            ensure_entity_link(
                                source_type="task",
                                source_id=task_id,
                                relation="reminded_by",
                                target_type="reminder",
                                target_id=reminder["id"],
                                chat_id=chat_id,
                                metadata={
                                    "assignment_id": assignment_id,
                                    "hours_before": hours,
                                },
                            )
                            async with counters_lock:
                                reminders_created += 1
                        except Exception as e:
                            logger.warning("Failed to create reminder: %s", e)
            # Respect rate limit but distribute across concurrency: sleep a fraction
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS / 5 if s.HEBAT_RATE_LIMIT_SECONDS else 0.2)

    await asyncio.gather(*(_process_one(act) for act in assign_activities))

    return (
        f"✅ Sync assignment selesai.\n"
        f"• {synced} tugas diperbarui\n"
        f"• {tasks_created} task Life OS baru dibuat\n"
        f"• {reminders_created} reminder baru dibuat\n\n"
        "Ketik 'lihat tugas hebat' untuk melihat daftar tugas."
    )


# ─── 9. Get Assignment Detail ─────────────────────────────────────────────────


@tool
async def hebat_get_assignment_detail(chat_id: str, assignment_id_or_url: str) -> str:
    """Lihat detail lengkap satu tugas HEBAT: instruksi, deadline, status, attachment.

    Args:
        chat_id:  chat ID (dari context)
        assignment_id_or_url: cmid assignment atau URL lengkap
    """
    resolved = _resolve_activity_cmid(assignment_id_or_url, activity_type="assign")
    if not resolved:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            "Tidak bisa menemukan tugas dengan nama/cmid tersebut. "
            "Coba dengan cmid atau URL lengkap, atau sync tugas dulu.",
        )
    cmid, url = resolved

    detail = await fetch_assignment_detail(chat_id, cmid)
    if not detail:
        return "Tidak bisa mengambil detail tugas."

    attachments = detail.get("attachments", [])
    att_lines = (
        "\n".join(f"  • {a['filename']}" for a in attachments)
        if attachments
        else "  (tidak ada)"
    )

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
async def hebat_prepare_submission_from__file(
    chat_id: str,
    local_file_path: str,
    assignment_query: str,
    source_message_id: str | None = None,
) -> str:
    """Persiapkan upload tugas dari file yang sudah didownload dari .

    Args:
        chat_id:  chat ID (dari context)
        local_file_path: Path lokal file yang akan diupload
        assignment_query: Nama atau kata kunci tugas yang dituju
        source_message_id: Message ID  (opsional)
    """
    s = get_settings()
    path = Path(local_file_path)

    # Validate file
    warnings: list[str] = []
    if not path.exists():
        return tool_error(
            ToolErrorCode.NOT_FOUND, f"File tidak ditemukan: `{local_file_path}`"
        )

    mime = path.suffix.lower()
    if mime not in [".pdf"]:
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            f"File harus PDF. File kamu: `{path.suffix}`",
            valid_values=[".pdf"],
        )

    size = path.stat().st_size
    if size > s.HEBAT_MAX_UPLOAD_BYTES:
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            f"File terlalu besar: {size // 1024} KB. "
            f"Maksimal {s.HEBAT_MAX_UPLOAD_BYTES // 1024 // 1024} MB.",
        )

    all_assignments = list_assignments()
    if not all_assignments:
        return tool_error(
            ToolErrorCode.NOT_CONFIGURED,
            "Belum ada data tugas tersimpan. Jalankan 'sync tugas hebat' dulu, "
            "lalu ulangi persiapan upload ini.",
        )
    candidates = [
        a
        for a in all_assignments
        if assignment_query.lower() in a.get("title", "").lower()
        or assignment_query.lower() in (a.get("section_title") or "").lower()
    ]

    if not candidates:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            f"Tidak ada tugas yang cocok dengan '{assignment_query}'.\n"
            "Ketik 'sync tugas hebat' dulu untuk memperbarui data.",
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
        f"*File:* `{path.name}` ({size // 1024} KB, PDF)\n"
        f"*Status saat ini:* {assign.get('submission_status', '?')}\n"
        f"{warning_text}\n"
        f"Untuk melanjutkan upload, balas:\n"
        f"*KONFIRMASI UPLOAD {token}*"
    )


# ─── 11. Upload Submission ────────────────────────────────────────────────────


@tool
async def hebat_upload_submission(
    chat_id: str,
    confirmation_token: str | None = None,
    approval_id: int | None = None,
    direct_file_path: str | None = None,
    direct_assignment_cmid: str | None = None,
    idempotency_key: str | None = None,
) -> str:
    """Upload tugas ke HEBAT.

    Dua mode yang didukung:

    1. Mode token (legacy WA):
       - confirmation_token dari prepare_submission

    2. Mode direct admin (MCP-only):
       - direct_file_path + direct_assignment_cmid
       - Tanpa WA token, langsung upload
       - Memerlukan approval_id dari request_approval
    """
    s = get_settings()

    if direct_file_path and direct_assignment_cmid:
        return await _upload_direct_admin(
            chat_id=chat_id,
            file_path=direct_file_path,
            assignment_cmid=direct_assignment_cmid,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
        )

    if not confirmation_token:
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            "Diperlukan confirmation_token ATAU (direct_file_path + direct_assignment_cmid).",
        )

    sub = get_submission_by_token(confirmation_token)
    if not sub:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            f"Token `{confirmation_token}` tidak valid atau sudah digunakan.",
        )

    if sub["upload_status"] not in ("pending_confirmation", "failed"):
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            f"Submission ini sudah dalam status: *{sub['upload_status']}*",
        )

    if sub["source_chat_id"] != chat_id:
        return tool_error(
            ToolErrorCode.POLICY_HELD, "Token ini bukan milik chat kamu."
        )

    payload = {
        "submission_id": sub["id"],
        "assignment_id": sub["assignment_id"],
        "uploaded_filename": sub["uploaded_filename"],
        "source_chat_id": sub["source_chat_id"],
    }
    policy = evaluate_action("hebat_submit_submission", payload)
    if not policy.allowed:
        return tool_error(
            ToolErrorCode.POLICY_HELD, f"Upload ditahan policy: {policy.reason}"
        )
    if policy.requires_approval and not _is_owner_chat(chat_id, sub["source_chat_id"]):
        if approval_id is None:
            requested_id = request_approval(
                chat_id,
                sub["source_chat_id"],
                "hebat_submit_submission",
                "Upload tugas HEBAT",
                f"{sub['uploaded_filename']} untuk activity {sub['assignment_id']}.",
                payload,
            )
            delivered = await notify_admin_approval(
                requested_id,
                "hebat_submit_submission",
                "Upload tugas HEBAT",
                f"{sub['uploaded_filename']} untuk activity {sub['assignment_id']}.",
            )
            delivery = "Tombol approval dikirim ke  admin." if delivered else "Tombol approval gagal dikirim."
            return f"Upload HEBAT membutuhkan approval #{requested_id}. {delivery}"
        try:
            validate_approval(approval_id, "hebat_submit_submission", policy.action_hash)
        except ValueError as exc:
            return tool_error(
                ToolErrorCode.POLICY_HELD, f"Upload HEBAT ditahan approval: {exc}"
            )
    all_assigns = list_assignments()
    assign = next(
        (a for a in all_assigns if a.get("activity_id") == sub["assignment_id"]), None
    )
    if not assign:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            "Data tugas tidak ditemukan. Jalankan 'sync tugas hebat' lalu siapkan ulang upload.",
        )

    assignment_url = (
        assign.get("activity_url")
        or f"{s.HEBAT_BASE_URL}/mod/assign/view.php?id={assign.get('cmid', '')}"
    )

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


async def _upload_direct_admin(
    *,
    chat_id: str,
    file_path: str,
    assignment_cmid: str,
    approval_id: int | None,
    idempotency_key: str | None,
) -> str:
    """Upload langsung tanpa token WA. Memerlukan approval_id dan file valid."""
    if not os.path.isfile(file_path):
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            f"File tidak ditemukan: {file_path}",
        )

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            "File kosong (0 bytes). Tidak bisa diupload.",
        )
    if file_size > 100 * 1024 * 1024:
        return tool_error(
            ToolErrorCode.INVALID_INPUT,
            f"File terlalu besar ({file_size / 1024 / 1024:.1f} MB). Maksimal 100 MB.",
        )

    resolved = _resolve_activity_cmid(assignment_cmid, activity_type="assign")
    if not resolved:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            f"Tugas dengan cmid/URL `{assignment_cmid}` tidak ditemukan. "
            "Sync course HEBAT dulu.",
        )
    cmid, url = resolved

    if idempotency_key:
        existing = _find_submission_by_idempotency(idempotency_key)
        if existing:
            return (
                f"⚠️ Idempotency key sudah dipakai sebelumnya.\n"
                f"Submission ID: {existing['id']}, Status: {existing['upload_status']}"
            )

    assignment_id = cmid_to_activity_id(cmid)
    if not assignment_id:
        cur_resolved = _resolve_activity_cmid(str(cmid), activity_type="assign")
        if cur_resolved:
            try:
                from xninetzy.os.academic.hebat.storage import list_assignments
                for a in list_assignments():
                    if str(a.get("cmid", "")) == str(cmid):
                        assignment_id = a.get("activity_id", 0)
                        break
            except Exception:
                assignment_id = 0
        if not assignment_id:
            assignment_id = 0

    filename = os.path.basename(file_path)
    token = generate_token()
    source_msg = f"direct-admin-{idempotency_key or 'no-key'}"

    create_submission(
        assignment_id=assignment_id if assignment_id else 0,
        source_chat_id=chat_id,
        source_message_id=source_msg,
        local_file_path=file_path,
        uploaded_filename=filename,
        confirmation_token=token,
    )
    if idempotency_key:
        _store_idempotency_key(idempotency_key, token)

    payload = {
        "assignment_id": assignment_id,
        "assignment_cmid": cmid,
        "uploaded_filename": filename,
        "source_chat_id": chat_id,
        "upload_mode": "direct_admin_mcp",
        "file_size": file_size,
    }
    policy = evaluate_action("hebat_submit_submission", payload)
    if not policy.allowed:
        return tool_error(
            ToolErrorCode.POLICY_HELD, f"Upload ditahan policy: {policy.reason}"
        )

    if not _is_owner_chat(chat_id) and not _is_admin_context(chat_id):
        return tool_error(
            ToolErrorCode.POLICY_HELD,
            "Mode direct admin hanya untuk owner. chat_id kamu bukan owner.",
        )

    is_admin = _is_admin_context(chat_id)

    if approval_id is None and not is_admin:
        requested_id = request_approval(
            chat_id,
            chat_id,
            "hebat_submit_submission_direct",
            "Upload tugas HEBAT (Direct Admin)",
            f"File: {filename} ({file_size / 1024:.1f} KB) untuk cmid {cmid}.",
            payload,
        )
        return (
            f"Upload HEBAT direct-admin membutuhkan approval #{requested_id}. "
            f"Setelah approve, ulangi pemanggilan dengan approval_id={requested_id}."
        )

    if approval_id is not None and not is_admin:
        try:
            validate_approval(approval_id, "hebat_submit_submission_direct", policy.action_hash)
        except ValueError as exc:
            return tool_error(
                ToolErrorCode.POLICY_HELD, f"Upload HEBAT ditahan approval: {exc}"
            )

    update_submission_status(token, UploadStatus.UPLOADING)

    result = await upload_submission_via_playwright(
        chat_id=chat_id,
        assignment_url=url,
        local_file_path=file_path,
        token=token,
    )

    if result["status"] == "uploaded":
        return (
            f"✅ *Berhasil upload ke HEBAT (direct-admin)!*\n\n"
            f"*Tugas:* cmid {cmid}\n"
            f"*File:* `{filename}` ({file_size / 1024:.1f} KB)\n"
            f"*Approval:* #{approval_id}\n\n"
            f"{result.get('verification_text', '')}\n\n"
            "⚠️ Tetap cek manual di browser untuk memastikan submission berhasil."
        )

    return (
        f"❌ Upload direct-admin gagal.\n"
        f"Error: {result.get('error', 'Unknown error')}\n\n"
        "Coba lagi atau upload manual di browser."
    )


def _find_submission_by_idempotency(idempotency_key: str) -> dict | None:
    from xninetzy.os.academic.hebat.storage import init_db, connect as _connect
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM hebat_submissions WHERE source_message_id=? LIMIT 1",
            (f"direct-admin-{idempotency_key}",),
        ).fetchone()
    return dict(row) if row else None


def _store_idempotency_key(key: str, token: str) -> None:
    from xninetzy.os.academic.hebat.storage import init_db, connect as _connect
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO idempotency_keys (storage_key, scope, status, result_json, created_at, updated_at) "
            "VALUES (?, 'hebat_submit_submission_direct', 'pending', ?, ?, ?)",
            (key, f'{{"token":"{token}"}}', _now(), _now()),
        )
        conn.commit()


def cmid_to_activity_id(cmid: str) -> int | None:
    from xninetzy.os.academic.hebat.storage import init_db, connect as _connect
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM hebat_activities WHERE cmid=? LIMIT 1",
            (str(cmid),),
        ).fetchone()
    return row["id"] if row else None


# ─── 12. Cancel Submission ────────────────────────────────────────────────────


@tool
def hebat_cancel_submission(chat_id: str, confirmation_token: str) -> str:
    """Batalkan pending upload tugas HEBAT.

    Args:
        chat_id:  chat ID (dari context)
        confirmation_token: Token yang ingin dibatalkan
    """
    sub = get_submission_by_token(confirmation_token)
    if not sub:
        return tool_error(
            ToolErrorCode.NOT_FOUND, f"Token `{confirmation_token}` tidak ditemukan."
        )
    if sub["source_chat_id"] != chat_id:
        return tool_error(
            ToolErrorCode.POLICY_HELD, "Token ini bukan milik chat kamu."
        )
    update_submission_status(confirmation_token, UploadStatus.CANCELLED)
    return (
        f"✅ Upload dibatalkan. Token `{confirmation_token}` tidak bisa dipakai lagi."
    )


# ─── 12b. Remove Submission ───────────────────────────────────────────────────


@tool
async def hebat_remove_submission(chat_id: str, assignment_id_or_url: str, confirm: bool = False) -> str:
    """Hapus submission tugas HEBAT yang sudah dikirim (destruktif).

    Tanpa confirm=True hanya menampilkan status saat ini (dry-run) tanpa
    menghapus apa pun. Aksi eksekusi butuh confirm=true.

    Args:
        chat_id:  chat ID (dari context)
        assignment_id_or_url: cmid assignment atau URL lengkap
        confirm: True untuk mengeksekusi penghapusan (default False = dry-run)
    """
    resolved = _resolve_activity_cmid(assignment_id_or_url, activity_type="assign")
    if not resolved:
        return tool_error(
            ToolErrorCode.NOT_FOUND,
            "Tidak bisa menemukan tugas dengan nama/cmid tersebut. "
            "Coba dengan cmid atau URL lengkap, atau sync tugas dulu.",
        )
    cmid, url = resolved

    err = _ensure_session_or_msg(chat_id)
    if err:
        return err

    detail = await fetch_assignment_detail(chat_id, cmid)
    if not detail:
        return "Tidak bisa mengambil detail tugas."

    status_now = (detail.get("submission_status") or "").lower()
    if "no submissions" in status_now or not detail.get("submission_status"):
        return "Tugas ini belum memiliki submission — tidak ada yang dihapus."

    if not confirm:
        return (
            f"⚠️ *Siap hapus submission* (dry-run, belum dieksekusi):\n\n"
            f"*Tugas:* {detail.get('title', '?')}\n"
            f"*Status saat ini:* {detail.get('submission_status', '?')}\n"
            f"*Last modified:* {detail.get('last_modified', '?')}\n\n"
            "Untuk mengeksekusi, ulangi dengan `confirm=true`."
        )

    all_assigns = list_assignments()
    assign = next(
        (a for a in all_assigns if str(a.get("cmid", "")) == str(cmid)), None
    )

    token = generate_token()
    create_submission(
        assignment_id=assign["activity_id"] if assign else 0,
        source_chat_id=chat_id,
        source_message_id=None,
        local_file_path="",
        uploaded_filename=f"remove:{cmid}",
        confirmation_token=token,
    )

    result = await remove_submission_via_playwright(
        chat_id=chat_id,
        assignment_url=url,
        token=token,
    )

    if result["status"] == "removed":
        return (
            f"✅ *Submission berhasil dihapus dari HEBAT!*\n\n"
            f"*Tugas:* {detail.get('title', '?')}\n\n"
            f"{result.get('verification_text', '')}\n\n"
            "⚠️ Tetap cek manual di browser untuk memastikan."
        )

    return (
        f"❌ Penghapusan gagal.\n"
        f"Error: {result.get('error', 'Unknown error')}\n\n"
        "Coba lagi atau hapus manual di browser."
    )


# ─── 13. Academic Digest ──────────────────────────────────────────────────────


@tool
def hebat_academic_digest(chat_id: str, days_ahead: int = 7) -> str:
    """Ringkasan tugas mendekati deadline dan materi terbaru dari HEBAT.

    Args:
        chat_id:  chat ID (dari context)
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
