from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.knowledge.chunking import chunk_text
from app.xninetzy.os.knowledge.vector_store import (
    add_chunks_to_index,
    add_structured_chunks_to_index,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now().isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def source_exists_by_hash(sha256: str) -> bool:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM knowledge_sources WHERE sha256=?", (sha256,)
        ).fetchone()
    return row is not None


def create_source(
    source_type: str,
    title: str,
    sha256: str,
    uri: str | None = None,
    local_path: str | None = None,
    obsidian_path: str | None = None,
    metadata: dict | None = None,
) -> int:
    init_db()
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO knowledge_sources
              (source_type, title, uri, local_path, obsidian_path, sha256, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                source_type,
                title,
                uri,
                local_path,
                obsidian_path,
                sha256,
                json.dumps(metadata or {}),
                now,
                now,
            ),
        )
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            "SELECT id FROM knowledge_sources WHERE sha256=?", (sha256,)
        ).fetchone()
        return row["id"] if row else 0


def ingest_text(
    title: str,
    text: str,
    source_type: str = "manual_note",
    uri: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Ingest plain text into knowledge store. Returns summary dict."""
    sha = _sha256_text(text)
    if source_exists_by_hash(sha):
        logger.info("Source already ingested (sha256=%s): %s", sha[:8], title)
        return {"status": "already_exists", "title": title, "chunks": 0}

    source_id = create_source(source_type, title, sha, uri=uri, metadata=metadata)
    chunks = chunk_text(text)
    if not chunks:
        return {"status": "empty", "title": title, "chunks": 0}

    add_chunks_to_index(source_id, chunks)
    logger.info("Ingested '%s': %d chunks, source_id=%d", title, len(chunks), source_id)

    return {
        "status": "ingested",
        "source_id": source_id,
        "title": title,
        "chunks": len(chunks),
    }


def ingest_document(
    file_path: str,
    title: str | None = None,
    source_type: str = "document",
    metadata: dict | None = None,
    mime_type: str | None = None,
) -> dict:
    """Router-driven ingestion for any supported document.

    Runs the extraction ecosystem (classify simple/complex, pick open-source
    extractor, structure-aware chunk, optional map-reduce overview), stores a
    ``DocumentManifest`` on the source and structural metadata on each chunk.
    """
    s = get_settings()
    if not getattr(s, "DOC_EXTRACTION_ENABLED", True):
        # Feature-flag off: fall back to the flat PDF/text path for PDFs.
        return ingest_pdf(file_path, title=title, source_type=source_type, metadata=metadata)

    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "error": "File not found"}

    sha = _sha256_file(path)
    if source_exists_by_hash(sha):
        return {"status": "already_exists", "title": title or path.name, "chunks": 0}

    from app.xninetzy.os.knowledge.extraction import (
        build_document_chunks,
        build_overview,
        extract_document,
    )
    from app.xninetzy.os.knowledge.extraction.schemas import DocumentManifest

    try:
        doc, plan = extract_document(file_path, mime_type=mime_type, filename=path.name)
    except Exception as e:
        logger.warning("Structured extraction failed for %s: %s — flat fallback", path.name, e)
        return ingest_pdf(file_path, title=title, source_type=source_type, metadata=metadata)

    chunks = build_document_chunks(doc, plan)
    if not chunks:
        return {"status": "empty", "title": title or path.stem, "chunks": 0}

    overview = None
    if plan.build_overview and getattr(s, "DOC_OVERVIEW_ENABLED", True):
        overview = build_overview(doc)

    manifest = DocumentManifest(
        strategy=plan.strategy,
        extractor=plan.extractor,
        chunker=plan.chunker,
        page_count=doc.page_count,
        table_count=doc.table_count,
        image_count=doc.image_count,
        chunk_count=len(chunks),
        overview=overview,
    )

    source_title = title or path.stem
    source_meta = {**(metadata or {}), "manifest": manifest.to_dict(), "plan": plan.to_dict()}
    source_id = create_source(
        source_type, source_title, sha, local_path=str(path), metadata=source_meta
    )
    add_structured_chunks_to_index(source_id, chunks)

    logger.info(
        "Ingested document '%s' via %s/%s: %d chunks, source_id=%d",
        source_title, plan.strategy, plan.extractor, len(chunks), source_id,
    )
    return {
        "status": "ingested",
        "source_id": source_id,
        "title": source_title,
        "chunks": len(chunks),
        "strategy": plan.strategy,
        "extractor": plan.extractor,
        "pages": doc.page_count,
        "tables": doc.table_count,
        "images": doc.image_count,
        "overview": overview.summary if overview else "",
    }


def ingest_pdf(
    file_path: str,
    title: str | None = None,
    source_type: str = "hebat_pdf",
    metadata: dict | None = None,
) -> dict:
    """Read a PDF and ingest its text."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "error": "File not found"}

    sha = _sha256_file(path)
    if source_exists_by_hash(sha):
        return {"status": "already_exists", "title": title or path.name, "chunks": 0}

    try:
        from app.xninetzy.os.academic.hebat.pdf_reader import read_pdf_text

        result = read_pdf_text(file_path)
        text = result.get("text", "")
        if not text:
            return {"status": "error", "error": "Could not extract text from PDF"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

    source_title = title or path.stem
    source_id = create_source(
        source_type, source_title, sha, local_path=str(path), metadata=metadata
    )
    chunks = chunk_text(text)
    add_chunks_to_index(source_id, chunks)

    logger.info("Ingested PDF '%s': %d chunks", source_title, len(chunks))
    return {
        "status": "ingested",
        "source_id": source_id,
        "title": source_title,
        "chunks": len(chunks),
        "pages": result.get("pages", 0),
    }


def list_sources(source_type: str | None = None, limit: int = 50) -> list[dict]:
    init_db()
    with connect() as conn:
        if source_type:
            rows = conn.execute(
                "SELECT * FROM knowledge_sources WHERE source_type=? ORDER BY created_at DESC LIMIT ?",
                (source_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM knowledge_sources ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]
