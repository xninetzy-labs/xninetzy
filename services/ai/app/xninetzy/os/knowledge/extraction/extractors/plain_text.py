"""Plain-text / markdown / csv / json extractor — the simple fast path."""
from __future__ import annotations

from pathlib import Path

from app.xninetzy.interfaces.media.document_parser import _parse_text
from app.xninetzy.os.knowledge.extraction.schemas import DocBlock, StructuredDocument


def extract_plain_text(path: str) -> StructuredDocument:
    """Read a flat text file into paragraph blocks split on blank lines."""
    p = Path(path)
    text = _parse_text(p).strip()
    blocks: list[DocBlock] = []
    for para in (chunk.strip() for chunk in text.split("\n\n")):
        if para:
            blocks.append(DocBlock(kind="paragraph", text=para))
    if not blocks and text:
        blocks.append(DocBlock(kind="paragraph", text=text))
    return StructuredDocument(
        blocks=tuple(blocks),
        page_count=1,
        kind=p.suffix.lstrip(".") or "text",
    )
