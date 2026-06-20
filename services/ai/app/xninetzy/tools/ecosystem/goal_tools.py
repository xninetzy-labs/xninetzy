from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.ecosystem.event_bus import record_event
from app.xninetzy.os.life.goal_manager import (
    create_goal,
    get_goal,
    get_goal_logs,
    list_goals,
    log_progress,
    update_goal_status,
)


@tool
def goal_create(title: str, description: str = "", domain: str = "personal",
                horizon: str = "monthly", priority: str = "medium",
                due_date: str | None = None, chat_id: str = "system") -> str:
    """Buat goal baru dalam life OS.

    Args:
        title: Judul goal
        description: Deskripsi detail
        domain: learning|career|health|money|relationship|project|spiritual|personal
        horizon: daily|weekly|monthly|quarterly|yearly|lifetime
        priority: low|medium|high|critical
        due_date: Tanggal target (YYYY-MM-DD)
        chat_id: WhatsApp chat ID (dari context)
    """
    g = create_goal(title, description, domain, horizon, priority, due_date)
    record_event(chat_id, "goal_created", "whatsapp", "goal", str(g["id"]),
                 {"title": title, "domain": domain})

    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService
        from app.xninetzy.os.notes.template_service import TemplateService
        note = (
            f"---\ntype: goal\ndomain: {domain}\nstatus: active\n"
            f"horizon: {horizon}\npriority: {priority}\ndue: {due_date or ''}\n"
            f"created: {g['created_at']}\ntags: [goal, {domain}]\n---\n\n"
            f"# {title}\n\n## Why\n{description}\n\n## Target Metric\n\n"
            "## Current Progress\n\n## Milestones\n\n## Related Tasks\n\n"
            "## Daily Logs\n\n## AI Review\n"
        )
        path = f"Goals/{domain}/{title.replace('/', '-')[:50]}.md"
        ObsidianVaultService().create_note(path, note, overwrite=False)
    except Exception:
        pass

    return (
        f"✅ Goal dibuat!\n\n"
        f"*{title}*\nDomain: {domain} | Horizon: {horizon} | Priority: {priority}\n"
        f"ID: `{g['id']}`\nDeadline: {due_date or 'tidak ada'}"
    )


@tool
def goal_list(status: str = "active", domain: str | None = None) -> str:
    """Tampilkan daftar goals.

    Args:
        status: active|paused|completed|cancelled (default: active)
        domain: Filter by domain (opsional)
    """
    goals = list_goals(status=status, domain=domain, limit=15)
    if not goals:
        return f"Tidak ada goal dengan status '{status}'."

    lines = [f"🎯 *Goals ({status}):*\n"]
    for g in goals:
        due = f" — due: {g.get('due_date', '?')}" if g.get("due_date") else ""
        lines.append(
            f"`{g['id']}` *{g['title']}*\n"
            f"   {g.get('domain', '?')} | {g.get('horizon', '?')} | {g.get('priority', '?')}{due}"
        )
    return "\n".join(lines)


@tool
def goal_update_progress(goal_id: int, log_text: str, delta: float = 0,
                         mood: int | None = None, chat_id: str = "system") -> str:
    """Catat progres ke goal.

    Args:
        goal_id: ID goal
        log_text: Deskripsi progress hari ini
        delta: Nilai numerik progress (opsional)
        mood: Skor mood 1-5 (opsional)
        chat_id: WhatsApp chat ID (dari context)
    """
    g = get_goal(goal_id)
    if not g:
        return f"Goal ID `{goal_id}` tidak ditemukan."

    log_progress(goal_id, log_text, delta, mood)
    record_event(chat_id, "goal_progress_logged", "whatsapp", "goal", str(goal_id),
                 {"log": log_text[:100], "delta": delta})

    # Append to Obsidian daily note
    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService
        from app.xninetzy.tools.internal.datetime_info import get_now_info
        now = get_now_info()
        ObsidianVaultService().append_note(
            f"Daily/{now['date']}.md",
            f"**Goal Progress** [{g['title']}]: {log_text}",
        )
    except Exception:
        pass

    return f"✅ Progress goal *{g['title']}* dicatat.\n\n_{log_text}_"


@tool
def goal_review(goal_id: int) -> str:
    """Lihat review lengkap satu goal: logs, current value, sisa waktu.

    Args:
        goal_id: ID goal
    """
    g = get_goal(goal_id)
    if not g:
        return f"Goal ID `{goal_id}` tidak ditemukan."

    logs = get_goal_logs(goal_id, limit=5)
    log_lines = "\n".join(f"• {l['created_at'][:10]}: {l['log_text']}" for l in logs) or "Belum ada log."

    progress_str = ""
    if g.get("target_value"):
        cur = g.get("current_value") or 0
        pct = cur / g["target_value"] * 100
        progress_str = f"\nProgress: {cur} / {g['target_value']} {g.get('unit', '')} ({pct:.0f}%)"

    return (
        f"🎯 *{g['title']}*\n"
        f"Domain: {g.get('domain')} | Status: {g.get('status')}\n"
        f"Horizon: {g.get('horizon')} | Priority: {g.get('priority')}\n"
        f"Deadline: {g.get('due_date', 'tidak ada')}{progress_str}\n\n"
        f"*Log terbaru:*\n{log_lines}"
    )
