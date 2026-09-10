from app.xninetzy.os.knowledge.evaluation import evaluate_retrieval
from app.xninetzy.os.knowledge.retrieval import Evidence, EvidenceBundle


def test_retrieval_evaluation_checks_sources_terms_and_citations():
    def fake_retriever(query: str, limit: int) -> EvidenceBundle:
        return EvidenceBundle(
            query=query,
            status="sufficient",
            confidence="high",
            evidence=(
                Evidence(
                    citation="K1",
                    source_id=7,
                    chunk_id=1,
                    title="Source",
                    source_type="note",
                    uri="vault://source",
                    text="supervised learning uses labelled data",
                    score=1.0,
                ),
            ),
            note="ok",
        )

    result = evaluate_retrieval(
        [
            {
                "query": "supervised learning",
                "expected_source_ids": [7],
                "expected_terms": ["labelled data"],
            }
        ],
        retriever=fake_retriever,
    )

    assert result["total"] == 1
    assert result["passed"] == 1
    assert result["recall_at_k"] == 1.0
