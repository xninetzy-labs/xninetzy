"""Document overview — map-reduce summarization over structured blocks.

Cheap open-source-friendly summarization: batch prose blocks, summarize each
batch with the flash LLM, then reduce the batch summaries into a single
overview + key points. Gated by ``DOC_OVERVIEW_ENABLED``; degrades to an empty
overview on any failure so ingestion never breaks because of it.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.llm import get_llm_flash
from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.extraction.schemas import (
    DocumentOverview,
    StructuredDocument,
)

logger = logging.getLogger(__name__)

_MAP_SYSTEM = (
    "Kamu meringkas sebagian dokumen. Ringkas isi berikut dalam 2-4 kalimat "
    "padat berbahasa Indonesia. Fokus pada fakta, angka, dan istilah penting. "
    "Jangan menambah informasi di luar teks."
)
_REDUCE_SYSTEM = (
    "Kamu menggabungkan ringkasan-ringkasan bagian dokumen menjadi satu "
    "gambaran utuh. Keluarkan: (1) satu paragraf ringkasan menyeluruh, lalu "
    "baris kosong, lalu (2) 3-6 poin kunci diawali '- '. Bahasa Indonesia."
)


def _batches(doc: StructuredDocument, batch_size: int) -> list[str]:
    texts = [b.text for b in doc.text_blocks() if b.text.strip()]
    texts += [b.text for b in doc.tables()]
    batches: list[str] = []
    for i in range(0, len(texts), batch_size):
        batches.append("\n\n".join(texts[i : i + batch_size]))
    return batches


def _reduce(batch_summaries: list[str]) -> tuple[str, tuple[str, ...]]:
    llm = get_llm_flash()
    joined = "\n\n".join(f"Bagian {i + 1}: {s}" for i, s in enumerate(batch_summaries))
    result = llm.invoke(
        [SystemMessage(content=_REDUCE_SYSTEM), HumanMessage(content=joined)]
    )
    content = result.content if isinstance(result.content, str) else str(result.content)
    summary_part, _, points_part = content.partition("\n\n")
    key_points = tuple(
        line.lstrip("-*• ").strip()
        for line in points_part.splitlines()
        if line.strip().startswith(("-", "*", "•"))
    )
    return summary_part.strip(), key_points


def build_overview(doc: StructuredDocument) -> DocumentOverview:
    s = get_settings()
    if not getattr(s, "DOC_OVERVIEW_ENABLED", True):
        return DocumentOverview()

    batch_size = getattr(s, "DOC_OVERVIEW_BATCH_SIZE", 6)
    max_batches = getattr(s, "DOC_OVERVIEW_MAX_BATCHES", 8)
    batches = _batches(doc, batch_size)[:max_batches]
    if not batches:
        return DocumentOverview()

    try:
        llm = get_llm_flash()
        per_batch: list[str] = []
        for chunk in batches:
            result = llm.invoke(
                [SystemMessage(content=_MAP_SYSTEM), HumanMessage(content=chunk)]
            )
            text = result.content if isinstance(result.content, str) else str(result.content)
            per_batch.append(text.strip())

        if len(per_batch) == 1:
            summary, key_points = per_batch[0], ()
        else:
            summary, key_points = _reduce(per_batch)

        return DocumentOverview(
            summary=summary,
            key_points=key_points,
            per_batch=tuple(per_batch),
        )
    except Exception as exc:
        logger.warning("Overview generation failed: %s", exc)
        return DocumentOverview()
