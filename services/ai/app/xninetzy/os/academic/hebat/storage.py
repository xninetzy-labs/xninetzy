from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.academic.hebat.models import (
    ActivityType,
    AuthMode,
    HebatActivity,
    HebatAssignment,
    HebatCourse,
    HebatFile,
    HebatSession,
    UploadStatus,
)


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


# ─── Session ─────────────────────────────────────────────────────────────────

def upsert_session(chat_id: str, *, profile_name: str | None = None,
                   storage_state_path: str | None = None,
                   auth_mode: AuthMode = AuthMode.USERNAME_PASSWORD,
                   is_active: bool = False) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_sessions
              (user_chat_id, profile_name, storage_state_path, auth_mode,
               is_active, last_login_at, last_checked_at, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_chat_id) DO UPDATE SET
              profile_name=excluded.profile_name,
              storage_state_path=excluded.storage_state_path,
              auth_mode=excluded.auth_mode,
              is_active=excluded.is_active,
              last_login_at=CASE WHEN excluded.is_active=1 THEN excluded.last_login_at
                             ELSE last_login_at END,
              last_checked_at=excluded.last_checked_at,
              updated_at=excluded.updated_at
            """,
            (chat_id, profile_name, storage_state_path, auth_mode.value,
             1 if is_active else 0, now if is_active else None, now, now, now),
        )


def get_session(chat_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM hebat_sessions WHERE user_chat_id=?", (chat_id,)
        ).fetchone()
    return dict(row) if row else None


def mark_session_checked(chat_id: str, is_active: bool) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            "UPDATE hebat_sessions SET is_active=?, last_checked_at=?, updated_at=? WHERE user_chat_id=?",
            (1 if is_active else 0, now, now, chat_id),
        )


# ─── Courses ─────────────────────────────────────────────────────────────────

def upsert_course(course: HebatCourse) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_courses (moodle_course_id, fullname, shortname, course_url, last_synced_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(moodle_course_id) DO UPDATE SET
              fullname=excluded.fullname, shortname=excluded.shortname,
              course_url=excluded.course_url, last_synced_at=excluded.last_synced_at
            """,
            (course.moodle_course_id, course.fullname, course.shortname, course.course_url, now),
        )


def list_courses(query: str | None = None) -> list[dict]:
    init_db()
    with connect() as conn:
        if query:
            needle = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM hebat_courses WHERE fullname LIKE ? OR shortname LIKE ? ORDER BY fullname",
                (needle, needle),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM hebat_courses ORDER BY fullname").fetchall()
    return [dict(r) for r in rows]


def get_course_by_id(moodle_course_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM hebat_courses WHERE moodle_course_id=?", (moodle_course_id,)
        ).fetchone()
    return dict(row) if row else None


# ─── Activities ──────────────────────────────────────────────────────────────

def upsert_activity(activity: HebatActivity) -> int:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_activities
              (course_id, cmid, type, title, section_title, activity_url,
               due_at, opened_at, status, last_synced_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(cmid) DO UPDATE SET
              type=excluded.type, title=excluded.title,
              section_title=excluded.section_title, activity_url=excluded.activity_url,
              due_at=excluded.due_at, opened_at=excluded.opened_at,
              status=excluded.status, last_synced_at=excluded.last_synced_at
            """,
            (activity.course_id, activity.cmid, activity.type.value, activity.title,
             activity.section_title, activity.activity_url, activity.due_at,
             activity.opened_at, activity.status, now),
        )
        row = conn.execute("SELECT id FROM hebat_activities WHERE cmid=?", (activity.cmid,)).fetchone()
    return row["id"] if row else 0


def list_activities(course_id: str | None = None, activity_type: str | None = None) -> list[dict]:
    init_db()
    with connect() as conn:
        sql = "SELECT * FROM hebat_activities WHERE 1=1"
        params: list = []
        if course_id:
            sql += " AND course_id=?"
            params.append(course_id)
        if activity_type:
            sql += " AND type=?"
            params.append(activity_type)
        sql += " ORDER BY section_title, title"
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_activity_by_cmid(cmid: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM hebat_activities WHERE cmid=?", (cmid,)).fetchone()
    return dict(row) if row else None


# ─── Files ───────────────────────────────────────────────────────────────────

def upsert_file(f: HebatFile) -> int:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_files
              (activity_id, filename, file_url, local_path, mime_type, size_bytes, sha256, downloaded_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT DO NOTHING
            """,
            (f.activity_id, f.filename, f.file_url, f.local_path,
             f.mime_type, f.size_bytes, f.sha256, now if f.local_path else None),
        )
        row = conn.execute(
            "SELECT id FROM hebat_files WHERE activity_id=? AND filename=?",
            (f.activity_id, f.filename),
        ).fetchone()
    return row["id"] if row else 0


# ─── Assignments ─────────────────────────────────────────────────────────────

