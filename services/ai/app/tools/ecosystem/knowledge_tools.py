from __future__ import annotations

from langchain_core.tools import tool

from app.ecosystem.event_bus import record_event


@tool
def knowledge_ingest_text(title: str, text: str, source_type: str = "manual_note",
                          uri: str | None = None, chat_id: str = "system") -> str:
    """Simpan teks ke knowledge base untuk pencarian semantik di masa depan.

    Args:
        title: Judul sumber
        text: Konten teks
        source_type: hebat_pdf|obsidian_note|web_article|youtube_video|manual_note
        uri: URL atau referensi sumber (opsional)
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.knowledge.ingestion import ingest_text
    result = ingest_text(title, text, source_type, uri)
    record_event(chat_id, "pdf_ingested", "manual", "note", result.get("source_id", ""),
                 {"title": title, "chunks": result.get("chunks", 0)})

    if result["status"] == "already_exists":
        return f"ℹ️ Sumber *{title}* sudah ada di knowledge base."
    if result["status"] == "empty":
        return "⚠️ Teks kosong, tidak ada yang diingest."

    return f"✅ Diingest ke knowledge:\n*{title}*\n{result['chunks']} chunk | ID: `{result.get('source_id', '?')}`"


@tool
def knowledge_ingest_file(file_path: str, title: str | None = None,
                          source_type: str = "hebat_pdf",
                          chat_id: str = "system") -> str:
    """Ingest file PDF ke knowledge base.

    Args:
        file_path: Path lokal file PDF
        title: Judul (default: nama file)
        source_type: Tipe sumber
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.knowledge.ingestion import ingest_pdf
    result = ingest_pdf(file_path, title, source_type)

    if result.get("status") == "error":
        return f"❌ Gagal ingest: {result.get('error')}"
    if result["status"] == "already_exists":
        return f"ℹ️ File sudah ada di knowledge base."

    record_event(chat_id, "pdf_ingested", "file", "note", str(result.get("source_id", "")),
                 {"title": result.get("title"), "chunks": result.get("chunks", 0)})
    return (
        f"✅ PDF diingest!\n"
        f"*{result['title']}*\n"
        f"{result.get('pages', '?')} halaman | {result['chunks']} chunk"
    )


@tool
def knowledge_search(query: str, limit: int = 5) -> str:
    """Cari di knowledge base menggunakan semantic/keyword search.

    Args:
        query: Pertanyaan atau kata kunci
        limit: Jumlah hasil (default: 5)
    """
    from app.knowledge.vector_store import semantic_search
    results = semantic_search(query, limit=limit)
    if not results:
        return "Tidak ada hasil di knowledge base untuk query tersebut."

    lines = [f"🔍 *Knowledge search:* `{query}`\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "?")
        source_type = r.get("source_type", "?")
        text_preview = r.get("text", "")[:200]
        lines.append(f"*[{i}] {title}* ({source_type})\n{text_preview}\n")
    return "\n".join(lines)


@tool
def knowledge_answer(query: str, chat_id: str = "system") -> str:
    """Jawab pertanyaan berdasarkan knowledge base yang sudah diingest.

    Args:
        query: Pertanyaan yang ingin dijawab
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.knowledge.rag import build_rag_context
    context = build_rag_context(query)
    if not context:
        return (
            "Tidak ada knowledge relevan ditemukan untuk menjawab pertanyaan ini.\n"
            "Coba ingest materi dulu dengan `knowledge_ingest_file` atau `knowledge_ingest_text`."
        )
    return context + f"\n\n_Pertanyaan: {query}_\n_(Jawab berdasarkan konteks di atas menggunakan pengetahuanmu)_"


@tool
def knowledge_list_sources(source_type: str | None = None, limit: int = 20) -> str:
    """Tampilkan daftar sumber yang sudah diingest ke knowledge base.

    Args:
        source_type: Filter by type (opsional)
        limit: Jumlah maksimal
    """
    from app.knowledge.ingestion import list_sources
    sources = list_sources(source_type, limit)
    if not sources:
        return "Belum ada sumber di knowledge base."

    lines = [f"📚 *Knowledge Sources ({len(sources)}):*\n"]
    for s in sources:
        lines.append(f"`{s['id']}` *{s['title']}* ({s['source_type']}) — {s['created_at'][:10]}")
    return "\n".join(lines)


@tool
def knowledge_rebuild_index() -> str:
    """Rebuild FAISS vector index dari semua knowledge chunks yang ada di database."""
    from app.knowledge.vector_store import rebuild_index
    count = rebuild_index()
    return f"✅ Knowledge index di-rebuild: {count} vectors"
