from __future__ import annotations

import math

from xninetzy.context.media.video.models import (
    Easing,
    Keyframe,
    MotionPreset,
)


def resolve_primitive(preset: MotionPreset) -> list[Keyframe]:
    name = preset.primitive
    p = dict(preset.parameters)
    start = preset.start_frame
    end = preset.end_frame
    span = end - start
    if span <= 0:
        raise ValueError("invalid motion preset frame window")
    easing = preset.easing

    if name == "FadeIn":
        return [Keyframe(property="opacity", frame=start, value=0.0)] + _eased(
            "opacity", start, end, 0.0, 1.0, easing
        )

    if name == "FadeOut":
        return _eased("opacity", start, end, 1.0, 0.0, easing)

    if name == "SlideIn":
        direction = p.get("direction", "left")
        x_start = _slide_start(direction)
        return [
            Keyframe(property="x", frame=start, value=x_start),
            *_eased("x", start, end, x_start, 0.0, easing),
        ]

    if name == "SlideOut":
        direction = p.get("direction", "right")
        x_end = _slide_end(direction)
        return [
            Keyframe(property="x", frame=start, value=0.0),
            *_eased("x", start, end, 0.0, x_end, easing),
        ]

    if name == "ScaleIn":
        from_scale = p.get("from_scale", 0.8)
        return [Keyframe(property="scale", frame=start, value=from_scale)] + _eased(
            "scale", start, end, from_scale, 1.0, easing
        )

    if name == "ScaleOut":
        to_scale = p.get("to_scale", 1.2)
        return _eased("scale", start, end, 1.0, to_scale, easing)

    if name == "Zoom":
        return _eased("scale", start, end, 1.0, p.get("to_scale", 1.12), easing)

    if name == "Pan":
        return _eased("x", start, end, p.get("from_x", 0.0), p.get("to_x", 0.0), easing)

    if name == "Reveal":
        return _eased("clip_path", start, end, 0.0, p.get("to_clip", 1.0), easing)

    if name == "Typewriter":
        return [
            Keyframe(property="text_step", frame=start, value=0.0),
            Keyframe(
                property="text_step",
                frame=end,
                value=float(_step_count(p.get("text", " "))),
                easing=easing,
            )
        ]

    if name == "BlurIn":
        from_blur = p.get("from_blur", 12.0)
        return [Keyframe(property="blur", frame=start, value=from_blur)] + _eased(
            "blur", start, end, from_blur, 0.0, easing
        )

    if name == "BlurOut":
        return _eased("blur", start, end, 0.0, p.get("to_blur", 12.0), easing)

    if name == "Pop":
        return [
            Keyframe(property="scale", frame=start, value=p.get("from_scale", 0.85)),
            Keyframe(
                property="scale",
                frame=start + max(1, span // 3),
                value=p.get("to_scale", 1.05),
                easing=Easing.SPRING_DETERMINISTIC,
            ),
            Keyframe(property="scale", frame=end, value=1.0),
        ]

    if name == "Spring":
        return _eased(
            "scale",
            start,
            end,
            p.get("from_scale", 1.0),
            p.get("to_scale", 1.0),
            Easing.SPRING_DETERMINISTIC,
        )

    if name == "Stagger":
        return [Keyframe(property="stagger_phase", frame=start, value=0.0)] + _eased(
            "stagger_phase", start, end, 0.0, 1.0, easing
        )

    if name == "Highlight":
        return _eased(
            "color", start, end,
            p.get("from_color", 0.0), p.get("to_color", 1.0), easing,
        )

    if name == "Spotlight":
        return [
            Keyframe(property="spotlight_radius", frame=start, value=0.05),
            *_eased("spotlight_radius", start, end, 0.05, 0.6, easing),
        ]

    if name == "CameraPush":
        return [Keyframe(property="scale", frame=start, value=1.0)] + _eased(
            "scale", start, end, 1.0, p.get("to_scale", 1.06), easing
        )

    if name == "CameraPull":
        return _eased("scale", start, end, 1.0, p.get("to_scale", 0.96), easing)

    if name == "KenBurns":
        return [
            Keyframe(property="scale", frame=start, value=p.get("from_scale", 1.0)),
            *_eased(
                "scale", start, end, p.get("from_scale", 1.0),
                p.get("to_scale", 1.18), easing
            ),
            *_eased(
                "x", start, end, p.get("from_x", -0.05),
                p.get("to_x", 0.05), easing
            ),
        ]

    if name == "LowerThird":
        return [
            Keyframe(property="lowerthird_opacity", frame=start, value=0.0),
            *_eased("lowerthird_opacity", start, end, 0.0, 1.0, easing),
        ]

    if name == "TitleCard":
        return [
            Keyframe(property="titlecard_opacity", frame=start, value=0.0),
            *_eased("titlecard_opacity", start, end, 0.0, 1.0, easing),
        ]

    if name == "Callout":
        return [
            Keyframe(property="callout_scale", frame=start, value=0.85),
            *_eased(
                "callout_scale", start, end, 0.85, 1.05,
                Easing.SPRING_DETERMINISTIC
            ),
            Keyframe(property="callout_scale", frame=end, value=1.0),
        ]

    if name == "CodeHighlight":
        return [
            Keyframe(property="codehl_y", frame=start, value=p.get("from_y", 0.0)),
            *_eased(
                "codehl_y", start, end, p.get("from_y", 0.0),
                p.get("to_y", 0.0), easing
            ),
        ]

    if name == "BrowserFrame":
        return [Keyframe(property="browser_chrome", frame=start, value=1.0)]

    if name == "DeviceFrame":
        return [Keyframe(property="device_chrome", frame=start, value=1.0)]

    if name == "Bounce":
        return _eased(
            "y", start, end, p.get("from_y", -1.0), p.get("to_y", 0.0),
            Easing.EASE_OUT_BOUNCE, steps=8,
        )

    if name == "Elastic":
        return _eased(
            "scale", start, end, p.get("from_scale", 0.6), p.get("to_scale", 1.0),
            Easing.EASE_OUT_ELASTIC, steps=10,
        )

    if name == "Rotate":
        return _eased(
            "rotate", start, end, p.get("from_deg", 0.0), p.get("to_deg", 360.0), easing
        )

    if name == "Flip3D":
        return _eased(
            "rotate_y", start, end, p.get("from_deg", 0.0), p.get("to_deg", 180.0), easing
        )

    if name == "Swing":
        amplitude = p.get("amplitude_deg", 18.0)
        decay = p.get("decay", 3.0)
        freq = p.get("frequency", 1.5)
        return _sampled(
            "rotate", start, end,
            lambda t: amplitude * math.exp(-decay * t) * math.cos(2.0 * math.pi * freq * t),
            samples=int(p.get("samples", 16)),
        )

    if name == "Wiggle":
        amplitude = p.get("amplitude_deg", 8.0)
        cycles = p.get("cycles", 3.0)
        return _sampled(
            "rotate", start, end,
            lambda t: amplitude * math.sin(2.0 * math.pi * cycles * t),
            samples=int(p.get("samples", 16)),
        )

    if name == "Shake":
        amplitude = p.get("amplitude", 0.03)
        decay = p.get("decay", 4.0)
        freq = p.get("frequency", 6.0)
        return _sampled(
            "x", start, end,
            lambda t: amplitude * math.exp(-decay * t) * math.sin(2.0 * math.pi * freq * t),
            samples=int(p.get("samples", 20)),
        )

    if name == "Orbit":
        radius = p.get("radius", 0.1)
        phase = p.get("phase", 0.0)
        base_x = radius * math.cos(phase)
        base_y = radius * math.sin(phase)
        turns = p.get("turns", 1.0)
        samples = int(p.get("samples", 16))
        x_keys = _sampled(
            "x", start, end,
            lambda t: radius * math.cos(2.0 * math.pi * turns * t + phase) - base_x,
            samples=samples,
        )
        y_keys = _sampled(
            "y", start, end,
            lambda t: radius * math.sin(2.0 * math.pi * turns * t + phase) - base_y,
            samples=samples,
        )
        return x_keys + y_keys

    if name == "Parallax":
        depth = p.get("depth", 1.0)
        from_x = p.get("from_x", 0.0)
        to_x = p.get("to_x", -0.2) * depth
        return _eased("x", start, end, from_x, to_x, easing)

    if name == "PathMove":
        from_x = p.get("from_x", 0.0)
        from_y = p.get("from_y", 0.0)
        to_x = p.get("to_x", 0.0)
        to_y = p.get("to_y", 0.0)
        return [
            *_eased("x", start, end, from_x, to_x, easing),
            *_eased("y", start, end, from_y, to_y, easing),
        ]

    if name == "MotionBlurStreak":
        amount = p.get("amount", 1.0)
        mid = start + max(1, span // 2)
        return [
            Keyframe(property="motion_blur", frame=start, value=0.0),
            Keyframe(property="motion_blur", frame=mid, value=amount, easing=easing),
            Keyframe(property="motion_blur", frame=end, value=0.0, easing=easing),
        ]

    if name == "GlowPulse":
        count = p.get("count", 2.0)
        return _sampled(
            "glow", start, end,
            lambda t: 0.5 * (1.0 - math.cos(2.0 * math.pi * count * t)),
            samples=int(p.get("samples", 16)),
        )

    if name == "PulseScale":
        amplitude = p.get("amplitude", 0.08)
        count = p.get("count", 1.0)
        return _sampled(
            "scale", start, end,
            lambda t: 1.0 + amplitude * math.sin(math.pi * count * t),
            samples=int(p.get("samples", 14)),
        )

    raise NotImplementedError(f"primitive '{name}' not implemented")


def resolve_to_keyframes(preset: MotionPreset) -> list[Keyframe]:
    return resolve_primitive(preset)


def _eased(
    property: str, start: int, end: int,
    from_value: float, to_value: float, easing: Easing, steps: int = 4,
) -> list[Keyframe]:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    keys: list[Keyframe] = [
        Keyframe(property=property, frame=start, value=from_value, easing=easing)
    ]
    if steps > 1:
        span = end - start
        for i in range(1, steps):
            t = i / steps
            frame = start + round(span * t)
            eased_t = _ease_for(easing, t)
            value = from_value + (to_value - from_value) * eased_t
            keys.append(Keyframe(property=property, frame=frame, value=value))
    keys.append(Keyframe(property=property, frame=end, value=to_value))
    return keys


def _sampled(property, start, end, fn, samples=12):
    span = end - start
    if span <= 0:
        raise ValueError("invalid sampling window")
    count = max(2, min(int(samples), span + 1))
    keys: list[Keyframe] = []
    last_frame = -1
    for i in range(count):
        t = i / (count - 1)
        frame = start + round(span * t)
        if frame <= last_frame:
            frame = last_frame + 1
        if frame > end:
            break
        keys.append(Keyframe(property=property, frame=frame, value=float(fn(t))))
        last_frame = frame
    if not keys or keys[-1].frame != end:
        keys.append(Keyframe(property=property, frame=end, value=float(fn(1.0))))
    return keys


def _ease_for(easing: Easing, t: float) -> float:
    if easing is Easing.LINEAR:
        return t
    if easing is Easing.EASE_IN:
        return t * t
    if easing is Easing.EASE_OUT:
        return 1.0 - (1.0 - t) * (1.0 - t)
    if easing is Easing.EASE_IN_OUT:
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    if easing is Easing.SPRING_DETERMINISTIC:
        decay = math.exp(-0.6 * 6.0 * t)
        osc = math.cos(8.0 * t)
        return 1.0 - decay * osc
    from xninetzy.context.media.video.models import easing_value
    return easing_value(easing, t)


def _slide_start(direction: str) -> float:
    if direction in {"left", "top"}:
        return -1.0
    return 1.0


def _slide_end(direction: str) -> float:
    if direction in {"right", "bottom"}:
        return 1.0
    return -1.0


def _step_count(text: str) -> int:
    return max(1, len(text or " "))


__all__ = ["resolve_primitive", "resolve_to_keyframes"]
