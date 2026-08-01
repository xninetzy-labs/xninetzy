from __future__ import annotations

import json

from langchain_core.tools import tool

from app.xninetzy.ecosystem.event_bus import record_event


@tool
def document_analyze(file_path: str) -> str:
    """Dry-run: klasifikasi dokumen (simple/complex) dan rencana tool ekstraksi tanpa ingest.

    Args:
        file_path: Path lokal dokumen (.pdf/.docx/.pptx/.xlsx/.txt/.md/.csv/.json)
    """
    from pathlib import Path

    from app.xninetzy.os.knowledge.extraction import analyze_document

    p = Path(file_path)
    if not p.exists():
        return f"❌ File tidak ditemukan: {file_path}"

    plan = analyze_document(file_path, filename=p.name)
    steps = []
    if plan.extract_tables:
        steps.append("tabel")
    if plan.use_ocr:
        steps.append("OCR")
    if plan.build_overview:
        steps.append("overview")
    extras = f" (+{', '.join(steps)})" if steps else ""
    return (
        f"🔎 *Analisis dokumen:* {p.name}\n"
        f"Strategi: *{plan.strategy}* | Extractor: `{plan.extractor}` | "
        f"Chunker: `{plan.chunker}`{extras}\n"
        f"Halaman: {plan.page_count}\n"
        f"Alasan: {plan.reason}"
    )


@tool
def document_ingest(
    file_path: str,
    title: str | None = None,
    source_type: str = "document",
    chat_id: str = "system",
) -> str:
    """Ingest dokumen penuh via router (structure-aware) ke knowledge base.

    Memilih extractor open-source sesuai kompleksitas dokumen, menyimpan metadata
    struktur (halaman, heading, tabel) per chunk, dan overview untuk dokumen kompleks.

    Args:
        file_path: Path lokal dokumen
        title: Judul (default: nama file)
        source_type: Tipe sumber
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.knowledge.ingestion import ingest_document

    result = ingest_document(file_path, title, source_type)
    status = result.get("status")
    if status == "error":
        return f"❌ Gagal ingest: {result.get('error')}"
    if status == "already_exists":
        return "ℹ️ Dokumen sudah ada di knowledge base."
    if status == "empty":
        return "⚠️ Tidak ada konten yang bisa diekstrak."

    record_event(
        chat_id,
        "pdf_ingested",
        "document",
        "note",
        str(result.get("source_id", "")),
        {"title": result.get("title"), "chunks": result.get("chunks", 0),
         "strategy": result.get("strategy")},
    )
    lines = [
        "✅ Dokumen diingest!",
        f"*{result['title']}*",
        f"Strategi: {result.get('strategy')}/{result.get('extractor')}",
        f"{result.get('pages', '?')} hal | {result['chunks']} chunk | "
        f"{result.get('tables', 0)} tabel | {result.get('images', 0)} gambar-OCR",
    ]
    if result.get("overview"):
        lines.append(f"\n📝 {result['overview']}")
    return "\n".join(lines)


@tool
def document_overview(source_id: int) -> str:
    """Tampilkan overview map-reduce dari dokumen yang sudah diingest.

    Args:
        source_id: ID sumber knowledge (dari document_catalog / document_ingest)
    """
    from app.xninetzy.db.sqlite import connect, init_db

    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT title, metadata_json FROM knowledge_sources WHERE id=?", (source_id,)
        ).fetchone()
    if not row:
        return f"❌ Sumber `{source_id}` tidak ditemukan."

    meta = json.loads(row["metadata_json"] or "{}")
    manifest = meta.get("manifest") or {}
    overview = manifest.get("overview") or {}
    summary = overview.get("summary")
    if not summary:
        return f"ℹ️ *{row['title']}* belum punya overview (dokumen simple atau overview nonaktif)."

    lines = [f"📄 *{row['title']}*", "", summary]
    key_points = overview.get("key_points") or []
    if key_points:
        lines.append("")
        lines.extend(f"• {kp}" for kp in key_points)
    return "\n".join(lines)


@tool
def document_tables(file_path: str, max_pages: int = 20) -> str:
    """Ekstrak tabel dari dokumen (PDF/DOCX/XLSX) sebagai markdown, tanpa ingest.

    Args:
        file_path: Path lokal dokumen
        max_pages: Batas halaman PDF yang dipindai
    """
    from pathlib import Path

    from app.xninetzy.interfaces.media.document_parser import _resolve_ext

    p = Path(file_path)
    if not p.exists():
        return f"❌ File tidak ditemukan: {file_path}"

    ext = _resolve_ext(p, None, p.name)
    tables = []
    if ext == ".pdf":
        from app.xninetzy.os.knowledge.extraction.extractors.tables import extract_pdf_tables

        tables = extract_pdf_tables(file_path, max_pages=max_pages)
    elif ext in (".docx", ".xlsx"):
        from app.xninetzy.os.knowledge.extraction.extractors.office import extract_office

        tables = extract_office(file_path).tables()
    else:
        return f"⚠️ Ekstraksi tabel belum didukung untuk {ext}."

    if not tables:
        return "ℹ️ Tidak ada tabel terdeteksi."

    parts = [f"📊 *{len(tables)} tabel* dari {p.name}:\n"]
    for i, t in enumerate(tables, 1):
        loc = f" (hal. {t.page})" if t.page else ""
        parts.append(f"**Tabel {i}{loc}:**\n{t.text}\n")
    return "\n".join(parts)


@tool
def document_catalog(limit: int = 20) -> str:
    """Daftar dokumen terekstrak beserta statistik struktur (halaman/tabel/gambar).

    Args:
        limit: Jumlah maksimal
    """
    from app.xninetzy.os.knowledge.ingestion import list_sources

    sources = list_sources(limit=limit)
    docs = []
    for s in sources:
        meta = json.loads(s.get("metadata_json") or "{}")
        manifest = meta.get("manifest")
        if manifest:
            docs.append((s, manifest))

    if not docs:
        return "Belum ada dokumen terstruktur di katalog."

    lines = [f"🗂️ *Document Catalog ({len(docs)}):*\n"]
    for s, m in docs:
        lines.append(
            f"`{s['id']}` *{s['title']}* — {m.get('strategy')}/{m.get('extractor')} | "
            f"{m.get('page_count', 0)} hal, {m.get('table_count', 0)} tabel, "
            f"{m.get('chunk_count', 0)} chunk"
        )
    return "\n".join(lines)
