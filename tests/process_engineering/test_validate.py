from __future__ import annotations

from xninetzy.context.process_engineering.model import (
    NodeDef,
    ProcessEdge,
    ProcessModel,
    ProcessNode,
    validate_process_model,
)
from xninetzy.context.process_engineering.validate import (
    validate_against_diagram,
    validate_against_xml,
)


def _ok_model() -> ProcessModel:
    nodes = (
        ProcessNode(
            definition=NodeDef(id="start", kind="start", name="Start"),
            outgoing=(ProcessEdge(source_id="start", target_id="end"),),
        ),
        ProcessNode(definition=NodeDef(id="end", kind="end", name="End")),
    )
    return ProcessModel(
        id="ok", title="ok", description="", nodes=nodes, lanes=()
    )


def test_validate_against_diagram_clean():
    report = validate_against_diagram(
        _ok_model(), artifact_id="a1", checked_at="2026-09-20T00:00:00Z"
    )
    assert report.passed
    assert report.issues == ()


def test_validate_against_diagram_flags_issues():
    model = ProcessModel(
        id="bad",
        title="bad",
        description="",
        nodes=(
            ProcessNode(definition=NodeDef(id="only", kind="task", name="Solo")),
        ),
        lanes=(),
    )
    report = validate_against_diagram(
        model, artifact_id="a2", checked_at="2026-09-20T00:00:00Z"
    )
    assert not report.passed
    bucket = report.by_severity()
    assert bucket["structural"]


def test_validate_against_xml_rejects_garbage():
    report = validate_against_xml(
        "<<<not-xml>>>",
        artifact_id="a3",
        checked_at="2026-09-20T00:00:00Z",
    )
    assert not report.passed
    assert any(issue.code == "xml" for issue in report.issues)