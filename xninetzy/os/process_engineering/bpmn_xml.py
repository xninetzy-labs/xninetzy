from __future__ import annotations

import json
from pathlib import Path

from xninetzy.context.process_engineering.bpmn_io import (
    parse_bpmn_text,
    render_bpmn_text,
)
from xninetzy.context.process_engineering.model import (
    ARTIFACT_STATUS_DRAFT,
    ProcessArtifact,
    ProcessModel,
)
from xninetzy.os.process_engineering.serializers import (
    deserialize_artifact,
    serialize_artifact,
)


def save_artifact(artifact: ProcessArtifact, target_path: Path) -> None:
    target_path = Path(target_path)
    if artifact.format == "bpmn":
        target_path.write_text(render_bpmn_text(artifact.model), encoding="utf-8")
        return
    target_path.write_text(serialize_artifact(artifact), encoding="utf-8")


def load_artifact(source_path: Path) -> ProcessArtifact:
    source_path = Path(source_path)
    text = source_path.read_text(encoding="utf-8")
    if text.lstrip().startswith("<?xml") or text.lstrip().startswith("<"):
        model = parse_bpmn_text(text)
        return ProcessArtifact(
            artifact_id=source_path.stem,
            model=model,
            status=ARTIFACT_STATUS_DRAFT,
            format="bpmn",
            created_at="",
            updated_at="",
            version=1,
        )
    return deserialize_artifact(text)