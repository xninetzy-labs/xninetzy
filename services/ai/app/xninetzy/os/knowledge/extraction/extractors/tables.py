"""Table helpers — render row grids to markdown and pull tables from PDFs.

pdfplumber is imported lazily; when absent, ``extract_pdf_tables`` yields
nothing and the caller degrades to plain text.
"""
from __future__ import annotations

from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.extraction.schemas import DocBlock

logger = logging.getLogger(__name__)


def rows_to_markdown(rows: list[list[str | None]]) -> str:
    """Render a grid of cells as a GitHub-flavored markdown table."""
    clean = [
        [(("" if cell is None else str(cell)).replace("\n", " ").strip()) for cell in row]
        for row in rows
        if any(cell not in (None, "") for cell in row)
    ]
    if not clean:
        return ""
    width = max(len(r) for r in clean)
    for r in clean:
        r.extend([""] * (width - len(r)))

    header = clean[0]
    body = clean[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def extract_pdf_tables(path: str, max_pages: int | None = None) -> list[DocBlock]:
    """Return one ``table`` DocBlock per detected table (markdown text)."""
    try:
        import pdfplumber
    except ImportError:
        return []

    blocks: list[DocBlock] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for page_index, page in enumerate(pages, 1):
                try:
                    tables = page.extract_tables() or []
                except Exception as exc:  # pragma: no cover - defensive per-page
                    logger.warning("table extract page %d failed: %s", page_index, exc)
                    continue
                for t_index, rows in enumerate(tables, 1):
                    md = rows_to_markdown(rows)
                    if md:
                        blocks.append(
                            DocBlock(
                                kind="table",
                                text=md,
                                page=page_index,
                                meta={"table_index": t_index, "rows": len(rows)},
                            )
                        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("pdfplumber table pass failed: %s", exc)
    return blocks
