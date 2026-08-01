"""Image/OCR helper — render scanned PDF pages and OCR them via tesseract.

Deterministic, open-source (pypdfium2 + pytesseract). No vision model. Gated
by both ``OCR_ENABLED`` and ``DOC_IMAGE_OCR_ENABLED``.
"""
from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.extraction.schemas import DocBlock

logger = logging.getLogger(__name__)


def ocr_pdf_pages(path: str, max_pages: int | None = None) -> list[DocBlock]:
    """OCR each rendered page into an ``image_caption`` block, page-tagged."""
    s = get_settings()
    if not (s.OCR_ENABLED and s.DOC_IMAGE_OCR_ENABLED):
        return []
    try:
        import pypdfium2 as pdfium
    except ImportError:
        logger.warning("pypdfium2 missing — skipping OCR pass")
        return []

    from app.xninetzy.interfaces.media.image_parser import ocr_pil_image

    cap = max_pages if max_pages is not None else s.OCR_MAX_PDF_PAGES
    blocks: list[DocBlock] = []
    document = pdfium.PdfDocument(str(path))
    try:
        page_count = min(len(document), cap)
        for index in range(page_count):
            page = document[index]
            try:
                bitmap = page.render(scale=2)
                try:
                    image = bitmap.to_pil()
                    try:
                        text = (ocr_pil_image(image) or "").strip()
                    finally:
                        image.close()
                finally:
                    bitmap.close()
            finally:
                page.close()
            if text:
                blocks.append(
                    DocBlock(kind="image_caption", text=text, page=index + 1,
                             meta={"ocr": True})
                )
    finally:
        document.close()
    return blocks
