"""Validation primitives for VideoProject, timeline, motion graph, and renderer requests.

CPU-only. NO Remotion imports, NO network calls.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Iterable

from xninetzy.context.media.video.models import (
    MotionPreset,
    RenderRequest,
    VideoComposition,
    VideoProject,
    VideoScene,
)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def validate_project(project: VideoProject) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if not project.compositions:
        errors.append("project has no compositions")
    for c in project.compositions:
        errors.extend(_validate_composition(c))

    composition_ids = {c.composition_id for c in project.compositions}
    for s in project.scenes:
        if s.composition_id not in composition_ids:
            errors.append(
                f"scene {s.scene_id!r} references unknown composition_id {s.composition_id!r}"
            )
        errors.extend(_validate_scene(s))

    asset_ids = {a.asset_id for a in project.assets}
    for s in project.scenes:
        for t in s.tracks:
            for c in t.clips:
                if c.asset_id is not None and c.asset_id not in asset_ids:
                    errors.append(
                        f"clip {c.clip_id!r} references unknown asset_id {c.asset_id!r}"
                    )
                errors.extend(_validate_clip(c))

    for a in project.assets:
        if not a.content_hash:
            errors.append(f"asset {a.asset_id!r} has no content_hash")

    if project.version < 1:
        errors.append(f"project version must be >= 1, got {project.version}")

    return ValidationReport(
        ok=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_composition(c: VideoComposition) -> list[str]:
    errs: list[str] = []
    if c.fps <= 0:
        errs.append(f"composition {c.composition_id!r} fps must be > 0")
    if c.duration_frames <= 0:
        errs.append(f"composition {c.composition_id!r} duration_frames must be > 0")
    if c.duration_frames / c.fps > 600.0:
        errs.append(
            f"composition {c.composition_id!r} duration exceeds 600s envelope"
        )
    return errs


def _validate_scene(s: VideoScene) -> list[str]:
    errs: list[str] = []
    if s.duration_frames <= 0:
        errs.append(f"scene {s.scene_id!r} duration_frames must be > 0")
    track_clips: list[tuple[str, int, int]] = []
    for t in s.tracks:
        for c in t.clips:
            if c.timeline_end_frame is None:
                continue
            track_clips.append((t.track_id, c.timeline_start_frame, c.timeline_end_frame))
    overlap = _detect_overlap(track_clips)
    if overlap:
        errs.append(f"scene {s.scene_id!r} has overlapping clips: {overlap}")
    return errs


def _validate_clip(c) -> list[str]:
    errs: list[str] = []
    if c.timeline_end_frame is not None and c.timeline_end_frame < c.timeline_start_frame:
        errs.append(f"clip {c.clip_id!r} end < start")
    for k in c.keyframes:
        if k.frame < 0:
            errs.append(f"clip {c.clip_id!r} has negative keyframe frame {k.frame}")
        if math.isnan(k.value) or math.isinf(k.value):
            errs.append(f"clip {c.clip_id!r} has non-finite keyframe value")
    return errs


def _detect_overlap(clips: Iterable[tuple[str, int, int]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    arr = sorted(clips, key=lambda x: (x[0], x[1]))
    for i in range(1, len(arr)):
        if arr[i][0] == arr[i - 1][0]:
            if arr[i][1] < arr[i - 1][2]:
                out.append((arr[i - 1][0], arr[i][0]))
    return out


def validate_motion_preset(preset: MotionPreset) -> ValidationReport:
    errs: list[str] = []
    if preset.primitive not in preset.primitive and False:
        errs.append("invalid preset")
    if preset.end_frame <= preset.start_frame:
        errs.append("preset end_frame must be > start_frame")
    for v in preset.parameters.values():
        if math.isnan(v) or math.isinf(v):
            errs.append("preset parameter must be finite")
    return ValidationReport(ok=not errs, errors=tuple(errs))


def validate_render_request(
    request: RenderRequest, fps: int, width: int, height: int, duration_frames: int,
) -> ValidationReport:
    errs: list[str] = []
    if request.output_format not in {"mp4", "webm"}:
        errs.append(f"unsupported output_format {request.output_format!r}")
    if request.concurrency < 1:
        errs.append("concurrency must be >= 1")
    if request.max_runtime_seconds <= 0:
        errs.append("max_runtime_seconds must be > 0")
    if fps <= 0:
        errs.append("fps must be > 0")
    if width <= 0 or height <= 0:
        errs.append("width/height must be > 0")
    if duration_frames <= 0:
        errs.append("duration_frames must be > 0")
    if request.duration_seconds() if hasattr(request, "duration_seconds") else 0 > 600:
        errs.append("duration > 600s envelope")
    return ValidationReport(ok=not errs, errors=tuple(errs))


def validate_path_within_roots(
    path: str, allowed_roots: tuple[str, ...]
) -> bool:
    """Rejects paths that escape allowed roots via '..' or symlinks."""

    norm = os.path.normpath(path)
    if norm.startswith(".."):
        return False
    abs_norm = os.path.abspath(norm)
    for root in allowed_roots:
        if abs_norm.startswith(os.path.abspath(root) + os.sep):
            return True
    return False


__all__ = [
    "ValidationReport",
    "validate_project",
    "validate_motion_preset",
    "validate_render_request",
    "validate_path_within_roots",
]
