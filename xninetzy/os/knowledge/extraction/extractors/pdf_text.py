"""Fast-path PDF text extractor (pypdf), for clean, short PDFs."""
from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.extraction.schemas import DocBlock, StructuredDocument

logger = logging.getLogger(__name__)


def extract_pdf_text(path: str, max_pages: int | None = None) -> StructuredDocument:
    """Extract each PDF page as a paragraph block, tagged with its page number."""
    from pypdf import PdfReader

    reader = PdfReader(str(Path(path)))
    page_count = len(reader.pages)
    limit = page_count if max_pages is None else min(page_count, max_pages)

    blocks: list[DocBlock] = []
    for index in range(limit):
        try:
            text = (reader.pages[index].extract_text() or "").strip()
        except Exception as exc:  # pragma: no cover - defensive per-page
            logger.warning("pdf_text page %d failed: %s", index + 1, exc)
            continue
        for para in (chunk.strip() for chunk in text.split("\n\n")):
            if para:
                blocks.append(DocBlock(kind="paragraph", text=para, page=index + 1))

    return StructuredDocument(
        blocks=tuple(blocks),
        page_count=page_count,
        kind="pdf",
    )
