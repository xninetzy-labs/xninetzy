from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.notifications.notification_policy import should_notify_admin
from app.xninetzy.os.notifications.notification_templates import format_admin_notification

logger = logging.getLogger(__name__)


def admin_jid() -> str:
    jid = get_settings().ADMIN_JID.strip()
    if jid and not jid.endswith(("@s.whatsapp.net", "@g.us")):
        return f"{jid}@s.whatsapp.net"
    return jid


async def notify_admin(event_type: str, payload: dict | None = None, impact: str = "medium") -> bool:
    if not should_notify_admin(event_type, impact):
        return False
    jid = admin_jid()
    if not jid:
        return False
    text = format_admin_notification(event_type, payload or {})
    try:
        from app.xninetzy.interfaces.whatsapp.client import call_wa_tool
        await call_wa_tool("send_text_message", {"jid": jid, "text": text})
        return True
    except Exception as exc:
        logger.warning("Admin notification failed: %s", exc)
        return False


async def notify_admin_approval(
    approval_id: int,
    action_type: str,
    title: str,
    summary: str,
) -> bool:
    jid = admin_jid()
    if not jid:
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
    try:
        from app.xninetzy.interfaces.whatsapp.client import call_wa_tool

        await call_wa_tool(
            "send_verification_buttons",
            {
                "jid": jid,
                "text": fallback,
                "approval_id": str(approval_id),
                "footer": "Xninetzy OS verification",
            },
        )
        return True
    except Exception as button_error:
        logger.warning("Admin approval buttons failed: %s", button_error)
        try:
            from app.xninetzy.interfaces.whatsapp.client import call_wa_tool

            await call_wa_tool(
                "send_text_message",
                {"jid": jid, "text": fallback},
            )
            return True
        except Exception as fallback_error:
            logger.warning("Admin approval fallback failed: %s", fallback_error)
            return False


@tool
async def admin_notify_progress(event_type: str, title: str = "", status: str = "", impact: str = "medium") -> str:
    """Kirim progress penting ke admin WhatsApp tanpa spam."""
    sent = await notify_admin(event_type, {"title": title, "status": status}, impact)
    return "✅ Notifikasi admin dikirim." if sent else "Notifikasi admin dilewati atau gagal."
