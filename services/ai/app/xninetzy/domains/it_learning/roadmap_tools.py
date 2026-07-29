from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.hitl.approval_service import request_approval
from app.xninetzy.domains.it_learning.roadmap_planner import (
    create_roadmap_draft,
    format_roadmap_draft,
)
from app.xninetzy.domains.it_learning.roadmap_store import (
    get_roadmap,
    list_roadmaps,
    save_roadmap_draft,
)
from app.xninetzy.domains.it_learning.progress_tracker import (
    build_today_plan,
    get_roadmap_progress,
    get_weekly_learning_summary,
)
from app.xninetzy.os.notifications.admin_notifier import notify_admin_approval


@tool
async def learning_create_roadmap(
    topic: str,
    duration_days: int = 14,
    level: str = "beginner",
    chat_id: str = "system",
    sender_id: str | None = None,
    source_ids: list[int] | None = None,
) -> str:
    """Buat draft roadmap belajar; aktivasi dan bulk task butuh approval."""
    sources = _resolve_planning_sources(topic, source_ids)
    draft = create_roadmap_draft(topic, duration_days, level, sources)
    roadmap_id = save_roadmap_draft(draft, chat_id=chat_id, status="draft")
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=sender_id,
        action_type="activate_learning_roadmap",
        title=f"Aktifkan roadmap {draft.topic}",
        summary=f"Akan mengaktifkan roadmap #{roadmap_id} dan membuat task belajar.",
        payload={"roadmap_id": roadmap_id},
    )
    await notify_admin_approval(
        approval_id,
        "activate_learning_roadmap",
        f"Aktifkan roadmap {draft.topic}",
        f"Akan mengaktifkan roadmap #{roadmap_id} dan membuat task belajar.",
    )
    return (
        format_roadmap_draft(draft)
        + f"\n\nApproval #{approval_id} dikirim ke WhatsApp admin."
    )


def _resolve_planning_sources(topic: str, source_ids: list[int] | None) -> list[dict]:
    if source_ids:
        from app.xninetzy.db.sqlite import connect

        placeholders = ",".join("?" for _ in source_ids[:5])
        with connect() as conn:
            rows = conn.execute(
                f"SELECT id AS source_id, title, source_type FROM knowledge_sources WHERE id IN ({placeholders})",
                source_ids[:5],
            ).fetchall()
        return [dict(row) for row in rows]
    try:
        from app.xninetzy.os.knowledge.rag import quick_search

        return quick_search(topic, limit=3)
    except Exception:
        return []


@tool
def learning_list_roadmaps(chat_id: str = "system") -> str:
    """List roadmap belajar."""
    rows = list_roadmaps()
    if not rows:
        return "Belum ada roadmap belajar."
    lines = ["*Roadmap Belajar*"]
    for row in rows:
        lines.append(f"#{row['id']} - {row['title']} ({row['status']})")
    return "\n".join(lines)


@tool
def learning_get_roadmap(roadmap_id: int) -> str:
    """Detail roadmap belajar."""
    row = get_roadmap(roadmap_id)
    if not row:
        return f"Roadmap #{roadmap_id} tidak ditemukan."
    return f"*{row['title']}*\nTarget: {row['target']}\nStatus: {row['status']}"


@tool
def learning_update_progress(roadmap_id: int, progress_note: str) -> str:
    """Catat progress roadmap."""
    from app.xninetzy.db.sqlite import connect
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.xninetzy.core.config import get_settings

    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learning_progress (roadmap_id, note, created_at) VALUES (?,?,?)",
            (roadmap_id, progress_note, now),
        )
    return f"✅ Progress roadmap #{roadmap_id} dicatat."


