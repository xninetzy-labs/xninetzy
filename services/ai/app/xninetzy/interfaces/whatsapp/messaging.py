from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.interfaces.whatsapp.client import (
    WaToolError,
    call_wa_tool,
    download_media_message,
    get_media_content,
)
from app.xninetzy.os.notifications.admin_notifier import (
    admin_jid,
    notify_admin_approval,
)


def _admin_jid() -> str:
    return admin_jid()


async def _send_admin_buttons(approval_id: int, text: str) -> None:
    sent = await notify_admin_approval(
        approval_id=approval_id,
        action_type="admin_verification",
        title="Verifikasi admin",
        summary=text,
    )
    if not sent:
        raise WaToolError("Permintaan verifikasi tidak dapat dikirim ke ADMIN_JID.")


@tool
async def wa_pin_message(
    jid: str,
    message_id: str,
    from_me: bool = False,
    participant: str | None = None,
) -> str:
    """Pin pesan di chat atau grup WhatsApp.

    Biasanya dipanggil saat user reply ke pesan dan ketik "pin".
    Gunakan quoted_message_id dan quoted_participant dari konteks.

    Args:
        jid: Chat atau group JID (dari context chat_id)
        message_id: ID pesan yang akan dipin (dari context quoted_message_id)
        from_me: True jika pesan dari bot sendiri (dari context is_reply_to_bot)
        participant: JID pengirim pesan untuk grup (dari context quoted_participant)
    """
    try:
        await call_wa_tool(
            "pin_message",
            {
                "jid": jid,
                "message_id": message_id,
                "duration": 604800,
                "from_me": from_me,
                "participant": participant,
            },
        )
        return "✅ Pesan berhasil dipin."
    except WaToolError as e:
        return _friendly_error(str(e))


@tool
async def wa_set_announce(group_jid: str, announce: bool) -> str:
    """Toggle mode announcement grup WhatsApp (hanya admin yang bisa chat).

    Args:
        group_jid: JID grup (harus diakhiri @g.us)
        announce: True untuk aktifkan announcement mode, False untuk matikan
    """
    if not group_jid.endswith("@g.us"):
        return "⚠️ Aksi ini hanya bisa dipakai di grup."
    try:
        await call_wa_tool("set_group_announce", {"group_jid": group_jid, "announce": announce})
        if announce:
            return "✅ Grup sekarang mode announcement — hanya admin yang bisa kirim pesan."
        return "✅ Mode announcement dimatikan — semua member bisa chat lagi."
    except WaToolError as e:
        return _friendly_error(str(e))


@tool
async def wa_send_text(jid: str, text: str) -> str:
    """Kirim pesan teks ke JID WhatsApp tertentu.

    Args:
        jid: WhatsApp JID penerima (format: 628xxx@s.whatsapp.net atau xxx@g.us)
        text: Isi pesan yang akan dikirim
    """
    try:
        await call_wa_tool("send_text_message", {"jid": jid, "text": text})
        return f"✅ Pesan berhasil dikirim ke {jid}"
    except WaToolError as e:
        return _friendly_error(str(e))


@tool
async def wa_send_admin_verification(approval_id: int, text: str) -> str:
    """Kirim approval owner-scoped ke admin WhatsApp dengan tombol dan fallback command."""
    try:
        await _send_admin_buttons(approval_id, text)
        return "✅ Permintaan verifikasi dikirim ke admin."
    except WaToolError as error:
        return _friendly_error(str(error))


@tool
async def wa_forward_media_to_admin(
    message_id: str,
    approval_id: int,
    caption: str = "Media membutuhkan verifikasi admin.",
    chat_id: str = "system",
) -> str:
    """Teruskan image/document dari chat asal ke admin lalu kirim tombol verifikasi."""
    jid = _admin_jid()
    if not jid:
        return "⚠️ ADMIN_JID belum dikonfigurasi."
    downloaded = await download_media_message(chat_id, message_id)
    if not downloaded.get("ok"):
        return f"⚠️ Media tidak dapat diambil: {downloaded.get('error', 'tidak tersedia')}"
    content = await get_media_content(chat_id, message_id)
    if not content.get("ok"):
        return f"⚠️ Konten media tidak tersedia: {content.get('error', 'unknown')}"
    media_type = content.get("media_type")
    source = content.get("content_base64")
    if media_type == "image":
        tool_name = "send_image"
        payload = {"jid": jid, "source": source, "caption": caption}
    elif media_type == "document":
        tool_name = "send_document"
        payload = {
            "jid": jid,
            "source": source,
            "filename": content.get("filename") or f"document_{message_id}",
            "mimetype": content.get("mime_type") or "application/octet-stream",
        }
    else:
        return "⚠️ Verifikasi admin saat ini hanya mendukung image dan document."
    try:
        await call_wa_tool(tool_name, payload)
        await _send_admin_buttons(approval_id, caption)
    except WaToolError as error:
        return _friendly_error(str(error))
    return "✅ Media dan tombol verifikasi dikirim ke admin."


def _friendly_error(message: str) -> str:
    lower = message.lower()
    if any(k in lower for k in ["forbidden", "admin", "not-authorized", "unauthorized"]):
        return "⚠️ Gagal. Pastikan bot sudah jadi admin grup."
    return f"⚠️ Gagal menjalankan aksi WhatsApp: {message}"
