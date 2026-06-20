from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool


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


def _friendly_error(message: str) -> str:
    lower = message.lower()
    if any(k in lower for k in ["forbidden", "admin", "not-authorized", "unauthorized"]):
        return "⚠️ Gagal. Pastikan bot sudah jadi admin grup."
    return f"⚠️ Gagal menjalankan aksi WhatsApp: {message}"
