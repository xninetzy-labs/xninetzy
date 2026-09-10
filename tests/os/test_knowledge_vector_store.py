from app.xninetzy.os.knowledge.vector_store import (
    _deduplicate_results,
    _rrf_fuse_results,
)


def test_deduplicate_identical_search_results():
    rows = [
        {"source_id": 1, "text": "same text", "score": 0.9},
        {"source_id": 1, "text": " same   text ", "score": 0.8},
        {"source_id": 2, "text": "same text", "score": 0.7},
    ]

    results = _deduplicate_results(rows, limit=5)

    assert len(results) == 2
    assert [result["source_id"] for result in results] == [1, 2]


def test_rrf_fusion_rewards_results_seen_by_both_retrievers():
    semantic = [
        {"id": 1, "source_id": 1, "text": "semantic only"},
        {"id": 2, "source_id": 2, "text": "shared"},
    ]
    keyword = [
        {"id": 2, "source_id": 2, "text": "shared"},
        {"id": 3, "source_id": 3, "text": "keyword only"},
    ]

    results = _rrf_fuse_results(semantic, keyword, limit=3)

    assert results[0]["id"] == 2
    assert results[0]["retrieval_channels"] == ["keyword", "semantic"]
