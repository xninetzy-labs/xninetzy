from __future__ import annotations

from langchain_core.tools import tool

from app.core.config import get_settings
from app.core.logging import logging
from app.notifications.notification_policy import should_notify_admin
from app.notifications.notification_templates import format_admin_notification

logger = logging.getLogger(__name__)


async def notify_admin(event_type: str, payload: dict | None = None, impact: str = "medium") -> bool:
    if not should_notify_admin(event_type, impact):
        return False
    settings = get_settings()
    jid = settings.ADMIN_JID or settings.HEBAT_NOTIFY_CHAT_ID
    if not jid:
        return False
    if not jid.endswith(("@s.whatsapp.net", "@g.us")):
        jid = f"{jid}@s.whatsapp.net"
    text = format_admin_notification(event_type, payload or {})
    try:
        from app.wa_tools.client import call_wa_tool
        await call_wa_tool("send_text_message", {"jid": jid, "text": text})
        return True
    except Exception as exc:
        logger.warning("Admin notification failed: %s", exc)
        return False


@tool
async def admin_notify_progress(event_type: str, title: str = "", status: str = "", impact: str = "medium") -> str:
    """Kirim progress penting ke admin WhatsApp tanpa spam."""
    sent = await notify_admin(event_type, {"title": title, "status": status}, impact)
    return "✅ Notifikasi admin dikirim." if sent else "Notifikasi admin dilewati atau gagal."
