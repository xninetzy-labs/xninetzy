from __future__ import annotations

import math

from xninetzy.context.media.video.models import (
    CANONICAL_PRIMITIVES,
    Easing,
    Keyframe,
    MotionPreset,
    VideoComposition,
    VideoProject,
    Resolution,
)
from xninetzy.context.media.video.models import easing_value, interpolate_keyframes
from xninetzy.context.media.video import storage
from xninetzy.context.media.video.motion import resolve_primitive


def test_resolution_validates_safe_envelope():
    Resolution(640, 360)
    Resolution(1920, 1080)
    Resolution(3840, 2160)
    try:
        Resolution(0, 0)
        assert False, "should reject zero"
    except ValueError:
        pass
    try:
        Resolution(99999, 99999)
        assert False, "should reject > 8K"
    except ValueError:
        pass


def test_easing_value_endpoints():
    for e in Easing:
        assert easing_value(e, 0.0) == 0.0
        assert easing_value(e, 1.0) == 1.0


def test_easing_value_monotone_in_window():
    for e in (Easing.LINEAR, Easing.EASE_IN, Easing.EASE_OUT, Easing.EASE_IN_OUT):
        prev = easing_value(e, 0.0)
        for i in range(1, 101):
            t = i / 100.0
            v = easing_value(e, t)
            assert v >= prev - 1e-9, f"easing {e} not monotone at t={t}"
            prev = v


def test_keyframe_rejects_non_finite():
    try:
        Keyframe(property="opacity", frame=0, value=math.nan)
        assert False
    except ValueError:
        pass
    try:
        Keyframe(property="opacity", frame=-1, value=1.0)
        assert False
    except ValueError:
        pass


def test_interpolate_keyframes_constant():
    keys = [
        Keyframe(property="scale", frame=0, value=1.0),
        Keyframe(property="scale", frame=30, value=1.5, easing=Easing.EASE_IN_OUT),
        Keyframe(property="scale", frame=60, value=2.0),
    ]
    assert interpolate_keyframes(keys, "scale", 0) == 1.0
    assert interpolate_keyframes(keys, "scale", 60) == 2.0
    assert interpolate_keyframes(keys, "scale", 90) == 2.0
    assert interpolate_keyframes(keys, "scale", -1) == 1.0


def test_interpolate_keyframes_unknown_property():
    keys = [Keyframe(property="opacity", frame=0, value=0.0)]
    assert interpolate_keyframes(keys, "scale", 30) is None


def test_motion_preset_rejects_unknown_primitive():
    try:
        MotionPreset(
            primitive="WarpSpeed",
            target="x",
            start_frame=0,
            end_frame=10,
        )
        assert False
    except ValueError:
        pass


def test_canonical_primitives_unique():
    assert len(CANONICAL_PRIMITIVES) == len(set(CANONICAL_PRIMITIVES))


def test_resolve_primitive_fade_in_yields_keyframes():
    p = MotionPreset(
        primitive="FadeIn",
        target="title",
        start_frame=0,
        end_frame=30,
    )
    keys = resolve_primitive(p)
    assert any(k.property == "opacity" for k in keys)
    assert keys[0].value == 0.0


def test_motion_preset_rejects_unknown_primitive_in_constructor():
    try:
        MotionPreset(
            primitive="NonExistentPrimitive",
            target="x",
            start_frame=0,
            end_frame=10,
        )
        assert False, "constructor should reject unknown primitive"
    except ValueError:
        pass


def test_video_composition_duration_limit():
    c = VideoComposition(
        composition_id="c1",
        name="c1",
        resolution=Resolution(640, 360),
        fps=30,
        duration_frames=30,
    )
    assert c.duration_seconds() == 1.0
    try:
        VideoComposition(
            composition_id="c2",
            name="c2",
            resolution=Resolution(640, 360),
            fps=30,
            duration_frames=30 * 700,
        )
        assert False
    except ValueError:
        pass


def test_video_project_requires_composition():
    try:
        VideoProject(
            project_id="x",
            name="x",
            source_project_root=None,
            schema_version="1",
            compositions=[],
            scenes=[],
            assets=[],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            version=1,
        )
        assert False
    except ValueError:
        pass


def test_storage_content_hash_stable():
    assert storage.content_hash("abc") == storage.content_hash("abc")
    assert storage.content_hash("abc") != storage.content_hash("xyz")
