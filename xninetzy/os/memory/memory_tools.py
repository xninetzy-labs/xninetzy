from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.memory.memory_store import (
    add_memory,
    forget_memory,
    list_memories,
    search_memories,
    update_memory,
)


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def memory_add(content: str, sender_id: str = "", chat_id: str = "", source_message_id: str | None = None) -> str:
    """Simpan memory tentang user (preferensi, profil belajar, konteks proyek, dll)."""
    if not content.strip():
        return "Mau aku ingat apa? Contoh: `/remember aku lagi belajar APSI minggu ini`"
    m = add_memory(_uid(sender_id, chat_id), content, source_message_id=source_message_id)
    return f"🧠 Disimpan ke memory #{m['id']} _({m['memory_type']})_:\n“{m['content']}”"


@tool
def memory_search(query: str, sender_id: str = "", chat_id: str = "") -> str:
    """Cari memory user secara semantik."""
    rows = search_memories(_uid(sender_id, chat_id), query)
    if not rows:
        return f"Tidak ada memory yang relevan dengan '{query}'."
    lines = [f"*Memory: {query}*"]
    for m in rows:
        lines.append(f"#{m['id']} [{m['memory_type']}] {m['content']}")
    return "\n".join(lines)


@tool
def memory_list(sender_id: str = "", chat_id: str = "") -> str:
    """Tampilkan memory user."""
    rows = list_memories(_uid(sender_id, chat_id))
    if not rows:
        return "Belum ada memory. Tambah dengan `/remember <isi>`."
    lines = ["*Memory Kamu*"]
    for m in rows:
        lines.append(f"#{m['id']} [{m['memory_type']}] {m['content']}")
    lines.append("\n`/memory search <query>` · `/forget-memory <id>`")
    return "\n".join(lines)


@tool
def memory_update_tool(memory_id: int, content: str, sender_id: str = "", chat_id: str = "") -> str:
    """Perbarui isi memory berdasarkan id."""
    ok = update_memory(_uid(sender_id, chat_id), memory_id, content)
    return f"✅ Memory #{memory_id} diperbarui." if ok else f"Memory #{memory_id} tidak ditemukan."


@tool
def memory_forget(memory_id: int, sender_id: str = "", chat_id: str = "") -> str:
    """Lupakan (nonaktifkan) memory berdasarkan id."""
    ok = forget_memory(_uid(sender_id, chat_id), memory_id)
    return f"✅ Memory #{memory_id} dilupakan." if ok else f"Memory #{memory_id} tidak ditemukan."


@tool
def memory_get_context(query: str, sender_id: str = "", chat_id: str = "") -> str:
    """Ambil memory relevan sebagai konteks (dipakai agent sebelum menjawab)."""
    rows = search_memories(_uid(sender_id, chat_id), query, limit=5)
    if not rows:
        return "Tidak ada memory relevan."
    return "\n".join(f"• [{m['memory_type']}] {m['content']}" for m in rows)
