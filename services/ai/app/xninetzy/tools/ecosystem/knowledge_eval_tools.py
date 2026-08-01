from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.knowledge.evaluation import evaluate_retrieval


@tool
def knowledge_evaluate_retrieval(cases: list[dict], limit: int = 5) -> dict:
    """Evaluasi recall, groundedness dasar, dan validitas citation knowledge."""
    return evaluate_retrieval(cases, limit=limit)
