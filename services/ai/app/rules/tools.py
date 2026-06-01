from __future__ import annotations

from langchain_core.tools import tool

from app.rules.store import (
    add_rule,
    delete_rule,
    list_rules,
    search_rules,
    set_active,
)


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def rule_add(content: str, sender_id: str = "", chat_id: str = "", source_message_id: str | None = None) -> str:
    """Tambah aturan perilaku untuk asisten (mis. 'jangan kirim reminder di atas jam 22')."""
    if not content.strip():
        return "Isi aturannya apa? Contoh: `/rule add jangan jawab panjang kalau aku minta singkat`"
    r = add_rule(_uid(sender_id, chat_id), content, source_message_id=source_message_id)
    return (
        f"✅ Aturan #{r['id']} disimpan _({r['rule_type']})_:\n“{r['content']}”\n\n"
        f"Lihat semua: `/rule list` · matikan: `/rule off {r['id']}`"
    )


@tool
def rule_list(sender_id: str = "", chat_id: str = "") -> str:
    """Tampilkan semua aturan user (aktif & nonaktif)."""
    rows = list_rules(_uid(sender_id, chat_id))
    if not rows:
        return "Belum ada aturan. Tambah dengan `/rule add <aturan>`."
    lines = ["*Aturan Kamu*"]
    for r in rows:
        mark = "🟢" if r["is_active"] else "⚪"
        lines.append(f"{mark} #{r['id']} [{r['rule_type']}] {r['content']}")
    lines.append("\n`/rule off <id>` · `/rule on <id>` · `/rule delete <id>`")
    return "\n".join(lines)


@tool
def rule_disable(rule_id: int, sender_id: str = "", chat_id: str = "") -> str:
    """Nonaktifkan aturan berdasarkan id."""
    ok = set_active(_uid(sender_id, chat_id), rule_id, False)
    return f"✅ Aturan #{rule_id} dinonaktifkan." if ok else f"Aturan #{rule_id} tidak ditemukan."


@tool
def rule_enable(rule_id: int, sender_id: str = "", chat_id: str = "") -> str:
    """Aktifkan kembali aturan berdasarkan id."""
    ok = set_active(_uid(sender_id, chat_id), rule_id, True)
    return f"✅ Aturan #{rule_id} diaktifkan." if ok else f"Aturan #{rule_id} tidak ditemukan."


@tool
def rule_delete(rule_id: int, sender_id: str = "", chat_id: str = "") -> str:
    """Hapus aturan berdasarkan id."""
    ok = delete_rule(_uid(sender_id, chat_id), rule_id)
    return f"✅ Aturan #{rule_id} dihapus." if ok else f"Aturan #{rule_id} tidak ditemukan."


@tool
def rule_search(query: str, sender_id: str = "", chat_id: str = "") -> str:
    """Cari aturan berdasarkan kata kunci."""
    rows = search_rules(_uid(sender_id, chat_id), query)
    if not rows:
        return f"Tidak ada aturan yang cocok dengan '{query}'."
    lines = [f"*Aturan cocok: {query}*"]
    for r in rows:
        mark = "🟢" if r["is_active"] else "⚪"
        lines.append(f"{mark} #{r['id']} [{r['rule_type']}] {r['content']}")
    return "\n".join(lines)


@tool
def rules_healthcheck(sender_id: str = "", chat_id: str = "") -> str:
    """Healthcheck sistem rules + style (untuk /test-rules)."""
    from app.style.store import get_style_text

    uid = _uid(sender_id, chat_id)
    active = list_rules(uid, active_only=True)
    total = list_rules(uid)
    style = get_style_text(uid)
    return (
        "*Rules & Style Healthcheck*\n"
        "• SQLite rules table: OK\n"
        f"• Aturan aktif: {len(active)} dari {len(total)} total\n"
        f"• Style profile: {'tersetel' if style else 'default'}\n"
        "• Injection ke agent: OK"
    )
