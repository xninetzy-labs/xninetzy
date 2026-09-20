from __future__ import annotations

import json
from dataclasses import dataclass

from xninetzy.db.sqlite import connect


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    run_id: str
    question_id: str
    expected_answer: str
    actual_answer: str
    score: float
    keywords: tuple[str, ...]
    captured_at: str

    def passed(self, threshold: float) -> bool:
        return self.score >= threshold


def build_evidence_bundle(
    *,
    run_id: str,
    question_id: str,
    expected_answer: str,
    actual_answer: str,
    score: float,
    keywords: tuple[str, ...],
    captured_at: str,
) -> EvidenceBundle:
    if not run_id:
        raise ValueError("run_id is required")
    if not question_id:
        raise ValueError("question_id is required")
    return EvidenceBundle(
        run_id=run_id,
        question_id=question_id,
        expected_answer=expected_answer,
        actual_answer=actual_answer,
        score=score,
        keywords=keywords,
        captured_at=captured_at,
    )


def evidence_to_row(bundle: EvidenceBundle) -> tuple[str, str, str, str, float, str, str]:
    payload = json.dumps(
        {
            "keywords": list(bundle.keywords),
            "expected_answer": bundle.expected_answer,
            "actual_answer": bundle.actual_answer,
            "score": bundle.score,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return (
        bundle.run_id,
        bundle.question_id,
        bundle.expected_answer,
        bundle.actual_answer,
        bundle.score,
        bundle.captured_at,
        payload,
    )


def load_evidence_for_run(run_id: str) -> tuple[EvidenceBundle, ...]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT run_id, question_id, expected_answer, actual_answer, "
            "score, captured_at, payload_json FROM evidence_artifacts WHERE run_id = ?",
            (run_id,),
        ).fetchall()
    bundles: list[EvidenceBundle] = []
    for row in rows:
        payload = json.loads(row["payload_json"] or "{}")
        keywords = tuple(payload.get("keywords") or ())
        bundles.append(
            EvidenceBundle(
                run_id=row["run_id"],
                question_id=row["question_id"],
                expected_answer=row["expected_answer"],
                actual_answer=row["actual_answer"],
                score=float(row["score"]),
                keywords=keywords,
                captured_at=row["captured_at"],
            )
        )
    return tuple(bundles)