from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from xninetzy.skills.router import (
    INTENT_CLASSES,
    compose_skills,
    pipeline_for_intent,
    route_request,
)
from xninetzy.skills.validators import (
    anti_slop,
    citation_fidelity,
    evidence_claim_alignment,
    requirement_coverage,
    run_all,
    submission_readiness_check,
    terminology_consistency,
)
from xninetzy.tools.tool_results import to_tool_result


@tool
def skill_route(
    request: str,
    top_n: int = 5,
    allowed_classes: list[str] | None = None,
) -> str:
    """Route a writing/proposal/academic request to the best matching skill.

    Args:
        request: Free-text request.
        top_n: Max candidates to return.
        allowed_classes: Optional list of intent classes to consider.
    """
    result = route_request(request, top_n=top_n, allowed_classes=allowed_classes)
    return to_tool_result(json.dumps({
        "request": result.request,
        "primary": {
            "skill": result.primary.skill_name,
            "intent_class": result.primary.intent_class,
            "score": result.primary.score,
            "signals": result.primary.signals,
        },
        "secondary": [{"skill": s.skill_name, "intent_class": s.intent_class, "score": s.score} for s in result.secondary],
        "detected_classes": result.detected_classes,
        "reasoning": result.reasoning,
    }, ensure_ascii=False))


@tool
def skill_compose(
    request: str = "",
    intent_class: str = "",
    explicit_skills: list[str] | None = None,
) -> str:
    """Compose a multi-skill pipeline for a writing request.

    Args:
        request: Original request (used to pick intent class if not specified).
        intent_class: Optional intent class to drive pipeline selection.
        explicit_skills: Optional override list of skill names.
    """
    if explicit_skills:
        steps = compose_skills(explicit_skills, request)
        return to_tool_result(json.dumps({"intent_class": intent_class, "steps": steps}, ensure_ascii=False))
    ic = intent_class
    if not ic and request:
        result = route_request(request, top_n=1)
        ic = result.primary.intent_class
    skill_names = pipeline_for_intent(ic)
    steps = compose_skills(skill_names, request)
    return to_tool_result(json.dumps({
        "intent_class": ic,
        "pipeline": skill_names,
        "steps": steps,
    }, ensure_ascii=False))


@tool
def skill_validate_output(
    text: str,
    requirements: list[str] | None = None,
    approved_citations: list[str] | None = None,
    approved_terms: list[str] | None = None,
) -> str:
    """Run all writing-quality validators against a draft.

    Args:
        text: Draft text to validate.
        requirements: Optional list of explicit requirements to check coverage for.
        approved_citations: Optional list of approved citation keys.
        approved_terms: Optional list of approved terminology.
    """
    reports = run_all(text, requirements or [], approved_citations, approved_terms)
    summary = {
        "passed": all(r.passed for r in reports),
        "validators": [
            {
                "name": r.validator,
                "passed": r.passed,
                "finding_count": len(r.findings),
                "findings": [
                    {
                        "severity": f.severity,
                        "location": f.location,
                        "message": f.message,
                        "suggestion": f.suggestion,
                    }
                    for f in r.findings
                ],
            }
            for r in reports
        ],
    }
    return to_tool_result(json.dumps(summary, ensure_ascii=False))


@tool
def skill_validate_anti_slop(text: str) -> str:
    """Run only the anti-slop validator.

    Args:
        text: Draft text.
    """
    r = anti_slop(text)
    return to_tool_result(json.dumps({"passed": r.passed, "findings": [{"location": f.location, "message": f.message} for f in r.findings]}, ensure_ascii=False))


@tool
def skill_validate_submission_readiness(
    text: str,
    requirements: list[str],
    approved_citations: list[str] | None = None,
) -> str:
    """Run a pre-submission readiness check.

    Args:
        text: Final draft text.
        requirements: Submission requirements.
        approved_citations: Approved citation set.
    """
    r = submission_readiness_check(text, requirements, approved_citations)
    return to_tool_result(json.dumps({
        "passed": r.passed,
        "validator": r.validator,
        "findings": [{"severity": f.severity, "location": f.location, "message": f.message, "suggestion": f.suggestion} for f in r.findings],
    }, ensure_ascii=False))


@tool
def skill_capabilities() -> str:
    """Return skill-routing and validation capabilities."""
    return to_tool_result(json.dumps({
        "skill_router": True,
        "skill_composer": True,
        "validators": [
            "anti-slop",
            "citation-fidelity",
            "evidence-claim-alignment",
            "requirement-coverage",
            "terminology-consistency",
            "numeric-consistency",
            "submission-readiness",
        ],
        "intent_classes": sorted(INTENT_CLASSES),
    }, ensure_ascii=False))


skill_routing_tools = [
    skill_route,
    skill_compose,
    skill_validate_output,
    skill_validate_anti_slop,
    skill_validate_submission_readiness,
    skill_capabilities,
]
