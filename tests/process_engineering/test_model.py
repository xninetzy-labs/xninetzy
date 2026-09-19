from __future__ import annotations

from xninetzy.context.process_engineering.model import (
    NodeDef,
    ProcessEdge,
    ProcessModel,
    ProcessNode,
    artifact_statuses,
    node_kinds,
    validate_process_model,
)


def _sample_model() -> ProcessModel:
    nodes = (
        ProcessNode(
            definition=NodeDef(id="start", kind="start", name="Start"),
            outgoing=(ProcessEdge(source_id="start", target_id="a"),),
        ),
        ProcessNode(
            definition=NodeDef(id="a", kind="task", name="Step A"),
            outgoing=(ProcessEdge(source_id="a", target_id="end"),),
        ),
        ProcessNode(definition=NodeDef(id="end", kind="end", name="End")),
    )
    return ProcessModel(
        id="p1",
        title="Sample",
        description="",
        nodes=nodes,
        lanes=(),
    )


def test_node_kinds_and_statuses_are_sorted():
    assert "end" in node_kinds()
    assert "draft" in artifact_statuses()


def test_validate_process_model_clean():
    issues = validate_process_model(_sample_model())
    assert issues == []


def test_validate_process_model_missing_end():
    nodes = (
        ProcessNode(
            definition=NodeDef(id="start", kind="start", name="Start"),
            outgoing=(ProcessEdge(source_id="start", target_id="only"),),
        ),
        ProcessNode(definition=NodeDef(id="only", kind="task", name="Solo")),
    )
    model = ProcessModel(
        id="p1", title="x", description="", nodes=nodes, lanes=()
    )
    issues = validate_process_model(model)
    assert any("no end node" in msg for msg in issues)


def test_validate_process_model_detects_duplicate_nodes():
    nodes = (
        ProcessNode(definition=NodeDef(id="dup", kind="task", name="A")),
        ProcessNode(definition=NodeDef(id="dup", kind="task", name="B")),
    )
    model = ProcessModel(
        id="p1", title="x", description="", nodes=nodes, lanes=()
    )
    issues = validate_process_model(model)
    assert any("duplicate node" in msg for msg in issues)