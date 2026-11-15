from __future__ import annotations


from xninetzy.context.media.video.validators import (
    validate_project,
    validate_motion_preset,
    validate_path_within_roots,
    validate_render_request,
)
from xninetzy.context.media.video.models import (
    Easing,
    MotionPreset,
    RenderRequest,
    VideoComposition,
    VideoProject,
    VideoScene,
    Resolution,
)


def _baseline_project() -> VideoProject:
    composition = VideoComposition(
        composition_id="c",
        name="c",
        resolution=Resolution(640, 360),
        fps=30,
        duration_frames=30,
    )
    return VideoProject(
        project_id="p",
        name="p",
        source_project_root=None,
        schema_version="1",
        compositions=[composition],
        scenes=[],
        assets=[],
        created_at="t",
        updated_at="t",
        version=1,
    )


def test_validate_project_minimal_ok():
    report = validate_project(_baseline_project())
    assert report.ok
    assert not report.errors


def test_validate_project_unknown_scene_composition_id():
    p = _baseline_project()
    valid_scene = VideoScene(
        scene_id="s1",
        composition_id=p.compositions[0].composition_id,
        name="s",
        start_frame=0,
        duration_frames=10,
    )
    pp = VideoProject(
        project_id=p.project_id,
        name=p.name,
        source_project_root=p.source_project_root,
        schema_version=p.schema_version,
        compositions=p.compositions,
        scenes=[valid_scene],
        assets=p.assets,
        created_at=p.created_at,
        updated_at=p.updated_at,
        version=p.version,
    )
    object.__setattr__(
        pp.scenes[0], "composition_id", "__missing__"
    )
    assert not validate_project(pp).ok


def test_validate_motion_preset_rejects_unknown_primitive():
    try:
        MotionPreset(
            primitive="Unknown",
            target="x",
            start_frame=0,
            end_frame=10,
        )
        assert False
    except ValueError:
        pass


def test_validate_motion_preset_valid():
    p = MotionPreset(
        primitive="FadeIn",
        target="title",
        start_frame=0,
        end_frame=30,
        easing=Easing.EASE_IN_OUT,
    )
    assert validate_motion_preset(p).ok


def test_validate_render_request_invalid_format():
    req = RenderRequest.__new__(RenderRequest)
    object.__setattr__(req, "project_id", "p")
    object.__setattr__(req, "composition_id", "c")
    object.__setattr__(req, "project_version", 1)
    object.__setattr__(req, "output_format", "avi")
    object.__setattr__(req, "output_path", "/tmp/x.avi")
    object.__setattr__(req, "props_path", "/tmp/x.json")
    object.__setattr__(req, "quality", "balanced")
    object.__setattr__(req, "concurrency", 1)
    object.__setattr__(req, "width", 0)
    object.__setattr__(req, "height", 0)
    object.__setattr__(req, "fps", 0)
    object.__setattr__(req, "duration_frames", 0)
    object.__setattr__(req, "max_runtime_seconds", 1800)
    object.__setattr__(req, "preview", False)
    assert not validate_render_request(req, 30, 1920, 1080, 900).ok


def test_validate_path_within_roots_rejects_traversal():
    assert not validate_path_within_roots(
        "../../etc/passwd",
        ("/home/user/xninetzy/output",),
    )


def test_validate_path_within_roots_allows_safe():
    assert validate_path_within_roots(
        "/home/user/xninetzy/output/video/x.mp4",
        ("/home/user/xninetzy/output",),
    )
