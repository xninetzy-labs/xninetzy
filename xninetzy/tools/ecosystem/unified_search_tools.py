from __future__ import annotations

from langchain_core.tools import tool


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def unified_search(
    query: str,
    limit: int = 5,
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """Cari lintas sumber: knowledge, Obsidian vault, graph RAG, dan memory.

    Args:
        query: Kata kunci pencarian
        limit: Jumlah hasil per sumber (default 5)
        sender_id: WhatsApp sender ID (dari context)
        chat_id: WhatsApp chat ID (dari context)
    """
    query = query.strip()
    if not query:
        return "Query kosong. Contoh: `/cari <topik>`"
    per_source = max(1, min(limit, 10))
    sections: list[str] = [f"🔎 *Unified Search*: {query}"]

    try:
        from app.xninetzy.os.knowledge.retrieval import retrieve_evidence

        bundle = retrieve_evidence(query, limit=per_source)
        items = [e for e in bundle.evidence]
        if items:
            lines = [f"📚 *Knowledge ({len(items)}):*"]
            for e in items:
                lines.append(f"- [{e.citation}] {e.title} ({e.source_type})")
            sections.append("\n".join(lines))
    except Exception as e:
        sections.append(f"📚 Knowledge: error ({e})")

    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService

        notes = ObsidianVaultService().search_notes(query, limit=per_source)
        if notes:
            lines = [f"🗂️ *Vault ({len(notes)}):*"]
            for n in notes:
                lines.append(f"- `{n['path']}` — {n.get('preview', '')[:120]}")
            sections.append("\n".join(lines))
    except Exception as e:
        sections.append(f"🗂️ Vault: error ({e})")

    try:
        from app.xninetzy.os.graph.graph_store import search_nodes

        nodes = search_nodes(query, limit=per_source)
        if nodes:
            lines = [f"🕸️ *Graph ({len(nodes)}):*"]
            for n in nodes:
                lines.append(f"- `{n['node_type']}` {n['title']}")
            sections.append("\n".join(lines))
    except Exception as e:
        sections.append(f"🕸️ Graph: error ({e})")

    try:
        from app.xninetzy.os.memory.memory_store import search_memories

        memories = search_memories(_uid(sender_id, chat_id), query, limit=per_source)
        if memories:
            lines = [f"🧠 *Memory ({len(memories)}):*"]
            for m in memories:
                lines.append(f"- #{m['id']} [{m['memory_type']}] {m['content']}")
            sections.append("\n".join(lines))
    except Exception as e:
        sections.append(f"🧠 Memory: error ({e})")

    if len(sections) == 1:
        return f"{sections[0]}\n\nTidak ada hasil untuk '{query}' di knowledge, vault, graph, atau memory."
    return "\n\n".join(sections)