def upsert_assignment(assign: HebatAssignment) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_assignments
              (activity_id, title, instruction_text, opened_at, due_at,
               time_remaining_text, submission_status, grading_status,
               last_modified_text, max_files, max_bytes, accepted_types,
               latest_submission_file, last_synced_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(activity_id) DO UPDATE SET
              title=excluded.title, instruction_text=excluded.instruction_text,
              opened_at=excluded.opened_at, due_at=excluded.due_at,
              time_remaining_text=excluded.time_remaining_text,
              submission_status=excluded.submission_status,
              grading_status=excluded.grading_status,
              last_modified_text=excluded.last_modified_text,
              max_files=excluded.max_files, max_bytes=excluded.max_bytes,
              accepted_types=excluded.accepted_types,
              latest_submission_file=excluded.latest_submission_file,
              last_synced_at=excluded.last_synced_at
            """,
            (assign.activity_id, assign.title, assign.instruction_text,
             assign.opened_at, assign.due_at, assign.time_remaining_text,
             assign.submission_status, assign.grading_status,
             assign.last_modified_text, assign.max_files, assign.max_bytes,
             assign.accepted_types, assign.latest_submission_file, now),
        )


def list_assignments(course_id: str | None = None) -> list[dict]:
    init_db()
    with connect() as conn:
        if course_id:
            rows = conn.execute(
                """
                SELECT ha.*, act.course_id, act.cmid, act.activity_url, act.section_title
                FROM hebat_assignments ha
                JOIN hebat_activities act ON act.id = ha.activity_id
                WHERE act.course_id=?
                ORDER BY ha.due_at ASC NULLS LAST
                """,
                (course_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ha.*, act.course_id, act.cmid, act.activity_url, act.section_title
                FROM hebat_assignments ha
                JOIN hebat_activities act ON act.id = ha.activity_id
                ORDER BY ha.due_at ASC NULLS LAST
                """
            ).fetchall()
    return [dict(r) for r in rows]


def get_assignment_by_activity(activity_id: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM hebat_assignments WHERE activity_id=?", (activity_id,)
        ).fetchone()
    return dict(row) if row else None


# ─── Submissions ─────────────────────────────────────────────────────────────

def create_submission(*, assignment_id: int, source_chat_id: str,
                      source_message_id: str | None, local_file_path: str,
                      uploaded_filename: str, confirmation_token: str) -> int:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_submissions
              (assignment_id, source_chat_id, source_message_id, local_file_path,
               uploaded_filename, upload_status, confirmation_token, created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (assignment_id, source_chat_id, source_message_id, local_file_path,
             uploaded_filename, UploadStatus.PENDING_CONFIRMATION.value,
             confirmation_token, now),
        )
        row = conn.execute(
            "SELECT id FROM hebat_submissions WHERE confirmation_token=?",
            (confirmation_token,),
        ).fetchone()
    return row["id"] if row else 0


def get_submission_by_token(token: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM hebat_submissions WHERE confirmation_token=?", (token,)
        ).fetchone()
    return dict(row) if row else None


def update_submission_status(token: str, status: UploadStatus,
                             verification_text: str | None = None,
                             error: str | None = None) -> None:
    init_db()
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE hebat_submissions SET upload_status=?,
              confirmed_at=CASE WHEN ?='uploading' THEN ? ELSE confirmed_at END,
              submitted_at=CASE WHEN ?='uploaded' THEN ? ELSE submitted_at END,
              verification_text=COALESCE(?, verification_text),
              error_message=COALESCE(?, error_message)
            WHERE confirmation_token=?
            """,
            (status.value, status.value, now, status.value, now,
             verification_text, error, token),
        )


# ─── Downloads ───────────────────────────────────────────────────────────────

def record_download(
    chat_id: str,
    *,
    file_url: str,
    course_id: str | None = None,
    cmid: str | None = None,
    activity_url: str | None = None,
    final_url: str | None = None,
    filename: str | None = None,
    mime_type: str | None = None,
    local_path: str | None = None,
    size_bytes: int | None = None,
    sha256: str | None = None,
    text_excerpt: str | None = None,
    summary: str | None = None,
) -> int:
    """Persist a downloaded HEBAT file so its content is searchable later."""
    init_db()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO hebat_downloads
              (chat_id, course_id, cmid, activity_url, file_url, final_url, filename,
               mime_type, local_path, size_bytes, sha256, text_excerpt, summary, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (chat_id, course_id, cmid, activity_url, file_url, final_url, filename,
             mime_type, local_path, size_bytes, sha256,
             (text_excerpt or "")[:4000], (summary or "")[:2000], _now()),
        )
        return int(cur.lastrowid or 0)


def search_downloads(chat_id: str, query: str | None = None, limit: int = 20) -> list[dict]:
    """Find previously downloaded HEBAT files by filename / excerpt / summary."""
    init_db()
    with connect() as conn:
        if query:
            needle = f"%{query}%"
            rows = conn.execute(
                """
                SELECT * FROM hebat_downloads
                WHERE chat_id=? AND (filename LIKE ? OR text_excerpt LIKE ? OR summary LIKE ?)
                ORDER BY created_at DESC LIMIT ?
                """,
                (chat_id, needle, needle, needle, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM hebat_downloads WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()
    return [dict(r) for r in rows]


# ─── Audit Log ───────────────────────────────────────────────────────────────

def audit_log(chat_id: str, action: str, status: str,
              target_type: str | None = None, target_id: str | None = None,
              detail: dict | None = None) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_audit_logs
              (user_chat_id, action, target_type, target_id, status, detail_json, created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (chat_id, action, target_type, target_id, status,
             json.dumps(detail or {}, ensure_ascii=False), _now()),
        )


# ─── Reminder dedup ──────────────────────────────────────────────────────────

def has_reminder_for_assignment(assignment_id: int, hours_before: int) -> bool:
    """Check if a reminder already exists for this assignment + hours combination."""
    init_db()
    keyword = f"hebat_assign_{assignment_id}_h{hours_before}"
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM reminders WHERE description LIKE ? AND status='pending'",
            (f"%{keyword}%",),
        ).fetchone()
    return row is not None
