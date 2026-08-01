"""Structure-aware PDF extractor for complex PDFs.

Uses pdfplumber for per-page text with a lightweight heading heuristic, folds
in extracted tables (via ``tables``) and, for scanned pages, tesseract OCR (via
``images``). Ordered by page so downstream chunking keeps a readable flow.
"""
from __future__ import annotations

import re

from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.extraction.extractors.images import ocr_pdf_pages
from app.xninetzy.os.knowledge.extraction.extractors.pdf_text import extract_pdf_text
from app.xninetzy.os.knowledge.extraction.extractors.tables import extract_pdf_tables
from app.xninetzy.os.knowledge.extraction.schemas import DocBlock, StructuredDocument

logger = logging.getLogger(__name__)

# A short, title-cased-or-numbered line with no terminal punctuation reads as a heading.
_HEADING_RE = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+)?[A-Z0-9].{0,79}$")


def _looks_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line.split()) > 12 or line.endswith((".", ",", ";", ":")):
        return False
    if not _HEADING_RE.match(line):
        return False
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(c.isupper() for c in letters) / len(letters)
    return upper_ratio > 0.6 or line[:1].isdigit()


def _text_blocks(path: str, max_pages: int | None) -> list[DocBlock]:
    try:
        import pdfplumber
    except ImportError:
        # Fall back to the pypdf fast path if pdfplumber is unavailable.
        return list(extract_pdf_text(path, max_pages=max_pages).blocks)

    blocks: list[DocBlock] = []
    heading_stack: list[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for page_index, page in enumerate(pages, 1):
                try:
                    text = page.extract_text() or ""
                except Exception as exc:  # pragma: no cover - defensive per-page
                    logger.warning("structured text page %d failed: %s", page_index, exc)
                    continue
                buffer: list[str] = []

                def flush() -> None:
                    if buffer:
                        blocks.append(
                            DocBlock(
                                kind="paragraph",
                                text="\n".join(buffer).strip(),
                                page=page_index,
                                heading_path=tuple(heading_stack),
                            )
                        )
                        buffer.clear()

                for raw in text.splitlines():
                    line = raw.strip()
                    if not line:
                        flush()
                        continue
                    if _looks_heading(line):
                        flush()
                        heading_stack[:] = [line]
                        blocks.append(
                            DocBlock(
                                kind="heading",
                                text=line,
                                page=page_index,
                                heading_path=(line,),
                            )
                        )
                    else:
                        buffer.append(line)
                flush()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("pdfplumber structured pass failed: %s — using pypdf", exc)
        return list(extract_pdf_text(path, max_pages=max_pages).blocks)
    return blocks


def extract_pdf_structured(
    path: str,
    *,
    use_ocr: bool = False,
    extract_tables: bool = True,
    max_pages: int | None = None,
) -> StructuredDocument:
    """Extract a complex PDF into ordered structural blocks."""
    text_blocks = _text_blocks(path, max_pages)
    table_blocks = extract_pdf_tables(path, max_pages) if extract_tables else []
    ocr_blocks = ocr_pdf_pages(path, max_pages) if use_ocr else []

    # Interleave by page so tables/OCR land near their surrounding text.
    merged = sorted(
        [*text_blocks, *table_blocks, *ocr_blocks],
        key=lambda b: (b.page, {"heading": 0, "paragraph": 1, "list": 1,
                                "table": 2, "image_caption": 3}.get(b.kind, 1)),
    )

    page_count = 0
    try:
        from pypdf import PdfReader

        page_count = len(PdfReader(str(path)).pages)
    except Exception:  # pragma: no cover - defensive
        page_count = max((b.page for b in merged), default=0)

    return StructuredDocument(
        blocks=tuple(merged),
        page_count=page_count,
        table_count=len(table_blocks),
        image_count=len(ocr_blocks),
        kind="pdf",
    )
