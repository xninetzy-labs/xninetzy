"""Router-based document extraction ecosystem.

Classifies each document as *simple* or *complex* and selects open-source
extractors accordingly (pypdf, pdfplumber, python-docx/pptx, openpyxl,
pypdfium2 + tesseract OCR). No Docling, no vision LLM. Produces heading/page
aware structured chunks with real per-chunk metadata that flows into the
existing FAISS knowledge store.
"""

from app.xninetzy.os.knowledge.extraction.overview import build_overview
from app.xninetzy.os.knowledge.extraction.pipeline import (
    build_document_chunks,
    extract_document,
)
from app.xninetzy.os.knowledge.extraction.router import analyze_document
from app.xninetzy.os.knowledge.extraction.schemas import (
    ContextualChunk,
    DocBlock,
    DocumentManifest,
    DocumentOverview,
    ExtractionPlan,
    StructuredDocument,
)
from app.xninetzy.os.knowledge.extraction.structure_chunker import chunk_structured

__all__ = [
    "extract_document",
    "build_document_chunks",
    "build_overview",
    "chunk_structured",
    "analyze_document",
    "ContextualChunk",
    "DocBlock",
    "DocumentManifest",
    "DocumentOverview",
    "ExtractionPlan",
    "StructuredDocument",
]
