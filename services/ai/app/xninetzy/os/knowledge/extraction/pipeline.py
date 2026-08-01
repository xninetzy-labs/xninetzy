"""Extraction pipeline — orchestrator that ties the ecosystem together.

``extract_document`` runs the router, dispatches to the chosen open-source
extractor, and returns the ``StructuredDocument`` together with the
``ExtractionPlan`` that produced it. ``build_document_chunks`` additionally
turns that into retrieval-ready ``ContextualChunk``s using the chunker named by
the plan. No heavy/vision libraries are ever imported here.
"""
from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.chunking import chunk_text
from app.xninetzy.os.knowledge.extraction.extractors import (
    extract_office,
    extract_pdf_structured,
    extract_pdf_text,
    extract_plain_text,
)
from app.xninetzy.os.knowledge.extraction.router import analyze_document
from app.xninetzy.os.knowledge.extraction.schemas import (
    ContextualChunk,
    ExtractionPlan,
    StructuredDocument,
)
from app.xninetzy.os.knowledge.extraction.structure_chunker import chunk_structured

logger = logging.getLogger(__name__)


def extract_document(
    path: str,
    mime_type: str | None = None,
    filename: str | None = None,
    plan: ExtractionPlan | None = None,
) -> tuple[StructuredDocument, ExtractionPlan]:
    """Route + extract. Returns (document, plan)."""
    s = get_settings()
    if plan is None:
        plan = analyze_document(path, mime_type, filename)

    max_pages = getattr(s, "DOC_MAX_PAGES", None)

    if plan.extractor == "plain_text" or plan.extractor == "unsupported":
        doc = extract_plain_text(path)
    elif plan.extractor == "office":
        doc = extract_office(path, extract_tables=plan.extract_tables)
    elif plan.extractor == "pdf_text":
        doc = extract_pdf_text(path, max_pages=max_pages)
    elif plan.extractor == "pdf_structured":
        doc = extract_pdf_structured(
            path,
            use_ocr=plan.use_ocr,
            extract_tables=plan.extract_tables,
            max_pages=max_pages,
        )
    else:  # pragma: no cover - defensive; router only emits the above
        logger.warning("Unknown extractor %s — falling back to plain_text", plan.extractor)
        doc = extract_plain_text(path)

    logger.info(
        "Extracted %s via %s/%s: %d blocks, %d pages, %d tables, %d images",
        filename or path,
        plan.strategy,
        plan.extractor,
        len(doc.blocks),
        doc.page_count,
        doc.table_count,
        doc.image_count,
    )
    return doc, plan


def build_document_chunks(
    doc: StructuredDocument, plan: ExtractionPlan
) -> list[ContextualChunk]:
    """Turn a StructuredDocument into ContextualChunks per the plan's chunker."""
    if plan.chunker == "structure_aware":
        return chunk_structured(doc)
    # flat: pack full text, wrap each piece as a ContextualChunk with light meta.
    return [
        ContextualChunk(text=piece, metadata={"kind": "text"})
        for piece in chunk_text(doc.full_text())
    ]
