from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect

_ACTIVE_STATUSES = ("planned", "planning", "subplanning", "web_searching", "source_ranking", "brief_writing")


def count_active_runs(chat_id: str) -> int:
    placeholders = ",".join("?" for _ in _ACTIVE_STATUSES)
    with connect() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM research_sessions WHERE chat_id=? AND status IN ({placeholders})",
            (chat_id, *_ACTIVE_STATUSES),
        ).fetchone()
    return int(row["n"]) if row else 0


def check_resource_guards(chat_id: str) -> tuple[bool, str]:
    settings = get_settings()
    limit = settings.DEEP_RESEARCH_MAX_CONCURRENT_PER_CHAT
    if limit > 0 and count_active_runs(chat_id) >= limit:
        return False, "max_concurrent"
    return True, "ok"


def resource_guard_denied_message(reason: str = "max_concurrent") -> str:
    if reason == "max_concurrent":
        return (
            "Deep research lain masih berjalan di chat ini. "
            "Tunggu sampai selesai sebelum memulai yang baru."
        )
    return "Deep research diblokir oleh batas resource. Coba lagi nanti."
