from __future__ import annotations

import time
from dataclasses import dataclass, field

from xninetzy.os.research import router as _research_router
from xninetzy.schemas.research_packet import (
    Claim,
    Evidence,
    OutlineSection,
    ResearchBrief,
    ResearchGap,
    ResearchOutline,
    ResearchPacket,
    ResearchPerspective,
    ResearchQuestion,
    ResearchRun,
    SourceRecord,
    Contradiction,
)


PERSPECTIVE_TEMPLATES = [
    ("scientific", "Scientific / empirical perspective grounded in primary research"),
    ("technical", "Technical / implementation perspective focused on systems and architecture"),
    ("clinical", "Clinical / applied perspective focused on real-world deployment"),
    ("economic", "Economic / market perspective focused on cost, value, and incentives"),
    ("regulatory", "Regulatory / compliance perspective focused on policy and standards"),
    ("user", "User / stakeholder perspective focused on experience and adoption"),
    ("implementation", "Implementation perspective focused on operational deployment"),
    ("historical", "Historical perspective focused on prior work and evolution"),
    ("methodological", "Methodological perspective focused on study design and evidence quality"),
    ("ethical", "Ethical / societal perspective focused on impact and responsibility"),
    ("operational", "Operational perspective focused on day-to-day execution"),
]


@dataclass
class EngineConfig:
    max_perspectives: int = 5
    max_questions_per_perspective: int = 4
    max_conversation_turns: int = 4
    search_top_k: int = 5
    retrieve_top_k: int = 5
    max_sources: int = 50
    max_evidence: int = 200
    remove_duplicates: bool = True
    depth: str = "STANDARD"


def discover_perspectives(topic: str, brief: ResearchBrief | None = None, config: EngineConfig | None = None) -> list[ResearchPerspective]:
    cfg = config or EngineConfig()
    text = (topic + " " + (brief.scope if brief else "")).lower()
    chosen: list[tuple[str, str]] = []
    for name, desc in PERSPECTIVE_TEMPLATES:
        if name in text or len(chosen) < cfg.max_perspectives:
            chosen.append((name, desc))
        if len(chosen) >= cfg.max_perspectives:
            break
    if not chosen:
        chosen = [("technical", "Technical perspective on " + topic), ("user", "User perspective on " + topic)]
    perspectives = []
    for name, desc in chosen[: cfg.max_perspectives]:
        perspectives.append(ResearchPerspective(name=name, description=desc, rationale=f"Relevant for topic '{topic}'"))
    return perspectives


def generate_questions(perspective: ResearchPerspective, topic: str, config: EngineConfig | None = None) -> list[ResearchQuestion]:
    cfg = config or EngineConfig()
    types = ["DEFINITION", "EVIDENCE", "MECHANISM", "LIMITATION", "COMPARISON", "IMPLEMENTATION"]
    questions = []
    for qtype in types[: cfg.max_questions_per_perspective]:
        text = {
            "DEFINITION": f"What is the definition and core concept of {topic} from the {perspective.name} perspective?",
            "EVIDENCE": f"What empirical evidence supports claims about {topic}?",
            "MECHANISM": f"How does {topic} actually work mechanistically?",
            "LIMITATION": f"What are the known limitations of {topic}?",
            "COMPARISON": f"How does {topic} compare to alternatives from the {perspective.name} view?",
            "IMPLEMENTATION": f"How is {topic} implemented in practice?",
        }[qtype]
        questions.append(ResearchQuestion(perspective_id=perspective.perspective_id, question=text, question_type=qtype))
    return questions


def consolidate_evidence(sources: list[SourceRecord], questions: list[ResearchQuestion]) -> list[Evidence]:
    evidence_list: list[Evidence] = []
    for idx, source in enumerate(sources):
        for q in questions[:2]:
            evidence_list.append(
                Evidence(
                    source_id=source.source_id,
                    excerpt=source.excerpt or f"Source {idx + 1} content excerpt",
                    location=source.url,
                    question_ids=[q.question_id],
                    confidence=0.6,
                    scope=source.source_type,
                )
            )
    return evidence_list


def extract_claims(evidence_list: list[Evidence]) -> list[Claim]:
    claims: list[Claim] = []
    for ev in evidence_list:
        claim_text = f"Claim supported by evidence {ev.evidence_id[:8]}"
        status = "SUPPORTED" if ev.confidence >= 0.5 else "UNSUPPORTED"
        claims.append(Claim(statement=claim_text, evidence_ids=[ev.evidence_id], status=status, confidence=ev.confidence))
    return claims


