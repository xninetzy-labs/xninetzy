from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ResearchPerspective:
    perspective_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    rationale: str = ""
    seed_source_ids: list[str] = field(default_factory=list)
    research_question_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class ResearchQuestion:
    question_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    perspective_id: str = ""
    question: str = ""
    question_type: str = "EVIDENCE"
    retrieved_evidence_ids: list[str] = field(default_factory=list)
    answer: str = ""
    follow_up_question_ids: list[str] = field(default_factory=list)
    unresolved_issue_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ResearchTurn:
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    perspective_id: str = ""
    question_id: str = ""
    retrieved_evidence_ids: list[str] = field(default_factory=list)
    answer: str = ""
    citation_ids: list[str] = field(default_factory=list)
    follow_up_question: str = ""
    unresolved: list[str] = field(default_factory=list)


@dataclass
class SourceRecord:
    source_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    url: str = ""
    canonical_url: str = ""
    title: str = ""
    author: str = ""
    publisher: str = ""
    published_at: str = ""
    retrieved_at: float = field(default_factory=time.time)
    source_type: str = "web"
    authority: str = ""
    content_hash: str = ""
    excerpt: str = ""
    methodology: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    evidence_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_id: str = ""
    excerpt: str = ""
    location: str = ""
    claim_ids: list[str] = field(default_factory=list)
    perspective_ids: list[str] = field(default_factory=list)
    question_ids: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.5
    scope: str = ""


@dataclass
class Claim:
    claim_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    statement: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    scope: str = ""
    population: str = ""
    timeframe: str = ""
    status: str = "SUPPORTED"
    confidence: float = 0.5


@dataclass
class Contradiction:
    contradiction_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    claim_a_id: str = ""
    claim_b_id: str = ""
    reason: str = ""
    possible_cause: str = ""
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class ResearchGap:
    gap_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    gap_kind: str = "EVIDENCE_GAP"
    evidence_ids: list[str] = field(default_factory=list)
    status: str = "GAP_CANDIDATE"


@dataclass
class OutlineSection:
    section_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    heading: str = ""
    key_questions: list[str] = field(default_factory=list)
    key_claim_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    unresolved_issue_ids: list[str] = field(default_factory=list)


@dataclass
class ResearchOutline:
    sections: list[OutlineSection] = field(default_factory=list)
    synthesis: str = ""


@dataclass
class ResearchBrief:
    objective: str = ""
    topic: str = ""
    scope: str = ""
    exclusions: list[str] = field(default_factory=list)
    key_questions: list[str] = field(default_factory=list)
    target_audience: str = ""
    evidence_standard: str = "moderate"
    date_range: dict[str, str] = field(default_factory=dict)
    source_types: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=lambda: ["en"])
    depth: str = "STANDARD"


@dataclass
class ResearchRun:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    project_id: str = ""
    owner_id: str = ""
    brief: ResearchBrief = field(default_factory=ResearchBrief)
    topic: str = ""
    mode: str = "STANDARD"
    source_mode: str = "hybrid"
    status: str = "CREATED"
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    model_config_ref: str = ""
    retriever_config_ref: str = ""
    perspective_count: int = 0
    question_count: int = 0
    source_count: int = 0
    evidence_count: int = 0
    claim_count: int = 0
    gap_count: int = 0
    contradiction_count: int = 0
    artifact_refs: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class ResearchPacket:
    schema_version: str = "1.0"
    research_run_id: str = ""
    topic: str = ""
    scope: str = ""
    perspectives: list[ResearchPerspective] = field(default_factory=list)
    questions: list[ResearchQuestion] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    gaps: list[ResearchGap] = field(default_factory=list)
    outline: ResearchOutline = field(default_factory=ResearchOutline)
    provenance: dict[str, Any] = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)


RESEARCH_RUN_STATES = {
    "CREATED",
    "PLANNING",
    "DISCOVERING_PERSPECTIVES",
    "GENERATING_QUESTIONS",
    "RETRIEVING",
    "SIMULATING_CONVERSATION",
    "CONSOLIDATING_EVIDENCE",
    "BUILDING_OUTLINE",
    "SYNTHESIZING",
    "VALIDATING",
    "WAITING_FOR_USER",
    "COMPLETED",
    "PARTIAL",
    "FAILED",
    "CANCELLED",
}


RESEARCH_MODES = {
    "QUICK_RESEARCH",
    "STANDARD",
    "DEEP_RESEARCH",
    "LITERATURE_REVIEW",
    "CORPUS_RESEARCH",
    "TECHNICAL_RESEARCH",
    "PROPOSAL_RESEARCH",
    "CONSULTING_RESEARCH",
    "INTERACTIVE_RESEARCH",
}


SOURCE_MODES = {"WEB_ONLY", "CORPUS_ONLY", "HYBRID"}


CLAIM_STATUSES = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTED",
    "HYPOTHESIS",
    "ASSUMPTION",
}


GAP_STATUSES = {"GAP_CANDIDATE", "GAP_SUPPORTED", "GAP_UNCERTAIN", "GAP_REJECTED"}


GAP_KINDS = {
    "EVIDENCE_GAP",
    "POPULATION_GAP",
    "METHODOLOGICAL_GAP",
    "TEMPORAL_GAP",
    "GEOGRAPHIC_GAP",
    "IMPLEMENTATION_GAP",
    "MEASUREMENT_GAP",
}


QUESTION_TYPES = {
    "DEFINITION",
    "MECHANISM",
    "COMPARISON",
    "CAUSAL",
    "EVIDENCE",
    "LIMITATION",
    "IMPLEMENTATION",
    "OUTCOME",
    "RISK",
    "COUNTERARGUMENT",
    "CONTEXT",
}


def research_packet_to_dict(packet: ResearchPacket) -> dict[str, Any]:
    return asdict(packet)


def research_run_to_dict(run: ResearchRun) -> dict[str, Any]:
    return asdict(run)
