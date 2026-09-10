from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging
from xninetzy.core.identity import normalize_chat_id
from xninetzy.os.notifications.notification_policy import should_notify_admin
from xninetzy.os.notifications.notification_templates import format_admin_notification

logger = logging.getLogger(__name__)


def owner_chat_id() -> str:
    """Resolve the owner's canonical chat identifier.

    Replaces the legacy WA-admin JID resolver. The owner is identified by
    OWNER_CHAT_ID (preferred) or the historical ADMIN_JID setting (kept
    for backward compatibility with installs that pre-date the pivot).
    """
    s = get_settings()
    raw = (s.OWNER_CHAT_ID or s.ADMIN_JID or "").strip()
    return normalize_chat_id(raw)


async def _persist_owner_notification(text: str, chat_id: str) -> bool:
    """Store the notification in the owner inbox as a captured note.

    Falls back to logging when the inbox is unavailable. Never raises.
    """
    try:
        from xninetzy.os.inbox.service import capture_item

        capture_item(text, kind="note", chat_id=chat_id or owner_chat_id())
        return True
    except Exception as exc:
        logger.warning("Owner inbox notification failed (logged only): %s", exc)
        logger.info("owner_notification: chat=%s text=%s", chat_id, text)
        return False


async def notify_admin(event_type: str, payload: dict | None = None, impact: str = "medium") -> bool:
    if not should_notify_admin(event_type, impact):
        return False
    chat_id = owner_chat_id()
    if not chat_id:
        return False
    text = format_admin_notification(event_type, payload or {})
    return await _persist_owner_notification(text, chat_id)


async def notify_admin_approval(
    approval_id: int,
    action_type: str,
    title: str,
    summary: str,
) -> bool:
    chat_id = owner_chat_id()
    if not chat_id:
        return False
    text = (
        f"*Approval Required #{approval_id}*\n\n"
        f"*Tipe:* {action_type}\n"
        f"*Judul:* {title}\n\n"
        f"{summary}"
    )
    fallback = (
        f"{text}\n\n"
        f"Balas `/approve {approval_id}` atau `/reject {approval_id}`."
    )
    ok = await _persist_owner_notification(fallback, chat_id)
    if not ok:
        logger.warning("Admin approval fallback failed for approval_id=%s", approval_id)
    return ok


@tool
async def admin_notify_progress(event_type: str, title: str = "", status: str = "", impact: str = "medium") -> str:
    """Kirim progress penting ke owner via inbox (tanpa spam)."""
    sent = await notify_admin(event_type, {"title": title, "status": status}, impact)
    return "✅ Notifikasi owner dikirim." if sent else "Notifikasi owner dilewati atau gagal."
