from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.jobs.service import get_data_freshness, owner_notification_jid
from app.xninetzy.os.jobs.store import JobStore


@tool
def os_job_status(limit: int = 10) -> str:
    """Lihat status briefing/review/sync terjadwal dan freshness data owner."""
    rows = JobStore().list_recent(max(1, min(limit, 30)))
    freshness = get_data_freshness()
    target = owner_notification_jid()
    hebat = freshness["hebat"]
    lines = ["*Xninetzy OS Scheduler*", f"Target: {target or 'belum dikonfigurasi'}"]
    if hebat["age_minutes"] is None:
        lines.append(f"HEBAT freshness: {hebat['status']}")
    else:
        lines.append(
            f"HEBAT freshness: {hebat['status']} ({hebat['age_minutes']} menit)"
        )
    if not rows:
        lines.append("Belum ada job run.")
        return "\n".join(lines)
    lines.append("\n*Job terbaru:*")
    for row in rows:
        detail = f" — {row['last_error'][:80]}" if row.get("last_error") else ""
        lines.append(
            f"• {row['job_key']} [{row['status']}] attempt {row['attempts']}{detail}"
        )
    return "\n".join(lines)
