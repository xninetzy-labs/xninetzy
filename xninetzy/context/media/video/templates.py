"""Deterministic video templates.

Templates are FUNCTIONS, not generative-AI prompts. They take a
``TemplateContext`` and return a populated :class:`VideoProject`.

Every template uses the canonical motion primitives from
``xninetzy.context.media.video.motion``. No new primitives are
invented here.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Mapping

from xninetzy.context.media.video.models import (
    CompositionPreset,
    Easing,
    MotionPreset,
    Resolution,
    resolution_for_preset,
    VideoAsset,
    VideoComposition,
    VideoProject,
    VideoScene,
)


@dataclass(frozen=True, slots=True)
class TemplateContext:
    project_id: str
    name: str
    fps: int = 30
    preset: CompositionPreset = CompositionPreset.YOUTUBE_LANDSCAPE
    source_project_root: str | None = None
    duration_seconds: float = 30.0
    assets: tuple[VideoAsset, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _composition(ctx: TemplateContext, composition_id: str = "main") -> VideoComposition:
    return VideoComposition(
        composition_id=composition_id,
        name=ctx.name,
        resolution=_resolution_from_preset(ctx.preset),
        fps=ctx.fps,
        duration_frames=int(ctx.duration_seconds * ctx.fps),
        preset=ctx.preset,
        metadata=dict(ctx.metadata),
    )


_TEMPLATE_COMPOSITION_ID = {
    "project_demo": "ProjectDemo",
    "tutorial": "Tutorial",
    "development_journey": "DevelopmentVideo",
    "motion_graph": "MotionGraphic",
}


def _resolution_from_preset(preset: CompositionPreset) -> Resolution:
    return resolution_for_preset(preset)


def project_demo_template(ctx: TemplateContext) -> VideoProject:
    """Intro -> Architecture -> Live Demo -> Result -> Outro.

    Each slot has a deterministic duration derived from the total
    duration_seconds. Motion is applied via canonical primitives.
    """

    composition = _composition(ctx, _TEMPLATE_COMPOSITION_ID["project_demo"])
    total = composition.duration_frames
    intro = total // 10
    arch = total // 5
    demo = total // 2
    result = total // 10
    outro = total - (intro + arch + demo + result)

    scenes: list[VideoScene] = []

    intro_scene = VideoScene(
        scene_id="intro",
        composition_id=composition.composition_id,
        name="Intro",
        purpose="intro",
        start_frame=0,
        duration_frames=intro,
        motion_presets=[
            MotionPreset(
                primitive="FadeIn",
                target="title",
                start_frame=0,
                end_frame=intro,
                easing=Easing.EASE_IN_OUT,
            ),
        ],
    )
    scenes.append(intro_scene)

    arch_scene = VideoScene(
        scene_id="arch",
        composition_id=composition.composition_id,
        name="Architecture",
        purpose="architecture",
        start_frame=intro,
        duration_frames=arch,
        motion_presets=[
            MotionPreset(
                primitive="CameraPush",
                target="screenshot",
                start_frame=intro,
                end_frame=intro + arch,
                easing=Easing.EASE_IN_OUT,
                parameters={"to_scale": 1.08},
            ),
        ],
    )
    scenes.append(arch_scene)

    demo_scene = VideoScene(
        scene_id="demo",
        composition_id=composition.composition_id,
        name="Live demo",
        purpose="demo",
        start_frame=intro + arch,
        duration_frames=demo,
        motion_presets=[
            MotionPreset(
                primitive="Pan",
                target="screen",
                start_frame=intro + arch,
                end_frame=intro + arch + demo,
                easing=Easing.EASE_IN_OUT,
                parameters={"from_x": 0.0, "to_x": 0.04},
            ),
        ],
    )
    scenes.append(demo_scene)

    result_scene = VideoScene(
        scene_id="result",
        composition_id=composition.composition_id,
        name="Result",
        purpose="result",
        start_frame=intro + arch + demo,
        duration_frames=result,
        motion_presets=[
            MotionPreset(
                primitive="Reveal",
                target="result",
                start_frame=intro + arch + demo,
                end_frame=intro + arch + demo + result,
                easing=Easing.EASE_OUT,
                parameters={"to_clip": 1.0},
            ),
        ],
    )
    scenes.append(result_scene)

    outro_scene = VideoScene(
        scene_id="outro",
        composition_id=composition.composition_id,
        name="Outro",
        purpose="outro",
        start_frame=intro + arch + demo + result,
        duration_frames=outro,
        motion_presets=[
            MotionPreset(
                primitive="FadeOut",
                target="endcard",
                start_frame=intro + arch + demo + result,
                end_frame=total,
                easing=Easing.EASE_IN_OUT,
            ),
        ],
    )
    scenes.append(outro_scene)

    return VideoProject(
        project_id=ctx.project_id,
        name=ctx.name,
        source_project_root=ctx.source_project_root,
        schema_version="1",
        compositions=[composition],
        scenes=scenes,
        assets=list(ctx.assets),
        created_at=_now_iso(),
        updated_at=_now_iso(),
        version=1,
        metadata=dict(ctx.metadata),
    )


def tutorial_template(ctx: TemplateContext) -> VideoProject:
    composition = _composition(ctx, _TEMPLATE_COMPOSITION_ID["tutorial"])
    total = composition.duration_frames
    hook = total // 10
    context_f = total // 5
    step = (total - hook - context_f - (total // 10)) // 3
    summary = total // 10
    scenes: list[VideoScene] = []

    scenes.append(VideoScene(
        scene_id="hook",
        composition_id=composition.composition_id,
        name="Hook",
        purpose="hook",
        start_frame=0,
        duration_frames=hook,
        motion_presets=[MotionPreset(
            primitive="TitleCard", target="title",
            start_frame=0, end_frame=hook, easing=Easing.EASE_IN_OUT,
        )],
    ))
    cursor = hook
    scenes.append(VideoScene(
        scene_id="context",
        composition_id=composition.composition_id,
        name="Context",
        purpose="context",
        start_frame=cursor,
        duration_frames=context_f,
        motion_presets=[MotionPreset(
            primitive="FadeIn", target="context",
            start_frame=cursor, end_frame=cursor + context_f,
            easing=Easing.EASE_IN_OUT,
        )],
    ))
    cursor += context_f
    for i in range(3):
        scenes.append(VideoScene(
            scene_id=f"step_{i + 1}",
            composition_id=composition.composition_id,
            name=f"Step {i + 1}",
            purpose="step",
            start_frame=cursor,
            duration_frames=step,
            motion_presets=[MotionPreset(
                primitive="CameraPush", target="screenshot",
                start_frame=cursor, end_frame=cursor + step,
                easing=Easing.EASE_IN_OUT,
                parameters={"to_scale": 1.05},
            )],
        ))
        cursor += step
    scenes.append(VideoScene(
        scene_id="summary",
        composition_id=composition.composition_id,
        name="Summary",
        purpose="summary",
        start_frame=cursor,
        duration_frames=summary,
        motion_presets=[MotionPreset(
            primitive="FadeOut", target="endcard",
            start_frame=cursor, end_frame=total,
            easing=Easing.EASE_IN_OUT,
        )],
    ))

    return VideoProject(
        project_id=ctx.project_id,
        name=ctx.name,
        source_project_root=ctx.source_project_root,
        schema_version="1",
        compositions=[composition],
        scenes=scenes,
        assets=list(ctx.assets),
        created_at=_now_iso(),
        updated_at=_now_iso(),
        version=1,
        metadata=dict(ctx.metadata),
    )


def development_journey_template(ctx: TemplateContext) -> VideoProject:
    composition = _composition(ctx, _TEMPLATE_COMPOSITION_ID["development_journey"])
    total = composition.duration_frames
    slot = total // 6
    scenes: list[VideoScene] = []
    purposes = ["problem", "implementation", "failure", "debugging", "resolution", "demo"]
    for i, purpose in enumerate(purposes):
        scenes.append(VideoScene(
            scene_id=purpose,
            composition_id=composition.composition_id,
            name=purpose.capitalize(),
            purpose=purpose,
            start_frame=i * slot,
            duration_frames=slot,
            motion_presets=[
                MotionPreset(
                    primitive="FadeIn",
                    target="event_marker",
                    start_frame=i * slot,
                    end_frame=(i + 1) * slot,
                    easing=Easing.EASE_IN_OUT,
                ),
            ],
        ))

    return VideoProject(
        project_id=ctx.project_id,
        name=ctx.name,
        source_project_root=ctx.source_project_root,
        schema_version="1",
        compositions=[composition],
        scenes=scenes,
        assets=list(ctx.assets),
        created_at=_now_iso(),
        updated_at=_now_iso(),
        version=1,
        metadata=dict(ctx.metadata),
    )


def motion_graph_template(ctx: TemplateContext) -> VideoProject:
    composition = _composition(ctx, _TEMPLATE_COMPOSITION_ID["motion_graph"])
    total = composition.duration_frames
    scene = VideoScene(
        scene_id="motion_graph",
        composition_id=composition.composition_id,
        name="Motion Graphic",
        purpose="feature",
        start_frame=0,
        duration_frames=total,
        motion_presets=[
            MotionPreset(
                primitive="TitleCard",
                target="headline",
                start_frame=0,
                end_frame=total // 4,
                easing=Easing.EASE_IN_OUT,
            ),
            MotionPreset(
                primitive="CameraPush",
                target="headline",
                start_frame=total // 4,
                end_frame=total // 2,
                easing=Easing.EASE_IN_OUT,
                parameters={"to_scale": 1.08},
            ),
            MotionPreset(
                primitive="FadeOut",
                target="endcard",
                start_frame=total // 2,
                end_frame=total,
                easing=Easing.EASE_IN_OUT,
            ),
        ],
    )

    return VideoProject(
        project_id=ctx.project_id,
        name=ctx.name,
        source_project_root=ctx.source_project_root,
        schema_version="1",
        compositions=[composition],
        scenes=[scene],
        assets=list(ctx.assets),
        created_at=_now_iso(),
        updated_at=_now_iso(),
        version=1,
        metadata=dict(ctx.metadata),
    )


__all__ = [
    "TemplateContext",
    "project_demo_template",
    "tutorial_template",
    "development_journey_template",
    "motion_graph_template",
]
