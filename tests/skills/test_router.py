from xninetzy.skills.router import compose_skills, pipeline_for_intent, route_request


def test_route_professional_request() -> None:
    result = route_request("write a brief product launch memo")
    assert result.primary.skill_name != ""
    assert result.primary.intent_class in {"PROFESSIONAL", "PROPOSAL", "CONSULTING"}


def test_route_proposal_request() -> None:
    result = route_request("draft a grant proposal for a research project")
    assert result.primary.intent_class in {"PROPOSAL", "ACADEMIC"}


def test_route_academic_request() -> None:
    result = route_request("write a literature review for my thesis paper")
    assert result.primary.intent_class in {"ACADEMIC", "RESEARCH"}


def test_pipeline_for_intent() -> None:
    assert "anti-slop" in pipeline_for_intent("PROFESSIONAL")
    assert "submission-readiness" in pipeline_for_intent("PROPOSAL")
    assert "paper-review" not in pipeline_for_intent("CONSULTING")


def test_compose_skills() -> None:
    steps = compose_skills(["evidence-synthesis", "professional-writer"])
    assert len(steps) == 2
    assert steps[0]["skill"] == "evidence-synthesis"
    assert steps[0]["intent_class"] in {"RESEARCH", "REVIEW"}


def test_route_respects_allowed_classes() -> None:
    result = route_request("write a paper", allowed_classes=["PROFESSIONAL"])
    assert result.primary.intent_class in {"PROFESSIONAL"}


def test_pipeline_proposal_includes_requirement_coverage() -> None:
    p = pipeline_for_intent("PROPOSAL")
    assert "requirement-coverage" in p
    assert "scoring-rubric" in p


def test_pipeline_academic_includes_lattice_and_methodology() -> None:
    p = pipeline_for_intent("ACADEMIC")
    assert "claim-lattice" in p
    assert "methodology-rater" in p
    assert "terminology-bank" in p


def test_pipeline_editing_includes_coherence() -> None:
    p = pipeline_for_intent("EDITING")
    assert "argument-coherence" in p
