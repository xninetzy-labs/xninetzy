from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from xninetzy.skills.registry import discover_skills, get_skill


INTENT_CLASSES = {
    "PROFESSIONAL",
    "CONSULTING",
    "PROPOSAL",
    "ACADEMIC",
    "RESEARCH",
    "TECHNICAL",
    "EDITING",
    "REVIEW",
}


INTENT_KEYWORDS = {
    "PROFESSIONAL": ["memo", "brief", "release", "announcement", "business", "product", "case study", "marketing", "communication", "executive", "one-pager", "decision"],
    "CONSULTING": ["analyze", "strategy", "market", "operations", "growth", "competitive", "consult", "hypothesis", "MECE", "diagnose", "options"],
    "PROPOSAL": ["proposal", "grant", "RFP", "competition", "bid", "submission for", "call for", "application", "rubric", "scoring"],
    "ACADEMIC": ["paper", "journal", "thesis", "manuscript", "literature review", "academic", "preprint", "IMRaD", "methodology", "empirical"],
    "RESEARCH": ["research", "investigate", "explore", "literature", "evidence", "synthesis", "claim", "source"],
    "TECHNICAL": ["tutorial", "how-to", "README", "API", "runbook", "technical", "developer", "implementation guide", "outline", "structure"],
    "EDITING": ["edit", "revise", "polish", "rewrite", "improve draft", "proofread", "coherence", "terminology", "argument"],
    "REVIEW": ["review", "critique", "red team", "stress test", "challenge", "audit", "validate", "scoring", "rubric", "readiness", "submission"],
}


@dataclass
class RouteScore:
    skill_name: str
    intent_class: str
    score: float
    signals: list[str] = field(default_factory=list)


@dataclass
class RouteResult:
    request: str
    primary: RouteScore
    secondary: list[RouteScore]
    detected_classes: list[str]
    reasoning: str


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z0-9-]+", text)]


def _score_skill(request: str, skill_name: str, intent_class: str) -> RouteScore:
    if intent_class not in INTENT_CLASSES:
        return RouteScore(skill_name=skill_name, intent_class=intent_class or "UNKNOWN", score=0.0)
    tokens = _tokenize(request)
    keywords = INTENT_KEYWORDS.get(intent_class, [])
    matches = [k for k in keywords if any(k in t or t in k for t in tokens)]
    base_score = 0.2
    keyword_boost = min(0.6, len(matches) * 0.15)
    name_boost = 0.2 if any(part in request.lower() for part in skill_name.split("-")) else 0.0
    return RouteScore(
        skill_name=skill_name,
        intent_class=intent_class,
        score=round(base_score + keyword_boost + name_boost, 3),
        signals=matches + ([f"name:{skill_name}"] if name_boost else []),
    )


def route_request(request: str, top_n: int = 5, allowed_classes: list[str] | None = None) -> RouteResult:
    skills = discover_skills()
    scores: list[RouteScore] = []
    for name, skill in skills.items():
        intent = (skill.metadata or {}).get("intent_class", "")
        if not intent:
            continue
        if allowed_classes and intent not in allowed_classes:
            continue
        scores.append(_score_skill(request, name, intent))
    scores.sort(key=lambda s: s.score, reverse=True)
    primary = scores[0] if scores else RouteScore(skill_name="", intent_class="UNKNOWN", score=0.0)
    secondary = scores[1:top_n]
    classes = sorted({s.intent_class for s in scores if s.score >= 0.4})
    reasoning = "matched by keyword + intent-class metadata" if primary.score > 0 else "no confident match"
    return RouteResult(
        request=request,
        primary=primary,
        secondary=secondary,
        detected_classes=classes,
        reasoning=reasoning,
    )


def compose_skills(skill_names: list[str], request: str = "") -> list[dict[str, Any]]:
    steps = []
    for name in skill_names:
        skill = get_skill(name)
        if not skill:
            continue
        meta = skill.metadata or {}
        steps.append({
            "skill": name,
            "intent_class": meta.get("intent_class", ""),
            "scope": meta.get("scope", ""),
            "consumes": meta.get("consumes", ""),
            "produces": meta.get("produces", ""),
            "description": skill.description,
        })
    return steps


def pipeline_for_intent(intent_class: str) -> list[str]:
    pipelines = {
        "PROFESSIONAL": ["outline-builder", "claim-lattice", "evidence-synthesis", "professional-writer", "argument-coherence", "anti-slop", "submission-readiness"],
        "CONSULTING": ["outline-builder", "claim-lattice", "evidence-synthesis", "consultant", "consultant-challenge", "executive-writer", "argument-coherence"],
        "PROPOSAL": ["outline-builder", "requirement-coverage", "scoring-rubric", "evidence-synthesis", "proposal-writer", "competition-proposal", "proposal-red-team", "submission-readiness"],
        "ACADEMIC": ["outline-builder", "claim-lattice", "source-evaluation", "literature-review-writer", "evidence-synthesis", "academic-writer", "citation-validation", "terminology-bank", "academic-editor", "methodology-rater", "paper-review"],
        "RESEARCH": ["source-evaluation", "claim-lattice", "evidence-synthesis", "citation-validation", "literature-review-writer"],
        "TECHNICAL": ["outline-builder", "evidence-synthesis", "technical-content-writer", "terminology-bank", "anti-slop"],
        "EDITING": ["argument-coherence", "terminology-bank", "professional-editor", "academic-editor", "anti-slop"],
        "REVIEW": ["source-evaluation", "citation-validation", "methodology-rater", "scoring-rubric", "paper-review", "proposal-red-team", "consultant-challenge", "anti-slop", "submission-readiness"],
    }
    return pipelines.get(intent_class, [])
