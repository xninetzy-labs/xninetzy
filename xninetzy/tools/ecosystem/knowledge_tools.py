from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.ecosystem.event_bus import record_event


@tool
def knowledge_ingest_text(
    title: str,
    text: str,
    source_type: str = "manual_note",
    uri: str | None = None,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Simpan teks ke knowledge base untuk pencarian semantik di masa depan.

    Args:
        title: Judul sumber
        text: Konten teks
        source_type: hebat_pdf|obsidian_note|web_article|youtube_video|manual_note
        uri: URL atau referensi sumber (opsional)
        chat_id:  chat ID (dari context)
        idempotency_key: Kunci opsional agar retry tidak menggandakan ingest
    """
    from xninetzy.db.idempotency import idempotent_call
    from xninetzy.os.knowledge.ingestion import ingest_text

    payload = {"title": title, "source_type": source_type, "uri": uri}

    def _ingest() -> str:
        result = ingest_text(title, text, source_type, uri)
        status = result.get("status", "unknown")
        record_event(
            chat_id,
            "pdf_ingested",
            "manual",
            "note",
            result.get("source_id", ""),
            {"title": title, "chunks": result.get("chunks", 0), "status": status},
        )

        if status == "already_exists":
            return f"ℹ️ Sumber *{title}* sudah ada di knowledge base."
        if status == "empty":
            return "⚠️ Teks kosong, tidak ada yang diingest."
        if status == "ingested":
            return f"✅ Diingest ke knowledge:\n*{title}*\n{result.get('chunks', 0)} chunk | ID: `{result.get('source_id', '?')}`"
        return f"⚠️ Status ingest tidak dikenal: {status} ({result})"

    try:
        result, _created = idempotent_call(
            "knowledge_ingest_text", idempotency_key, payload, _ingest
        )
    except Exception as exc:
        return f"❌ Gagal ingest teks: {exc}"
    return result


@tool
def knowledge_ingest_file(
    file_path: str,
    title: str | None = None,
    source_type: str = "hebat_pdf",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Ingest file ke knowledge base (PDF, Markdown, TXT, JSON, CSV, DOCX, PPTX, XLSX).

    Args:
        file_path: Path lokal file
        title: Judul (default: nama file)
        source_type: Tipe sumber
<<<<<<< Updated upstream
        chat_id:  chat ID (dari context)
=======
        chat_id: WhatsApp chat ID (dari context)
>>>>>>> Stashed changes
        idempotency_key: Kunci opsional agar retry tidak menggandakan ingest
    """
    from pathlib import Path

    from xninetzy.db.idempotency import idempotent_call
    from xninetzy.os.knowledge.ingestion import (
        ingest_document,
        ingest_pdf,
        ingest_text,
    )

    payload = {"file_path": file_path, "title": title, "source_type": source_type}

    def _do() -> str:
        path = Path(file_path)
        if not path.exists():
            return f"❌ File tidak ditemukan: {file_path}"

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            result = ingest_pdf(file_path, title, source_type)
        elif suffix in {".md", ".markdown", ".txt", ".json", ".csv"}:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                return f"❌ Gagal membaca file teks: {e}"
            if not text.strip():
                return "⚠️ File kosong, tidak ada yang diingest."
            result = ingest_text(title or path.stem, text, source_type, uri=str(path))
        else:
            result = ingest_document(file_path, title=title, source_type=source_type)

        status = result.get("status", "unknown")
        if status == "error":
            return f"❌ Gagal ingest: {result.get('error')}"
        if status == "already_exists":
            return "ℹ️ File sudah ada di knowledge base."
        if status == "empty":
            return "⚠️ Isi file kosong, tidak ada yang diingest."
        if status == "ingested":
            record_event(
                chat_id,
                "file_ingested",
                "file",
                "note",
                str(result.get("source_id", "")),
                {"title": result.get("title"), "chunks": result.get("chunks", 0)},
            )
            return (
                f"✅ Diingest!\n"
                f"*{result.get('title')}*\n"
                f"{result.get('chunks', 0)} chunk"
            )
        return f"⚠️ Status ingest tidak dikenal: {status}"

    try:
        result, _created = idempotent_call(
            "knowledge_ingest_file", idempotency_key, payload, _do
        )
    except Exception as exc:
        return f"❌ Gagal ingest file: {exc}"
    return result


@tool
def knowledge_search(query: str, limit: int = 5) -> str:
    """Inspeksi evidence bundle terpilih dari knowledge base.

    Args:
        query: Pertanyaan atau kata kunci
        limit: Jumlah hasil (default: 5)
    """
    from xninetzy.os.knowledge.retrieval import (
        render_evidence_bundle,
        retrieve_evidence,
    )

    clamped = max(1, min(int(limit), 50))
    try:
        bundle = retrieve_evidence(query, limit=clamped)
    except Exception as exc:
        return f"❌ Gagal mencari evidence: {exc}"
    if not bundle.evidence:
        return "Tidak ada hasil di knowledge base untuk query tersebut."
    try:
        return render_evidence_bundle(bundle)
    except Exception as exc:
        return f"❌ Gagal render evidence bundle: {exc}"


@tool
async def knowledge_answer(query: str, chat_id: str = "system") -> str:
    """Jawab melalui retrieval, evidence selection, sintesis, dan validasi sitasi.

    Args:
        query: Pertanyaan yang ingin dijawab
        chat_id:  chat ID (dari context)
    """
    from xninetzy.os.knowledge.retrieval import answer_from_knowledge

    try:
        answer = await answer_from_knowledge(query)
    except Exception as exc:
        return f"❌ Gagal menjawab dari knowledge base: {exc}"
    try:
        record_event(
            chat_id,
            "knowledge_answered",
            "knowledge",
            "query",
            None,
            {"query": query[:500]},
        )
    except Exception:
        pass
    return answer


@tool
def knowledge_list_sources(source_type: str | None = None, limit: int = 20) -> str:
    """Tampilkan daftar sumber yang sudah diingest ke knowledge base.

    Args:
        source_type: Filter by type (opsional)
        limit: Jumlah maksimal
    """
    from xninetzy.os.knowledge.ingestion import list_sources

    clamped = max(1, min(int(limit), 200))
    try:
        sources = list_sources(source_type, clamped)
    except Exception as exc:
        return f"❌ Gagal membaca daftar sumber: {exc}"
    if not sources:
        return "Belum ada sumber di knowledge base."

    lines = [f"📚 *Knowledge Sources ({len(sources)}):*\n"]
    for s in sources:
        sid = s.get("id", "?")
        title = s.get("title", "?")
        stype = s.get("source_type", "?")
        created = s.get("created_at", "")[:10]
        lines.append(f"`{sid}` *{title}* ({stype}) — {created}")
    return "\n".join(lines)


@tool
def knowledge_rebuild_index() -> str:
    """Rebuild FAISS vector index dari semua knowledge chunks yang ada di database."""
    from xninetzy.os.knowledge.vector_store import rebuild_index

    try:
        count = rebuild_index()
    except Exception as exc:
        return f"❌ Gagal rebuild index: {exc}"
    return f"✅ Knowledge index di-rebuild: {count} vectors"
