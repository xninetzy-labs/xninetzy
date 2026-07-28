from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.xninetzy.os.knowledge.retrieval import (
    finalize_grounded_answer,
    select_evidence,
    should_auto_ground,
)


def test_select_evidence_deduplicates_and_assigns_stable_citations():
    candidates = [
        {"id": 10, "source_id": 1, "title": "A", "text": "same evidence", "score": 0.9},
        {
            "id": 11,
            "source_id": 1,
            "title": "A",
            "text": " same   evidence ",
            "score": 0.8,
        },
        {
            "id": 12,
            "source_id": 2,
            "title": "B",
            "text": "other evidence",
            "score": 0.7,
        },
    ]

    bundle = select_evidence("query", candidates, limit=5, min_evidence=1)

    assert bundle.status == "sufficient"
    assert [item.citation for item in bundle.evidence] == ["K1", "K2"]
    assert bundle.confidence == "high"


def test_finalize_grounded_answer_removes_unknown_citations():
    bundle = select_evidence(
        "query",
        [{"id": 10, "source_id": 1, "title": "Source", "text": "evidence"}],
        limit=5,
        min_evidence=1,
    )

    result = finalize_grounded_answer("Supported [K1], invalid [K99].", bundle)

    assert "[K1]" in result
    assert "[K99]" not in result
    assert "Source" in result


def test_auto_grounding_is_limited_to_knowledge_seeking_requests():
    assert should_auto_ground("it_learning", "explain", "jelaskan RAG") is True
    assert should_auto_ground("general", "chat", "halo") is False
    assert should_auto_ground("life", "reminder", "ingatkan besok") is False


@pytest.mark.asyncio
async def test_answer_from_knowledge_synthesizes_and_validates_citations(monkeypatch):
    from app.xninetzy.os.knowledge import retrieval

    bundle = select_evidence(
        "query",
        [{"id": 10, "source_id": 1, "title": "Source", "text": "evidence"}],
        limit=5,
        min_evidence=1,
    )

    class FakeLLM:
        async def ainvoke(self, messages):
            assert "[XNINETZY KNOWLEDGE EVIDENCE]" in messages[-1].content
            return SimpleNamespace(content="Grounded claim [K1], fake [K9].")

    monkeypatch.setattr(retrieval, "retrieve_evidence", lambda query: bundle)
    monkeypatch.setattr(
        "app.xninetzy.core.llm.get_llm_pro", lambda profile=None: FakeLLM()
    )

    result = await retrieval.answer_from_knowledge("query")

    assert "Grounded claim [K1]" in result
    assert "[K9]" not in result
    assert "Source" in result
