"""Extraction router — the heart of the ecosystem.

Cheaply probes a document (type, size, page count, text-ratio, table presence)
and decides a ``simple`` vs ``complex`` strategy, then names which open-source
extractor + chunker + optional steps to run. No heavy libraries are imported at
probe time; pdfplumber is only touched for the table sniff and degrades to a
no-table decision when absent.
"""
from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.interfaces.media.document_parser import _resolve_ext
from app.xninetzy.os.knowledge.extraction.schemas import ExtractionPlan

logger = logging.getLogger(__name__)

_PLAIN_EXTS = {".txt", ".md", ".markdown", ".csv", ".json"}
_OFFICE_EXTS = {".docx", ".pptx", ".xlsx"}


def _pdf_probe(path: Path, sample_pages: int) -> tuple[int, float, bool]:
    """Return (page_count, text_ratio chars/page, looks_scanned)."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        if page_count == 0:
            return 0, 0.0, False
        probe = reader.pages[: max(1, min(sample_pages, page_count))]
        chars = 0
        for page in probe:
            try:
                chars += len((page.extract_text() or "").strip())
            except Exception:  # pragma: no cover - defensive per-page
                continue
        text_ratio = chars / len(probe) if probe else 0.0
        return page_count, text_ratio, text_ratio < 1.0
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("PDF probe failed for %s: %s", path.name, exc)
        return 0, 0.0, False


def _pdf_has_tables(path: Path, sample_pages: int) -> bool:
    try:
        import pdfplumber
    except ImportError:
        return False
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages[: max(1, sample_pages)]:
                try:
                    if page.find_tables():
                        return True
                except Exception:  # pragma: no cover - defensive per-page
                    continue
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Table sniff failed for %s: %s", path.name, exc)
    return False


def analyze_document(
    path: str,
    mime_type: str | None = None,
    filename: str | None = None,
) -> ExtractionPlan:
    """Classify a document and pick its extraction strategy + tools."""
    s = get_settings()
    p = Path(path)
    ext = _resolve_ext(p, mime_type, filename)

    if not ext:
        return ExtractionPlan(
            strategy="simple",
            extractor="unsupported",
            chunker="flat",
            reason=f"Tipe file tak didukung (mime={mime_type}, name={filename or p.name})",
        )

    # Plain text / markdown / structured-text: always simple, flat chunking.
    if ext in _PLAIN_EXTS:
        return ExtractionPlan(
            strategy="simple",
            extractor="plain_text",
            chunker="flat",
            reason=f"Berkas teks ({ext}) — jalur cepat flat.",
        )

    # Office formats carry inherent structure (headings, tables, slides/sheets).
    if ext in _OFFICE_EXTS:
        return ExtractionPlan(
            strategy="complex",
            extractor="office",
            chunker="structure_aware",
            extract_tables=s.DOC_TABLE_EXTRACTION_ENABLED,
            build_overview=s.DOC_OVERVIEW_ENABLED,
            reason=f"Dokumen Office ({ext}) berstruktur — structure-aware.",
        )

    if ext == ".pdf":
        return _plan_pdf(p, s)

    return ExtractionPlan(
        strategy="simple",
        extractor="plain_text",
        chunker="flat",
        reason=f"Fallback flat untuk {ext}.",
    )


def _plan_pdf(p: Path, s) -> ExtractionPlan:
    page_count, text_ratio, _ = _pdf_probe(p, s.DOC_ROUTER_SAMPLE_PAGES)
    scanned = text_ratio < s.DOC_ROUTER_MIN_TEXT_RATIO
    many_pages = page_count > s.DOC_ROUTER_COMPLEX_PAGE_THRESHOLD
    has_tables = (
        s.DOC_TABLE_EXTRACTION_ENABLED
        and not scanned
        and _pdf_has_tables(p, s.DOC_ROUTER_SAMPLE_PAGES)
    )

    if not (scanned or many_pages or has_tables):
        return ExtractionPlan(
            strategy="simple",
            extractor="pdf_text",
            chunker="flat",
            page_count=page_count,
            reason=(
                f"PDF {page_count} hal, text-ratio {text_ratio:.0f} — bersih & ringkas, jalur cepat."
            ),
        )

    reasons = []
    if scanned:
        reasons.append(f"scanned (text-ratio {text_ratio:.0f} < {s.DOC_ROUTER_MIN_TEXT_RATIO})")
    if many_pages:
        reasons.append(f"{page_count} hal > {s.DOC_ROUTER_COMPLEX_PAGE_THRESHOLD}")
    if has_tables:
        reasons.append("terdeteksi tabel")

    return ExtractionPlan(
        strategy="complex",
        extractor="pdf_structured",
        chunker="structure_aware",
        use_ocr=scanned and s.DOC_IMAGE_OCR_ENABLED and s.OCR_ENABLED,
        extract_tables=has_tables,
        extract_images=scanned and s.DOC_IMAGE_OCR_ENABLED and s.OCR_ENABLED,
        build_overview=s.DOC_OVERVIEW_ENABLED,
        page_count=page_count,
        reason="PDF kompleks: " + ", ".join(reasons) + ".",
    )
