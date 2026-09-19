from __future__ import annotations

import yaml

from xninetzy.os.notes.template_service import TemplateService


def test_template_learning_note_escapes_quotes_in_title() -> None:
    ts = TemplateService()
    _, content = ts.learning_note('My "Project"; rm -rf / #')
    parsed = yaml.safe_load(content.split("---", 2)[1])
    assert parsed is not None
    assert isinstance(parsed, dict)
    assert parsed["title"] == 'My "Project"; rm -rf / #'
    assert parsed["topic"] == 'My "Project"; rm -rf / #'


def test_template_project_note_escapes_yaml_special_chars() -> None:
    ts = TemplateService()
    _, content = ts.project_note("name: injection\nkey: value")
    parsed = yaml.safe_load(content.split("---", 2)[1])
    assert isinstance(parsed, dict)
    assert parsed["title"] == "name: injection\nkey: value"


def test_template_task_note_rejects_invalid_priority() -> None:
    ts = TemplateService()
    try:
        ts.task_note("X", priority="nonsense")
    except ValueError as exc:
        assert "priority tidak valid" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_template_task_note_rejects_invalid_status() -> None:
    ts = TemplateService()
    try:
        ts.task_note("X", status="unknown")
    except ValueError as exc:
        assert "status tidak valid" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_template_task_note_rejects_invalid_deadline() -> None:
    ts = TemplateService()
    try:
        ts.task_note("X", deadline="not-a-date")
    except ValueError as exc:
        assert "deadline" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")


def test_template_daily_note_rejects_invalid_date() -> None:
    ts = TemplateService()
    try:
        ts.daily_note("2026/09/19")
    except ValueError as exc:
        assert "YYYY-MM-DD" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_template_project_uses_slugify_collapse() -> None:
    ts = TemplateService()
    _, content = ts.project_note("Hello   World!!  ")
    parsed = yaml.safe_load(content.split("---", 2)[1])
    assert isinstance(parsed, dict)
    canonical = parsed["canonical_path"]
    assert "hello-world" in canonical
    assert "--" not in canonical.split("/")[-2]
