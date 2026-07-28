from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.ecosystem.event_bus import record_event


@tool
def knowledge_ingest_text(
    title: str,
    text: str,
    source_type: str = "manual_note",
    uri: str | None = None,
    chat_id: str = "system",
) -> str:
    """Simpan teks ke knowledge base untuk pencarian semantik di masa depan.

    Args:
        title: Judul sumber
        text: Konten teks
        source_type: hebat_pdf|obsidian_note|web_article|youtube_video|manual_note
        uri: URL atau referensi sumber (opsional)
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.knowledge.ingestion import ingest_text

    result = ingest_text(title, text, source_type, uri)
    record_event(
        chat_id,
        "pdf_ingested",
        "manual",
        "note",
        result.get("source_id", ""),
        {"title": title, "chunks": result.get("chunks", 0)},
    )

    if result["status"] == "already_exists":
        return f"ℹ️ Sumber *{title}* sudah ada di knowledge base."
    if result["status"] == "empty":
        return "⚠️ Teks kosong, tidak ada yang diingest."

    return f"✅ Diingest ke knowledge:\n*{title}*\n{result['chunks']} chunk | ID: `{result.get('source_id', '?')}`"


@tool
def knowledge_ingest_file(
    file_path: str,
    title: str | None = None,
    source_type: str = "hebat_pdf",
    chat_id: str = "system",
) -> str:
    """Ingest file PDF ke knowledge base.

    Args:
        file_path: Path lokal file PDF
        title: Judul (default: nama file)
        source_type: Tipe sumber
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.knowledge.ingestion import ingest_pdf

    result = ingest_pdf(file_path, title, source_type)

    if result.get("status") == "error":
        return f"❌ Gagal ingest: {result.get('error')}"
    if result["status"] == "already_exists":
        return "ℹ️ File sudah ada di knowledge base."

    record_event(
        chat_id,
        "pdf_ingested",
        "file",
        "note",
        str(result.get("source_id", "")),
        {"title": result.get("title"), "chunks": result.get("chunks", 0)},
    )
    return (
        f"✅ PDF diingest!\n"
        f"*{result['title']}*\n"
        f"{result.get('pages', '?')} halaman | {result['chunks']} chunk"
    )


@tool
def knowledge_search(query: str, limit: int = 5) -> str:
    """Inspeksi evidence bundle terpilih dari knowledge base.

    Args:
        query: Pertanyaan atau kata kunci
        limit: Jumlah hasil (default: 5)
    """
    from app.xninetzy.os.knowledge.retrieval import (
        render_evidence_bundle,
        retrieve_evidence,
    )

    bundle = retrieve_evidence(query, limit=limit)
    if not bundle.evidence:
        return "Tidak ada hasil di knowledge base untuk query tersebut."
    return render_evidence_bundle(bundle)


@tool
async def knowledge_answer(query: str, chat_id: str = "system") -> str:
    """Jawab melalui retrieval, evidence selection, sintesis, dan validasi sitasi.

    Args:
        query: Pertanyaan yang ingin dijawab
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.knowledge.retrieval import answer_from_knowledge

    answer = await answer_from_knowledge(query)
    record_event(
        chat_id,
        "knowledge_answered",
        "knowledge",
        "query",
        None,
        {"query": query[:500]},
    )
    return answer


@tool
def knowledge_list_sources(source_type: str | None = None, limit: int = 20) -> str:
    """Tampilkan daftar sumber yang sudah diingest ke knowledge base.

    Args:
        source_type: Filter by type (opsional)
        limit: Jumlah maksimal
    """
    from app.xninetzy.os.knowledge.ingestion import list_sources

    sources = list_sources(source_type, limit)
    if not sources:
        return "Belum ada sumber di knowledge base."

    lines = [f"📚 *Knowledge Sources ({len(sources)}):*\n"]
    for s in sources:
        lines.append(
            f"`{s['id']}` *{s['title']}* ({s['source_type']}) — {s['created_at'][:10]}"
        )
    return "\n".join(lines)


@tool
def knowledge_rebuild_index() -> str:
    """Rebuild FAISS vector index dari semua knowledge chunks yang ada di database."""
    from app.xninetzy.os.knowledge.vector_store import rebuild_index

    count = rebuild_index()
    return f"✅ Knowledge index di-rebuild: {count} vectors"
