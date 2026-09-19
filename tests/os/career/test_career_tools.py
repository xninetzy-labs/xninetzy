from __future__ import annotations

from xninetzy.tools.ecosystem.career_tools import career_tools
from xninetzy.tools.registry import get_tool_groups


EXPECTED = {
    "career_search_jobs",
    "career_search_internships",
    "career_skill_gap",
    "career_market_skill_trend",
    "career_resume_tailor",
    "career_search_companies",
    "career_get_job",
    "career_extract_requirements",
    "career_company_research",
    "career_salary_analysis",
    "career_find_similar_jobs",
    "career_find_alternative_titles",
    "career_find_hidden_jobs",
    "career_monitor",
    "career_track_application",
    "career_interview_prep",
    "career_resume_analysis",
}


def test_career_tools_list_complete() -> None:
    names = {t.name for t in career_tools}
    missing = EXPECTED - names
    assert not missing, f"missing from career_tools: {missing}"


def test_career_tool_group_complete() -> None:
    groups = get_tool_groups()
    career_group = set(groups.get("career", []))
    missing = EXPECTED - career_group
    assert not missing, f"missing from career group: {missing}"


def test_career_alternative_titles_expand() -> None:
    from xninetzy.tools.ecosystem.career_tools import _expand_title

    expansions = _expand_title("backend")
    assert "backend" in expansions
    assert any("backend engineer" in term for term in expansions)


def test_career_requirement_keywords() -> None:
    from xninetzy.tools.ecosystem.career_tools import _extract_requirements

    snippet = "We require 5 years of Python experience, knowledge of FastAPI, and Docker."
    keywords = _extract_requirements(snippet)
    assert "python" in keywords
    assert "docker" in keywords
    assert "experience" in keywords


def test_career_salary_parse() -> None:
    from xninetzy.tools.ecosystem.career_tools import _parse_salary

    parsed = _parse_salary("Salary: USD 120k")
    assert parsed is not None
    currency, _rate, amount = parsed
    assert currency == "usd"
    assert amount >= 1000


def test_career_salary_parse_no_match() -> None:
    from xninetzy.tools.ecosystem.career_tools import _parse_salary

    assert _parse_salary("competitive salary") is None
