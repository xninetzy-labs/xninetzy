from __future__ import annotations

import pytest

from xninetzy.context.media.video.models import (
    CANONICAL_PRIMITIVES,
    Easing,
    MotionPreset,
    easing_value,
    interpolate_keyframes,
)
from xninetzy.context.media.video.motion import resolve_primitive

ADVANCED_PRIMITIVES = [
    "Bounce", "Elastic", "Rotate", "Flip3D", "Swing",
    "Wiggle", "Shake", "Orbit", "Parallax", "PathMove",
    "MotionBlurStreak", "GlowPulse", "PulseScale",
]

ADVANCED_EASINGS = [
    Easing.EASE_IN_BACK, Easing.EASE_OUT_BACK, Easing.EASE_IN_OUT_BACK,
    Easing.EASE_OUT_ELASTIC, Easing.EASE_OUT_BOUNCE, Easing.EASE_OUT_EXPO,
    Easing.EASE_OUT_CIRC, Easing.ANTICIPATE,
]


def test_advanced_primitives_registered():
    for name in ADVANCED_PRIMITIVES:
        assert name in CANONICAL_PRIMITIVES


def test_advanced_easings_endpoints():
    for e in ADVANCED_EASINGS:
        assert easing_value(e, 0.0) == 0.0
        assert easing_value(e, 1.0) == 1.0


def test_back_easing_overshoots():
    assert easing_value(Easing.EASE_OUT_BACK, 0.7) > 1.0


def test_bounce_easing_stays_in_unit_band():
    for i in range(1, 100):
        v = easing_value(Easing.EASE_OUT_BOUNCE, i / 100.0)
        assert 0.0 <= v <= 1.0


@pytest.mark.parametrize("name", ADVANCED_PRIMITIVES)
def test_advanced_primitive_resolves_deterministically(name):
    preset = MotionPreset(
        primitive=name, target="layer", start_frame=0, end_frame=30,
        easing=Easing.EASE_IN_OUT,
    )
    first = [k.to_dict() for k in resolve_primitive(preset)]
    second = [k.to_dict() for k in resolve_primitive(preset)]
    assert first == second
    assert first, f"{name} produced no keyframes"


@pytest.mark.parametrize("name", ADVANCED_PRIMITIVES)
def test_advanced_primitive_frames_monotonic_and_interpolable(name):
    preset = MotionPreset(
        primitive=name, target="layer", start_frame=0, end_frame=30,
        easing=Easing.EASE_IN_OUT,
    )
    keys = resolve_primitive(preset)
    for prop in {k.property for k in keys}:
        frames = [k.frame for k in keys if k.property == prop]
        assert frames == sorted(frames)
        assert len(frames) == len(set(frames))
        value = interpolate_keyframes(
            [k for k in keys if k.property == prop], prop, 15
        )
        assert value is not None


def test_shake_returns_to_rest():
    preset = MotionPreset(
        primitive="Shake", target="layer", start_frame=0, end_frame=40,
    )
    keys = resolve_primitive(preset)
    assert abs(keys[-1].value) < 0.02
