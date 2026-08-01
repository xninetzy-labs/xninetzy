"""Structure-aware chunker.

Turns a ``StructuredDocument`` into ``ContextualChunk``s that carry a heading
breadcrumb and a ``[hal. N]`` page prefix in the text (so retrieval snippets are
self-locating) plus real structural metadata (page, heading_path, kind) for the
FAISS store. Tables are kept whole as their own chunks; prose is packed with the
existing ``chunk_text`` splitter.
"""
from __future__ import annotations

from app.xninetzy.os.knowledge.chunking import chunk_text
from app.xninetzy.os.knowledge.extraction.schemas import (
    ContextualChunk,
    StructuredDocument,
)


def _breadcrumb(heading_path: tuple[str, ...]) -> str:
    return " > ".join(h for h in heading_path if h.strip())


def _prefix(page: int, breadcrumb: str) -> str:
    parts: list[str] = []
    if page:
        parts.append(f"[hal. {page}]")
    if breadcrumb:
        parts.append(breadcrumb)
    return " ".join(parts)


def _emit(
    text: str,
    *,
    page: int,
    heading_path: tuple[str, ...],
    kind: str,
    extra: dict | None = None,
) -> ContextualChunk:
    breadcrumb = _breadcrumb(heading_path)
    prefix = _prefix(page, breadcrumb)
    body = f"{prefix}\n{text}" if prefix else text
    metadata = {
        "page": page,
        "heading_path": list(heading_path),
        "breadcrumb": breadcrumb,
        "kind": kind,
    }
    if extra:
        metadata.update(extra)
    return ContextualChunk(text=body, metadata=metadata)


def chunk_structured(
    doc: StructuredDocument,
    *,
    max_tokens: int = 300,
    overlap: int = 50,
) -> list[ContextualChunk]:
    """Group prose under its heading context, keep tables/images whole."""
    chunks: list[ContextualChunk] = []

    # Buffer consecutive prose blocks that share the same heading context so a
    # heading and the paragraphs beneath it stay together in a chunk.
    buffer: list[str] = []
    buf_page = 0
    buf_path: tuple[str, ...] = ()

    def flush() -> None:
        nonlocal buffer, buf_page, buf_path
        if not buffer:
            return
        combined = "\n\n".join(buffer)
        for piece in chunk_text(combined, max_tokens=max_tokens, overlap=overlap):
            chunks.append(
                _emit(piece, page=buf_page, heading_path=buf_path, kind="text")
            )
        buffer = []

    for block in doc.blocks:
        if block.kind in ("table", "image_caption"):
            flush()
            chunks.append(
                _emit(
                    block.text,
                    page=block.page,
                    heading_path=block.heading_path,
                    kind=block.kind,
                    extra=dict(block.meta) if block.meta else None,
                )
            )
            continue

        # Prose (heading/paragraph/list). Break the buffer when the heading
        # context changes so breadcrumbs stay accurate.
        if buffer and block.heading_path != buf_path:
            flush()
        if not buffer:
            buf_page = block.page
            buf_path = block.heading_path
        buffer.append(block.text)

    flush()
    return chunks