def detect_contradictions(claims: list[Claim]) -> list[Contradiction]:
    contradictions: list[Contradiction] = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if claims[i].status == "CONTRADICTED" or claims[j].status == "CONTRADICTED":
                contradictions.append(
                    Contradiction(
                        claim_a_id=claims[i].claim_id,
                        claim_b_id=claims[j].claim_id,
                        reason="Status contradiction",
                        possible_cause="Different populations or methodology",
                        evidence_ids=claims[i].evidence_ids + claims[j].evidence_ids,
                    )
                )
    return contradictions


def detect_gaps(claims: list[Claim], evidence_list: list[Evidence], brief: ResearchBrief) -> list[ResearchGap]:
    gaps: list[ResearchGap] = []
    if len(evidence_list) < 5:
        gaps.append(ResearchGap(description="Insufficient evidence collected", gap_kind="EVIDENCE_GAP", status="GAP_SUPPORTED"))
    if not any(c.status == "SUPPORTED" for c in claims):
        gaps.append(ResearchGap(description="No supported claims yet", gap_kind="EVIDENCE_GAP", status="GAP_CANDIDATE"))
    return gaps


def build_outline(packet: ResearchPacket, brief: ResearchBrief) -> ResearchOutline:
    sections = [
        OutlineSection(
            heading="Executive Summary",
            key_questions=[q.question for q in packet.questions[:2]],
            key_claim_ids=[c.claim_id for c in packet.claims[:2]],
            evidence_ids=[e.evidence_id for e in packet.evidence[:3]],
        ),
        OutlineSection(
            heading="Method",
            key_questions=["How was research conducted?"],
            evidence_ids=[e.evidence_id for e in packet.evidence[:5]],
        ),
        OutlineSection(
            heading="Findings",
            key_claim_ids=[c.claim_id for c in packet.claims],
            evidence_ids=[e.evidence_id for e in packet.evidence],
        ),
        OutlineSection(
            heading="Contradictions and Gaps",
            key_claim_ids=[c.claim_id for c in packet.claims if c.status == "CONTRADICTED"],
            unresolved_issue_ids=[g.gap_id for g in packet.gaps],
        ),
        OutlineSection(
            heading="Limitations",
            evidence_ids=[e.evidence_id for e in packet.evidence[:2]],
        ),
    ]
    return ResearchOutline(sections=sections)


def build_research_packet(run: ResearchRun, sources: list[SourceRecord]) -> ResearchPacket:
    perspectives = discover_perspectives(run.topic, run.brief)
    questions: list[ResearchQuestion] = []
    for p in perspectives:
        questions.extend(generate_questions(p, run.topic))
    evidence_list = consolidate_evidence(sources, questions)
    claims = extract_claims(evidence_list)
    contradictions = detect_contradictions(claims)
    gaps = detect_gaps(claims, evidence_list, run.brief)
    packet = ResearchPacket(
        research_run_id=run.run_id,
        topic=run.topic,
        scope=run.brief.scope,
        perspectives=perspectives,
        questions=questions,
        sources=sources,
        evidence=evidence_list,
        claims=claims,
        contradictions=contradictions,
        gaps=gaps,
    )
    packet.outline = build_outline(packet, run.brief)
    return packet


def start_run(topic: str, brief: ResearchBrief | None = None, mode: str = "STANDARD", source_mode: str = "hybrid", owner_id: str = "", project_id: str = "") -> ResearchRun:
    run = ResearchRun(topic=topic, brief=brief or ResearchBrief(topic=topic), mode=mode, source_mode=source_mode, owner_id=owner_id, project_id=project_id, status="PLANNING")
    return run


def advance_run(run: ResearchRun, sources: list[SourceRecord] | None = None) -> ResearchRun:
    run.status = "DISCOVERING_PERSPECTIVES"
    run.perspective_count = len(discover_perspectives(run.topic, run.brief))
    run.status = "GENERATING_QUESTIONS"
    perspectives = discover_perspectives(run.topic, run.brief)
    run.question_count = sum(len(generate_questions(p, run.topic)) for p in perspectives)
    run.status = "RETRIEVING"
    run.source_count = len(sources) if sources else 0
    run.status = "CONSOLIDATING_EVIDENCE"
    if sources:
        questions = []
        for p in perspectives:
            questions.extend(generate_questions(p, run.topic))
        evidence = consolidate_evidence(sources, questions)
        run.evidence_count = len(evidence)
        claims = extract_claims(evidence)
        run.claim_count = len(claims)
        run.contradiction_count = len(detect_contradictions(claims))
        run.gap_count = len(detect_gaps(claims, evidence, run.brief))
    run.status = "COMPLETED"
    run.completed_at = time.time()
    return run
