from __future__ import annotations

import json

import pytest

from xninetzy.integrations.moviepy.capabilities import capability_snapshot

pytestmark = pytest.mark.skipif(
    not capability_snapshot()["ready"],
    reason="moviepy + ffmpeg not available",
)


def _make_clip(path, size, seconds=1.0, fps=24):
    import os

    import imageio_ffmpeg

    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
    from moviepy import ColorClip

    ColorClip(size=size, color=(30, 90, 160)).with_duration(seconds).with_fps(fps).write_videofile(
        str(path), codec="libx264", fps=fps, logger=None
    )


def _dims(path):
    from moviepy import VideoFileClip

    clip = VideoFileClip(str(path))
    try:
        return clip.w, clip.h
    finally:
        clip.close()


def test_reframe_landscape_to_vertical_crop(tmp_path, monkeypatch):
    from xninetzy.core.config import get_settings
    from xninetzy.tools.ecosystem import moviepy_tools

    src = tmp_path / "src.mp4"
    _make_clip(src, (1920, 1080))
    root = tmp_path / "artifacts"
    root.mkdir()
    for key in (
        "OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR",
        "UNTRACKED_OUTPUT_DIR", "VIDEO_OUTPUT_DIR", "DATA_DIR",
    ):
        monkeypatch.setenv(key, str(root))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "true")
    get_settings.cache_clear()
    try:
        out_path = root / "vertical.mp4"
        result = json.loads(
            moviepy_tools.moviepy_reframe.invoke(
                {
                    "input_path": str(src),
                    "output_path": str(out_path),
                    "platform": "youtube_shorts",
                    "mode": "crop",
                }
            )
        )
        assert result["status"] == "ok", result
        assert out_path.exists()
        assert _dims(out_path) == (1080, 1920)
    finally:
        get_settings.cache_clear()


def test_concat_two_clips(tmp_path, monkeypatch):
    from xninetzy.core.config import get_settings
    from xninetzy.tools.ecosystem import moviepy_tools

    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    _make_clip(a, (640, 640), seconds=1.0)
    _make_clip(b, (640, 640), seconds=1.0)
    root = tmp_path / "artifacts"
    root.mkdir()
    for key in (
        "OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR",
        "UNTRACKED_OUTPUT_DIR", "VIDEO_OUTPUT_DIR", "DATA_DIR",
    ):
        monkeypatch.setenv(key, str(root))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "true")
    get_settings.cache_clear()
    try:
        out_path = root / "joined.mp4"
        result = json.loads(
            moviepy_tools.moviepy_concat.invoke(
                {
                    "input_paths": [str(a), str(b)],
                    "output_path": str(out_path),
                    "fps": 24,
                }
            )
        )
        assert result["status"] == "ok", result
        assert result["clip_count"] == 2
        assert out_path.exists()
    finally:
        get_settings.cache_clear()
