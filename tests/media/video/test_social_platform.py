from __future__ import annotations


import uuid

from xninetzy.context.media.video.models import CompositionPreset
from xninetzy.context.media.video.social import (
    PLATFORM_SPECS,
    available_platforms,
    validate_for_platform,
)
from xninetzy.context.media.video.templates import (
    TemplateContext,
    project_demo_template,
)


def _project(preset: CompositionPreset, duration_seconds: float = 10.0, fps: int = 30):
    ctx = TemplateContext(
        project_id=f"proj-{uuid.uuid4().hex[:8]}",
        name="t",
        fps=fps,
        preset=preset,
        duration_seconds=duration_seconds,
    )
    return project_demo_template(ctx)


def test_platform_specs_cover_major_targets():
    for name in ("tiktok", "instagram_reels", "youtube_shorts", "youtube_landscape"):
        assert name in PLATFORM_SPECS
    assert available_platforms() == sorted(PLATFORM_SPECS)


def test_vertical_project_passes_shorts():
    project = _project(CompositionPreset.SHORTS_VERTICAL, duration_seconds=30.0)
    report = validate_for_platform(project, "youtube_shorts")
    assert report.ok, report.errors
    assert report.measured["width"] == 1080
    assert report.measured["height"] == 1920


def test_landscape_project_fails_reels_aspect():
    project = _project(CompositionPreset.YOUTUBE_LANDSCAPE, duration_seconds=30.0)
    report = validate_for_platform(project, "instagram_reels")
    assert not report.ok
    assert any("aspect" in e for e in report.errors)


def test_reels_duration_cap_enforced():
    project = _project(CompositionPreset.INSTAGRAM_VERTICAL, duration_seconds=120.0)
    report = validate_for_platform(project, "instagram_reels")
    assert not report.ok
    assert any("duration" in e for e in report.errors)


def test_unknown_platform_reports_error():
    project = _project(CompositionPreset.SHORTS_VERTICAL)
    report = validate_for_platform(project, "myspace")
    assert not report.ok
    assert any("unknown platform" in e for e in report.errors)


def test_tool_validates_and_lists(tmp_path, monkeypatch):
    import json

    from xninetzy.tools.ecosystem.media_video_tools import (
        video_platform_targets,
        video_project_create,
        video_validate_for_platform,
    )

    monkeypatch.setenv("VIDEO_GENERATION_ENABLED", "true")
    targets = json.loads(video_platform_targets.invoke({}))
    assert "tiktok" in targets

    created = json.loads(
        video_project_create.invoke({"name": "demo", "preset": "shorts_vertical"})
    )
    pid = created.get("project_id") or (created.get("project") or {}).get("project_id")
    assert pid
    report = json.loads(
        video_validate_for_platform.invoke({"project_id": pid, "platform": "youtube_shorts"})
    )
    assert report["ok"] is True


def test_tool_unknown_project():
    import json

    from xninetzy.tools.ecosystem.media_video_tools import video_validate_for_platform

    report = json.loads(
        video_validate_for_platform.invoke({"project_id": "nope", "platform": "tiktok"})
    )
    assert report["ok"] is False
