from __future__ import annotations

from xninetzy.integrations.moviepy import capabilities


def test_capability_snapshot_shape():
    snap = capabilities.capability_snapshot()
    for key in ("moviepy_available", "ffmpeg_available", "ready", "ffmpeg_source"):
        assert key in snap
    assert isinstance(snap["ready"], bool)


def test_editor_gates_when_moviepy_missing(monkeypatch):
    from xninetzy.integrations.moviepy import editor

    monkeypatch.setattr(editor, "moviepy_available", lambda: False)
    import pytest

    with pytest.raises(editor.MoviePyUnavailable):
        editor.reframe_video("in.mp4", "out.mp4", 1080, 1920)


def test_tool_reports_unavailable(monkeypatch, tmp_path):
    import json

    from xninetzy.integrations.moviepy import editor
    from xninetzy.tools.ecosystem import moviepy_tools

    src = tmp_path / "in.mp4"
    src.write_bytes(b"not really a video")
    monkeypatch.setattr(editor, "moviepy_available", lambda: False)
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "false")
    out = json.loads(
        moviepy_tools.moviepy_reframe.invoke(
            {"input_path": str(src), "output_path": str(tmp_path / "out.mp4")}
        )
    )
    assert out["status"] == "unavailable"


def test_tool_blocks_output_outside_artifact_roots(monkeypatch, tmp_path):
    import json

    from xninetzy.core.config import get_settings
    from xninetzy.tools.ecosystem import moviepy_tools

    src_dir = tmp_path / "inputs"
    src_dir.mkdir()
    src = src_dir / "in.mp4"
    src.write_bytes(b"data")
    root = tmp_path / "artifacts"
    root.mkdir()
    escape_dir = tmp_path / "elsewhere"
    escape_dir.mkdir()
    for key in (
        "OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR",
        "UNTRACKED_OUTPUT_DIR", "VIDEO_OUTPUT_DIR", "DATA_DIR",
    ):
        monkeypatch.setenv(key, str(root))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "true")
    get_settings.cache_clear()
    try:
        out = json.loads(
            moviepy_tools.moviepy_reframe.invoke(
                {"input_path": str(src), "output_path": str(escape_dir / "escape.mp4")}
            )
        )
        assert out["status"] == "error"
        assert "ARTIFACT_ALLOWLIST" in out["error"]
    finally:
        get_settings.cache_clear()
