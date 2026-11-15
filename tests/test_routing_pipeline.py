from __future__ import annotations

from xninetzy.context.routing.pipeline import (
    PipelineOutcome,
    load_pipeline_outcome,
    normalize_request,
    run_pipeline,
)


def test_normalize_request_extracts_entities() -> None:
    n = normalize_request("submit my HEBAT assignment and find the video_render docs")
    assert "hebat" in n.entities
    assert "video_render" in n.entities
    assert n.language in ("en", "id")
    assert n.constraints == ()


def test_normalize_request_detects_negation() -> None:
    n = normalize_request("don't render anything without gpu")
    assert "has_negation" in n.constraints


def test_pipeline_returns_outcome(tmp_path) -> None:
    out = run_pipeline(
        "submit to HEBAT",
        request_id="test-1",
        idempotency_key="idem-1",
        calibration_dir=str(tmp_path / "calibration"),
        persist=False,
    )
    assert isinstance(out, PipelineOutcome)
    assert out.selected_tool
    assert out.total_latency_ms >= 0


def test_pipeline_persists_and_replays(tmp_path) -> None:
    out = run_pipeline(
        "find research papers on adaptive learning",
        request_id="test-2",
        idempotency_key="idem-2",
        calibration_dir=str(tmp_path / "calibration"),
        persist=True,
    )
    snap = load_pipeline_outcome(out.request_id)
    assert snap is not None
    assert snap["request_id"] == out.request_id
    assert snap["selected_tool"]
