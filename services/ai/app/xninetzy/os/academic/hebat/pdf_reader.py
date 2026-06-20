from __future__ import annotations

import re
from pathlib import Path

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


def read_pdf_text(file_path: str | Path) -> dict:
    """Extract text from PDF. Returns {text, pages, error}."""
    path = Path(file_path)
    if not path.exists():
        return {"text": "", "pages": 0, "error": "File tidak ditemukan"}

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        texts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
        full_text = "\n\n".join(texts)
        return {"text": full_text, "pages": pages, "error": None}
    except Exception as e:
        logger.warning("pypdf read failed for %s: %s", path, e)
        return {"text": "", "pages": 0, "error": str(e)}


def summarize_pdf(file_path: str | Path, max_chars: int = 3000) -> dict:
    """Read PDF and return a trimmed preview + basic stats for LLM summarization."""
    result = read_pdf_text(file_path)
    if result["error"]:
        return result

    text = result["text"]
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cleaned = "\n".join(lines)

    # Try to extract headings as outline
    headings = [l for l in lines if re.match(r"^[A-Z\d][\w\s\-:]{3,60}$", l) and len(l) < 80]

    preview = cleaned[:max_chars]
    if len(cleaned) > max_chars:
        preview += "\n\n[...konten terpotong...]"

    return {
        "text_preview": preview,
        "pages": result["pages"],
        "total_chars": len(cleaned),
        "headings": headings[:20],
        "error": None,
    }
