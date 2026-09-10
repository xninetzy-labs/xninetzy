"""Concrete extractors named by the router.

Each ``extract_*`` returns a :class:`StructuredDocument` of ordered
``DocBlock``s. All rely on pure-python open-source parsers already vendored by
xninetzy (pypdf, pdfplumber, python-docx, openpyxl, python-pptx) plus
tesseract OCR — no Docling, no vision model.
"""
from __future__ import annotations

from app.xninetzy.os.knowledge.extraction.extractors.office import extract_office
from app.xninetzy.os.knowledge.extraction.extractors.pdf_structured import (
    extract_pdf_structured,
)
from app.xninetzy.os.knowledge.extraction.extractors.pdf_text import extract_pdf_text
from app.xninetzy.os.knowledge.extraction.extractors.plain_text import extract_plain_text

__all__ = [
    "extract_office",
    "extract_pdf_structured",
    "extract_pdf_text",
    "extract_plain_text",
]
