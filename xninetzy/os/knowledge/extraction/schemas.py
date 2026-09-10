"""Structured document models for the extraction ecosystem.

Frozen dataclasses (following the style of ``retrieval.Evidence``) that carry
document structure from the extractors through chunking and into storage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

BlockKind = Literal["heading", "paragraph", "list", "table", "image_caption"]
Strategy = Literal["simple", "complex"]
ChunkerKind = Literal["flat", "structure_aware"]


@dataclass(frozen=True)
class DocBlock:
    """A single structural unit extracted from a document."""

    kind: BlockKind
    text: str
    page: int = 0
    heading_path: tuple[str, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredDocument:
    """Ordered structural blocks plus aggregate structure statistics."""

    blocks: tuple[DocBlock, ...]
    page_count: int = 0
    table_count: int = 0
    image_count: int = 0
    kind: str = "document"

    def text_blocks(self) -> list[DocBlock]:
        return [b for b in self.blocks if b.kind in ("paragraph", "list", "heading")]

    def tables(self) -> list[DocBlock]:
        return [b for b in self.blocks if b.kind == "table"]

    def full_text(self) -> str:
        return "\n\n".join(b.text for b in self.blocks if b.text.strip())


@dataclass(frozen=True)
class ContextualChunk:
    """A retrieval chunk with contextual prefix + real structural metadata."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentOverview:
    """Map-reduce overview of a document."""

    summary: str = ""
    key_points: tuple[str, ...] = ()
    per_batch: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "key_points": list(self.key_points),
            "per_batch": list(self.per_batch),
        }


@dataclass(frozen=True)
class ExtractionPlan:
    """Router decision: which extraction strategy + tools to use."""

    strategy: Strategy
    extractor: str
    chunker: ChunkerKind
    use_ocr: bool = False
    extract_tables: bool = False
    extract_images: bool = False
    build_overview: bool = False
    page_count: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "extractor": self.extractor,
            "chunker": self.chunker,
            "use_ocr": self.use_ocr,
            "extract_tables": self.extract_tables,
            "extract_images": self.extract_images,
            "build_overview": self.build_overview,
            "page_count": self.page_count,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DocumentManifest:
    """Persisted catalog entry describing how a document was extracted."""

    strategy: str
    extractor: str
    chunker: str
    page_count: int = 0
    table_count: int = 0
    image_count: int = 0
    chunk_count: int = 0
    overview: DocumentOverview | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "extractor": self.extractor,
            "chunker": self.chunker,
            "page_count": self.page_count,
            "table_count": self.table_count,
            "image_count": self.image_count,
            "chunk_count": self.chunk_count,
            "overview": self.overview.to_dict() if self.overview else None,
        }
