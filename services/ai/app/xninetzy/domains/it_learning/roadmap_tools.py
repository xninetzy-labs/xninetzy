from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.hitl.approval_service import request_approval
from app.xninetzy.domains.it_learning.roadmap_planner import create_roadmap_draft, format_roadmap_draft
from app.xninetzy.domains.it_learning.roadmap_store import get_roadmap, list_roadmaps, save_roadmap_draft
from app.xninetzy.os.notifications.admin_notifier import notify_admin


@tool
async def learning_create_roadmap(
    topic: str,
    duration_days: int = 14,
    level: str = "beginner",
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Buat draft roadmap belajar; aktivasi dan bulk task butuh approval."""
    draft = create_roadmap_draft(topic, duration_days, level)
    roadmap_id = save_roadmap_draft(draft, chat_id=chat_id, status="draft")
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=sender_id,
        action_type="activate_learning_roadmap",
        title=f"Aktifkan roadmap {draft.topic}",
        summary=f"Akan mengaktifkan roadmap #{roadmap_id} dan membuat task belajar.",
        payload={"roadmap_id": roadmap_id},
    )
    await notify_admin("roadmap_draft_created", {"status": f"roadmap #{roadmap_id}", "title": draft.topic}, "medium")
    return format_roadmap_draft(draft) + f"\n\nApproval: `/approve {approval_id}`"


@tool
def learning_list_roadmaps(chat_id: str = "system") -> str:
    """List roadmap belajar."""
    rows = list_roadmaps(chat_id)
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
def learning_generate_today_plan(chat_id: str = "system") -> str:
    """Generate rencana belajar hari ini dari roadmap draft/aktif."""
    rows = list_roadmaps(chat_id)
    if not rows:
        return "Belum ada roadmap. Buat dulu dengan `buat roadmap belajar <topik>`."
    row = rows[0]
    return f"*Study Today*\nRoadmap: {row['title']}\n• Review target akhir\n• Kerjakan 1 task paling kecil\n• Catat hasil belajar ke Obsidian"


@tool
def learning_review_week(chat_id: str = "system") -> str:
    """Review belajar mingguan."""
    return "*Study Review Mingguan*\n• Apa yang selesai?\n• Apa yang masih membingungkan?\n• Resource apa yang paling membantu?\n• Apa fokus minggu depan?"


@tool
def learning_attach_resource(roadmap_id: int, title: str, url: str = "", resource_type: str = "web") -> str:
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
