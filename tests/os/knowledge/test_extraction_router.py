"""Offline tests for the router-based extraction ecosystem (no LLM, no network)."""
from __future__ import annotations

from app.xninetzy.os.knowledge.extraction.router import analyze_document
from app.xninetzy.os.knowledge.extraction.schemas import (
    DocBlock,
    StructuredDocument,
)
from app.xninetzy.os.knowledge.extraction.structure_chunker import chunk_structured
from app.xninetzy.os.knowledge.extraction.extractors.tables import rows_to_markdown


def test_router_plain_text_is_simple(tmp_path):
    p = tmp_path / "note.md"
    p.write_text("# Judul\n\nisi catatan singkat.", encoding="utf-8")

    plan = analyze_document(str(p), filename=p.name)

    assert plan.strategy == "simple"
    assert plan.extractor == "plain_text"
    assert plan.chunker == "flat"


def test_router_office_is_complex_structure_aware(tmp_path):
    p = tmp_path / "deck.pptx"
    p.write_bytes(b"PK\x03\x04dummy")  # ext resolves from suffix; no parsing at probe

    plan = analyze_document(str(p), filename=p.name)

    assert plan.strategy == "complex"
    assert plan.extractor == "office"
    assert plan.chunker == "structure_aware"


def test_router_unsupported_extension_degrades(tmp_path):
    p = tmp_path / "mystery.xyz"
    p.write_text("data", encoding="utf-8")

    plan = analyze_document(str(p), filename=p.name)

    # Unknown suffix + no mime resolves to a safe flat fallback, never crashes.
    assert plan.chunker == "flat"


def test_structure_chunker_keeps_page_and_heading_metadata():
    doc = StructuredDocument(
        blocks=(
            DocBlock(kind="heading", text="Bab 1", page=1, heading_path=("Bab 1",)),
            DocBlock(kind="paragraph", text="Isi paragraf bab satu yang cukup panjang "
                     "untuk lolos ambang minimal panjang chunk pada chunker.",
                     page=1, heading_path=("Bab 1",)),
            DocBlock(kind="table", text="| a | b |\n| --- | --- |\n| 1 | 2 |",
                     page=2, heading_path=("Bab 1",), meta={"rows": 2}),
        ),
        page_count=2,
        table_count=1,
    )

    chunks = chunk_structured(doc)

    assert chunks, "expected at least one chunk"
    # Every chunk carries page + heading breadcrumb metadata.
    for c in chunks:
        assert "page" in c.metadata
        assert "heading_path" in c.metadata
    # Table becomes its own chunk with kind=table and its meta preserved.
    table_chunks = [c for c in chunks if c.metadata.get("kind") == "table"]
    assert len(table_chunks) == 1
    assert table_chunks[0].metadata["page"] == 2
    assert table_chunks[0].metadata["rows"] == 2
    # Prose chunk text is prefixed with a self-locating breadcrumb.
    prose = [c for c in chunks if c.metadata.get("kind") == "text"]
    assert prose and prose[0].text.startswith("[hal. 1]")
    assert "Bab 1" in prose[0].text


def test_rows_to_markdown_pads_and_cleans():
    md = rows_to_markdown([["Nama", "Nilai"], ["Budi\n", None], ["Ani", "90", "extra"]])

    lines = md.splitlines()
    assert lines[0] == "| Nama | Nilai |  |"
    assert lines[1] == "| --- | --- | --- |"
    # None becomes empty, newline stripped, short rows padded to max width.
    assert lines[2] == "| Budi |  |  |"
    assert lines[3] == "| Ani | 90 | extra |"


def test_rows_to_markdown_empty_returns_blank():
    assert rows_to_markdown([]) == ""
    assert rows_to_markdown([[None, ""], ["", None]]) == ""
