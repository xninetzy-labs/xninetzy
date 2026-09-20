from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect

EvolutionStage: str = "evolution"
EvolutionStageProposed: str = "proposed"
EvolutionStageValidated: str = "validated"
EvolutionStageApproved: str = "approved"
EvolutionStageDeployed: str = "deployed"
EvolutionStageRejected: str = "rejected"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


@dataclass(frozen=True, slots=True)
class EvolutionProposal:
    proposal_id: str
    title: str
    problem: str
    proposed_change: str
    expected_impact: str
    risk_level: str
    confidence: float
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    stage: str = EvolutionStageProposed

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "problem": self.problem,
            "proposed_change": self.proposed_change,
            "expected_impact": self.expected_impact,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 4),
            "evidence_refs": list(self.evidence_refs),
            "stage": self.stage,
        }


@dataclass(frozen=True, slots=True)
class EvolutionDecision:
    proposal_id: str
    decision: str
    reason: str
    next_stage: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "decision": self.decision,
            "reason": self.reason,
            "next_stage": self.next_stage,
        }


@dataclass(frozen=True, slots=True)
class EvolutionState:
    proposals: tuple[EvolutionProposal, ...]
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]
    deployed: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposals": [p.to_dict() for p in self.proposals],
            "accepted": list(self.accepted),
            "rejected": list(self.rejected),
            "deployed": list(self.deployed),
            "notes": list(self.notes),
        }


_STAGE_TRANSITIONS: dict[str, str] = {
    EvolutionStageProposed: EvolutionStageValidated,
    EvolutionStageValidated: EvolutionStageApproved,
    EvolutionStageApproved: EvolutionStageDeployed,
    EvolutionStageRejected: EvolutionStageRejected,
}


def _load_proposal(proposal_id: str) -> EvolutionProposal | None:
    _ensure_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM context_evolution_proposals WHERE proposal_id=?",
            (proposal_id,),
        ).fetchone()
    if row is None:
        return None
    raw_evidence = str(row["evidence_refs_json"] or "[]")
    try:
        evidence_data = json.loads(raw_evidence)
    except (TypeError, ValueError):
        evidence_data = []
    return EvolutionProposal(
        proposal_id=str(row["proposal_id"]),
        title=str(row["title"]),
        problem=str(row["problem"]),
        proposed_change=str(row["proposed_change"]),
        expected_impact=str(row["expected_impact"]),
        risk_level=str(row["risk_level"]),
        confidence=float(row["confidence"] or 0.0),
        evidence_refs=tuple(str(item) for item in evidence_data),
        stage=str(row["stage"] or EvolutionStageProposed),
    )


def propose_evolution(
    *,
    proposal_id: str,
    title: str,
    problem: str,
    proposed_change: str,
    expected_impact: str,
    risk_level: str,
    confidence: float,
    evidence_refs: tuple[str, ...] = (),
) -> EvolutionProposal:
    if not proposal_id:
        raise ValueError("proposal_id required")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence must be in [0,1]; got {confidence}")
    proposal = EvolutionProposal(
        proposal_id=proposal_id,
        title=title,
        problem=problem,
        proposed_change=proposed_change,
        expected_impact=expected_impact,
        risk_level=risk_level,
        confidence=confidence,
        evidence_refs=evidence_refs,
        stage=EvolutionStageProposed,
    )
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO context_evolution_proposals
              (proposal_id, title, problem, proposed_change, expected_impact,
               risk_level, confidence, evidence_refs_json, stage,
               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                title,
                problem,
                proposed_change,
                expected_impact,
                risk_level,
                max(0.0, min(1.0, confidence)),
                json.dumps(list(evidence_refs), ensure_ascii=False),
                EvolutionStageProposed,
                _utcnow(),
                _utcnow(),
            ),
        )
    return proposal


def transition_proposal(
    *,
    proposal_id: str,
    decision: str,
    reason: str = "",
) -> EvolutionDecision:
    proposal = _load_proposal(proposal_id)
    if proposal is None:
        raise ValueError(f"unknown proposal {proposal_id!r}")
    if decision == EvolutionStageRejected:
        next_stage = EvolutionStageRejected
    else:
        next_stage = _STAGE_TRANSITIONS.get(proposal.stage, EvolutionStageRejected)
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE context_evolution_proposals SET stage=?, updated_at=? WHERE proposal_id=?
            """,
            (next_stage, _utcnow(), proposal_id),
        )
    return EvolutionDecision(
        proposal_id=proposal_id,
        decision=decision,
        reason=reason,
        next_stage=next_stage,
    )


def get_proposal(proposal_id: str) -> EvolutionProposal | None:
    return _load_proposal(proposal_id)


def evolution_state() -> EvolutionState:
    _ensure_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM context_evolution_proposals ORDER BY proposal_id"
        ).fetchall()
    proposals = tuple(
        EvolutionProposal(
            proposal_id=str(row["proposal_id"]),
            title=str(row["title"]),
            problem=str(row["problem"]),
            proposed_change=str(row["proposed_change"]),
            expected_impact=str(row["expected_impact"]),
            risk_level=str(row["risk_level"]),
            confidence=float(row["confidence"] or 0.0),
            evidence_refs=tuple(
                str(item)
                for item in json.loads(str(row["evidence_refs_json"] or "[]"))
            ),
            stage=str(row["stage"] or EvolutionStageProposed),
        )
        for row in rows
    )
    accepted = tuple(
        p.proposal_id for p in proposals if p.stage == EvolutionStageApproved
    )
    rejected = tuple(
        p.proposal_id for p in proposals if p.stage == EvolutionStageRejected
    )
    deployed = tuple(
        p.proposal_id for p in proposals if p.stage == EvolutionStageDeployed
    )
    return EvolutionState(
        proposals=proposals,
        accepted=accepted,
        rejected=rejected,
        deployed=deployed,
    )


def reset_evolution() -> None:
    _ensure_db()
    with connect() as conn:
        conn.execute("DELETE FROM context_evolution_proposals")