@tool
def learning_generate_today_plan(
    chat_id: str = "system", roadmap_id: int | None = None
) -> str:
    """Buat rencana belajar adaptif dari roadmap, sesi, mastery, dan energi terakhir."""
    plan = build_today_plan(roadmap_id)
    if not plan:
        return "Belum ada roadmap aktif. Buat dan aktifkan roadmap terlebih dahulu."
    session_line = f"\nSesi aktif: `{plan['session_id']}`" if plan["session_id"] else ""
    return (
        f"*Study Today — {plan['mode']}*\nRoadmap: {plan['roadmap_title']}\n"
        f"Fokus: {plan['focus']}\nDurasi: {plan['minutes']} menit\n"
        f"Alasan: {plan['reason']}\nActive recall: {plan['recall']}{session_line}"
    )


@tool
def learning_review_week(chat_id: str = "system", roadmap_id: int | None = None) -> str:
    """Review mingguan dari sesi, menit belajar, mastery, dan fokus aktual."""
    summary = get_weekly_learning_summary(roadmap_id)
    mastery = summary["average_mastery"]
    mastery_text = f"{mastery:.0%}" if mastery is not None else "belum ada"
    lines = [
        "*Study Review Mingguan*",
        f"Sesi selesai: {summary['session_count']}",
        f"Total belajar: {summary['total_minutes']} menit",
        f"Rata-rata mastery: {mastery_text}",
    ]
    if summary["recent"]:
        lines.append("Fokus terbaru:")
        for session in summary["recent"]:
            lines.append(
                f"• {session['objective']} — {session['actual_minutes']} menit, mastery {session['mastery_after']:.0%}"
            )
    else:
        lines.append("Belum ada sesi selesai dalam 7 hari terakhir.")
    from app.xninetzy.domains.it_learning.concept_graph import mastery_focus

    concepts = mastery_focus(roadmap_id, limit=3)
    if concepts:
        lines.append("Konsep yang perlu perhatian:")
        for concept in concepts:
            lines.append(
                f"• {concept['title']} — {float(concept['mastery']):.0%}, "
                f"{concept['evidence_count']} evidence"
            )
    from app.xninetzy.domains.it_learning.recall import recall_summary

    recall = recall_summary(roadmap_id)
    coverage = recall["average_coverage"]
    coverage_text = f"{coverage:.0%}" if coverage is not None else "belum ada"
    lines.extend(
        [
            "Active recall:",
            f"• {recall['attempts']} attempt, coverage {coverage_text}, "
            f"{recall['lapses']} lapse, {recall['due']} due",
        ]
    )
    return "\n".join(lines)


@tool
def learning_get_study_progress(roadmap_id: int) -> str:
    """Tampilkan progres task, total sesi, menit belajar, dan mastery sebuah roadmap."""
    progress = get_roadmap_progress(roadmap_id)
    if not progress:
        return f"Roadmap #{roadmap_id} tidak ditemukan."
    mastery = progress["average_mastery"]
    mastery_text = f"{mastery:.0%}" if mastery is not None else "belum ada"
    concept_mastery = progress["concept_average_mastery"]
    concept_mastery_text = (
        f"{concept_mastery:.0%}" if concept_mastery is not None else "belum ada"
    )
    return (
        f"*Progress {progress['roadmap']['title']}*\n"
        f"Task: {progress['task_done']}/{progress['task_total']} ({progress['task_ratio']:.0%})\n"
        f"Sesi: {progress['session_count']}\nTotal belajar: {progress['total_minutes']} menit\n"
        f"Rata-rata mastery sesi: {mastery_text}\n"
        f"Konsep mastered: {progress['concept_mastered']}/{progress['concept_total']} "
        f"(rata-rata {concept_mastery_text})"
    )


@tool
def learning_attach_resource(
    roadmap_id: int, title: str, url: str = "", resource_type: str = "web"
) -> str:
    """Lampirkan resource ke roadmap."""
    from app.xninetzy.db.sqlite import connect
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.xninetzy.core.config import get_settings

    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learning_resources (roadmap_id, title, url, resource_type, created_at) VALUES (?,?,?,?,?)",
            (roadmap_id, title, url, resource_type, now),
        )
    return f"✅ Resource ditambahkan ke roadmap #{roadmap_id}."
