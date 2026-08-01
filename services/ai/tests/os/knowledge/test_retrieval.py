from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.xninetzy.os.knowledge.retrieval import (
    _apply_reference_penalty,
    _is_reference_chunk,
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


# ─── relevance gating (phase 8 retrieval-quality fixes) ──────────────────────


def test_off_domain_low_cosine_query_is_insufficient():
    """A query the vault does not cover retrieves chunks by lexical overlap only;
    with a live semantic leg reporting low cosine, the bundle must be insufficient
    — not sufficient/high (the 'resep nasi goreng' false positive)."""
    candidates = [
        {"id": 1, "source_id": 5, "title": "Topologi Jaringan", "text": "router switch",
         "score": 0.02, "semantic_score": 0.11},
        {"id": 2, "source_id": 6, "title": "Jaringan HEBAT", "text": "subnet mask",
         "score": 0.01, "semantic_score": 0.09},
    ]

    bundle = select_evidence("resep nasi goreng enak", candidates, limit=5, min_evidence=1)

    assert bundle.status == "insufficient"
    assert bundle.confidence == "low"


def test_lexical_only_hits_are_dropped_when_semantic_leg_is_live():
    """Cross-document FTS pollution: a chunk matched only on a common word carries
    no cosine (semantic_score=None) and must be dropped once real semantic backing
    exists elsewhere."""
    candidates = [
        {"id": 1, "source_id": 1, "title": "Tidur & Memori", "text": "sleep consolidates memory",
         "score": 0.03, "semantic_score": 0.62},
        {"id": 2, "source_id": 9, "title": "Jaringan Komputer", "text": "mahasiswa memori RAM",
         "score": 0.02, "semantic_score": None},
    ]

    bundle = select_evidence("tidur mempengaruhi memori mahasiswa", candidates, limit=5, min_evidence=1)

    source_ids = {e.source_id for e in bundle.evidence}
    assert 9 not in source_ids  # polluting lexical-only chunk removed
    assert bundle.status == "sufficient"


def test_reference_chunk_detection():
    ref = "Walker, M. (2017). Why We Sleep. doi.org/10.1000/xyz. pp. 33-40. et al."
    body = "Social jetlag adalah selisih antara jam biologis dan jadwal sosial."
    assert _is_reference_chunk(ref) is True
    assert _is_reference_chunk(body) is False


def test_reference_penalty_demotes_bibliography_below_content():
    """Chunk 29 (references) must not outrank chunk 26 (content) after penalty."""
    candidates = [
        {"id": 29, "source_id": 1, "text": "Roenneberg (2012). Wittmann (2006). doi.org/10.1 pp. 12",
         "score": 0.05, "semantic_score": 0.40},
        {"id": 26, "source_id": 1, "text": "Social jetlag menurunkan performa belajar mahasiswa.",
         "score": 0.03, "semantic_score": 0.55},
    ]

    ordered = _apply_reference_penalty(candidates, penalty=0.5)

    assert ordered[0]["id"] == 26  # content now leads
    assert ordered[1]["id"] == 29 and ordered[1]["is_reference"] is True


def test_multi_topic_bundle_is_not_high_confidence():
    """confidence=high must require topic consistency, not just presence."""
    candidates = [
        {"id": 1, "source_id": 1, "title": "A", "text": "chunk a", "score": 0.03, "semantic_score": 0.34},
        {"id": 2, "source_id": 2, "title": "B", "text": "chunk b", "score": 0.02, "semantic_score": 0.31},
        {"id": 3, "source_id": 3, "title": "C", "text": "chunk c", "score": 0.02, "semantic_score": 0.30},
    ]

    bundle = select_evidence("q", candidates, limit=5, min_evidence=1)

    assert bundle.confidence != "high"  # three unrelated sources, no strong hit


def test_strong_consistent_evidence_is_high_confidence():
    candidates = [
        {"id": 1, "source_id": 1, "title": "A", "text": "on topic one", "score": 0.05, "semantic_score": 0.71},
        {"id": 2, "source_id": 1, "title": "A", "text": "on topic two", "score": 0.04, "semantic_score": 0.63},
    ]

    bundle = select_evidence("q", candidates, limit=5, min_evidence=1)

    assert bundle.status == "sufficient"
    assert bundle.confidence == "high"
