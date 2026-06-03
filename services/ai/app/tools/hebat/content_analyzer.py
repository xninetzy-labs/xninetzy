"""Analyze a downloaded HEBAT file into text + lightweight summary metadata.

Reuses the shared ``app.media.document_parser`` (PDF/DOCX/PPTX/XLSX/TXT/MD/CSV)
so there is one parsing implementation across HEBAT and WhatsApp media. Adds
HTML handling and a cheap extractive preview; heavy summarization is left to the
LLM layer. Works on real files — unit-tested with temp files.
"""

from __future__ import annotations

from pathlib import Path

from app.media.document_parser import parse_document
from app.tools.hebat.html_cleaner import html_to_readable_text

# Above this many characters, callers should chunk + push to knowledge/RAG
# rather than inlining the whole thing into a prompt.
LARGE_TEXT_THRESHOLD = 8_000
_HTML_EXTS = {".html", ".htm"}


def analyze_downloaded_file(path: str | Path, mime_type: str | None = None) -> dict:
    """Return ``{text, summary, word_count, char_count, kind, supported, is_large, error}``."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return _empty(error="file not found")

    if p.suffix.lower() in _HTML_EXTS or (mime_type or "").startswith("text/html"):
        text = html_to_readable_text(p.read_text(encoding="utf-8", errors="replace"))
        kind, error = "html", None
    else:
        parsed = parse_document(str(p), mime_type=mime_type, filename=p.name)
        text = parsed.get("text", "") or ""
        kind = parsed.get("kind")
        error = parsed.get("error")

    text = text.strip()
    words = text.split()
    return {
        "text": text,
        "summary": _preview(text),
        "word_count": len(words),
        "char_count": len(text),
        "kind": kind,
        "supported": bool(text) and error is None,
        "is_large": len(text) > LARGE_TEXT_THRESHOLD,
        "error": error,
    }


def _preview(text: str, max_chars: int = 1_500) -> str:
    if not text:
        return ""
    return text[:max_chars].rstrip() + (" …" if len(text) > max_chars else "")


def _empty(*, error: str | None = None) -> dict:
    return {
        "text": "", "summary": "", "word_count": 0, "char_count": 0,
        "kind": None, "supported": False, "is_large": False, "error": error,
    }
