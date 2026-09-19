from __future__ import annotations

import json
from datetime import datetime, timezone

from xninetzy.context.process_engineering.model import (
    ARTIFACT_STATUS_DRAFT,
    LaneDef,
    NodeDef,
    ProcessArtifact,
    ProcessEdge,
    ProcessLane,
    ProcessModel,
    ProcessNode,
)
from xninetzy.db.sqlite import connect
from xninetzy.os.process_engineering.serializers import (
    artifact_from_row,
    artifact_to_row,
    deserialize_artifact,
    serialize_artifact,
)


def _artifact() -> ProcessArtifact:
    lane = ProcessLane(
        definition=LaneDef(id="ops", name="Ops"), node_ids=("a",)
    )
    nodes = (
        ProcessNode(
            definition=NodeDef(id="start", kind="start", name="Start"),
            outgoing=(ProcessEdge(source_id="start", target_id="a"),),
        ),
        ProcessNode(
            definition=NodeDef(id="a", kind="task", name="Step A", lane_id="ops"),
            outgoing=(ProcessEdge(source_id="a", target_id="end"),),
        ),
        ProcessNode(definition=NodeDef(id="end", kind="end", name="End")),
    )
    return ProcessArtifact(
        artifact_id="a-1",
        model=ProcessModel(
            id="m1",
            title="demo",
            description="",
            nodes=nodes,
            lanes=(lane,),
        ),
        status=ARTIFACT_STATUS_DRAFT,
        format="json",
        created_at="2026-09-20T00:00:00Z",
        updated_at="2026-09-20T00:00:00Z",
        version=1,
    )


def test_serialize_roundtrip_artifact():
    artifact = _artifact()
    text = serialize_artifact(artifact)
    payload = json.loads(text)
    assert payload["artifact_id"] == "a-1"
    again = deserialize_artifact(text)
    assert again.model.id == "m1"
    assert len(again.model.lanes) == 1


def test_artifact_persist_roundtrip():
    artifact = _artifact()
    row = artifact_to_row(artifact)
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO process_artifacts "
            "(artifact_id, status, format, payload_json, updated_at, version) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            row,
        )
        row_data = conn.execute(
            "SELECT * FROM process_artifacts WHERE artifact_id = ?",
            (artifact.artifact_id,),
        ).fetchone()
    loaded = artifact_from_row(row_data)
    assert loaded.artifact_id == artifact.artifact_id
    assert loaded.model.nodes[1].definition.lane_id == "ops"