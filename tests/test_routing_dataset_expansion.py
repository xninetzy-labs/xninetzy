from __future__ import annotations

from xninetzy.context.routing.dataset_expansion import (
    CONFUSION_PAIR_TEMPLATES,
    expanded_adversarial_set,
    write_expanded_adversarial,
)


def test_confusion_pair_templates_have_queries() -> None:
    assert len(CONFUSION_PAIR_TEMPLATES) >= 9
    for t in CONFUSION_PAIR_TEMPLATES:
        assert t["queries"]
        assert t["label"]


def test_expanded_adversarial_set_at_least_200() -> None:
    rows = expanded_adversarial_set()
    assert len(rows) >= 200
    labels: set[str] = set()
    for r in rows:
        src = r.get("source", {})
        labels.add(src.get("label", ""))
    assert len({label for label in labels if label}) >= 9


def test_write_expanded_adversarial_overwrites(tmp_path) -> None:
    p = tmp_path / "adversarial.jsonl"
    n = write_expanded_adversarial(p)
    assert n >= 200
    import pathlib

    assert pathlib.Path(p).exists()
    assert p.stat().st_size > 0


def test_no_duplicate_queries_in_expanded() -> None:
    rows = expanded_adversarial_set()
    texts = [r["input"]["text"] for r in rows]
    assert len(texts) == len(set(texts))


def test_difficulty_label_for_negation_pair() -> None:
    rows = expanded_adversarial_set()
    negation = [r for r in rows if r["source"].get("label") == "negation"]
    assert negation
    assert all(r["difficulty"] == "hard" for r in negation)
