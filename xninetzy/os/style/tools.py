from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.style.store import get_style_text, reset_style, set_style


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def style_set(description: str, sender_id: str = "", chat_id: str = "") -> str:
    """Atur gaya jawaban asisten (mis. 'jawab santai, teknis, langkah demi langkah')."""
    if not description.strip():
        return "Deskripsi gayanya apa? Contoh: `/style set santai, teknis, to the point`"
    set_style(_uid(sender_id, chat_id), description)
    return f"✅ Gaya jawaban diatur:\n“{description.strip()}”\n\nLihat: `/style show` · reset: `/style reset`"


@tool
def style_show(sender_id: str = "", chat_id: str = "") -> str:
    """Tampilkan gaya jawaban yang sedang aktif."""
    text = get_style_text(_uid(sender_id, chat_id))
    if not text:
        return "Belum ada gaya khusus (pakai default WhatsApp-friendly). Atur dengan `/style set <deskripsi>`."
    return f"*Gaya jawaban kamu:*\n“{text}”"


@tool
def style_reset(sender_id: str = "", chat_id: str = "") -> str:
    """Kembalikan gaya jawaban ke default."""
    reset_style(_uid(sender_id, chat_id))
    return "✅ Gaya jawaban dikembalikan ke default."
