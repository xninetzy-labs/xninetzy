from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


VIDEO_SCHEMA_VERSION: str = "1"
VIDEO_RENDERER_VERSION: str = "ffmpeg-cpu/1+remotion-cpu/1"


VIDEO_STATE_CREATED: str = "created"
VIDEO_STATE_QUEUED: str = "queued"
VIDEO_STATE_RUNNING: str = "running"
VIDEO_STATE_VALIDATING: str = "validating"
VIDEO_STATE_COMPLETED: str = "completed"
VIDEO_STATE_FAILED: str = "failed"
VIDEO_STATE_CANCELLED: str = "cancelled"
VIDEO_STATE_CANCEL_REQUESTED: str = "cancel_requested"
VIDEO_STATE_EXPIRED: str = "expired"

VIDEO_STATE_TERMINAL_OK: frozenset[str] = frozenset({VIDEO_STATE_COMPLETED})
VIDEO_STATE_TERMINAL_FAIL: frozenset[str] = frozenset(
    {VIDEO_STATE_FAILED, VIDEO_STATE_CANCELLED, VIDEO_STATE_EXPIRED}
)


class CompositionPreset(StrEnum):
    YOUTUBE_LANDSCAPE = "youtube_landscape"
    SHORTS_VERTICAL = "shorts_vertical"
    INSTAGRAM_VERTICAL = "instagram_vertical"
    SQUARE_SOCIAL = "square_social"
    PRESENTATION = "presentation"
    CUSTOM = "custom"


class RendererId(StrEnum):
    FFMPEG_CPU = "ffmpeg-cpu"
    REMOTION_CPU = "remotion-cpu"
    REMOTION_LAMBDA = "remotion-lambda"
    UNKNOWN = "unknown"


class AssetKind(StrEnum):
    VIDEO = "video"
    IMAGE = "image"
    SVG = "svg"
    AUDIO = "audio"
    FONT = "font"
    LOGO = "logo"
    SCREENSHOT = "screenshot"
    CODE = "code"
    TEXT = "text"
    DATA = "data"


class TrackKind(StrEnum):
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    SHAPE = "shape"
    AUDIO = "audio"
    OVERLAY = "overlay"
    CAPTION = "caption"
    CODE = "code"
    UI = "ui"


class Easing(StrEnum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    CUBIC_BEZIER = "cubic_bezier"
    SPRING_DETERMINISTIC = "spring_deterministic"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_OUT_BOUNCE = "ease_out_bounce"
    EASE_OUT_EXPO = "ease_out_expo"
    EASE_OUT_CIRC = "ease_out_circ"
    ANTICIPATE = "anticipate"


class RendererSelectionReason(StrEnum):
    CAPABILITY_REQUIRES_REMOTION = "capability_requires_remotion"
    CAPABILITY_REQUIRES_FFMPEG = "capability_requires_ffmpeg"
    DEFAULT_LOCAL_CPU_FFMPEG = "default_local_cpu_ffmpeg"
    HEALTH_AWARE = "health_aware"
    NO_RENDERER_AVAILABLE = "no_renderer_available"
    USER_OVERRIDE = "user_override"


@dataclass(frozen=True, slots=True)
class Resolution:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"invalid resolution: {self.width}x{self.height}")
        if self.width > 7680 or self.height > 4320:
            raise ValueError(
                f"resolution exceeds 8K safe envelope: {self.width}x{self.height}"
            )

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    def to_dict(self) -> dict[str, int]:
        return {"width": self.width, "height": self.height}


_PRESET_RESOLUTIONS: dict[CompositionPreset, tuple[int, int]] = {
    CompositionPreset.YOUTUBE_LANDSCAPE: (1920, 1080),
    CompositionPreset.SHORTS_VERTICAL: (1080, 1920),
    CompositionPreset.INSTAGRAM_VERTICAL: (1080, 1920),
    CompositionPreset.SQUARE_SOCIAL: (1080, 1080),
    CompositionPreset.PRESENTATION: (1920, 1080),
}


def resolution_for_preset(preset: CompositionPreset) -> Resolution:
    width, height = _PRESET_RESOLUTIONS.get(preset, (1280, 720))
    return Resolution(width, height)


@dataclass(frozen=True, slots=True)
class FrameTime:
    frame: int

    def __post_init__(self) -> None:
        if self.frame < 0:
            raise ValueError(f"frame must be >= 0, got {self.frame}")

    def to_seconds(self, fps: int) -> float:
        if fps <= 0:
            raise ValueError(f"fps must be > 0, got {fps}")
        return self.frame / fps


def easing_value(easing: Easing | str, t: float, *args: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    name = easing.value if isinstance(easing, Easing) else str(easing)
    if name == "linear":
        return t
    if name == "ease_in":
        return t * t * t
    if name == "ease_out":
        return 1.0 - (1.0 - t) ** 3
    if name == "ease_in_out":
        return 4.0 * t * t * t if t < 0.5 else 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0
    if name == "cubic_bezier":
        if len(args) != 4:
            raise ValueError(
                "cubic_bezier requires (x1, y1, x2, y2) extra args"
            )
        x1, y1, x2, y2 = args
        s = t
        for _ in range(8):
            xs = _cb(s, x1, x2)
            dx = xs - t
            if abs(dx) < 1e-6:
                break
            dxs = _cb_deriv(s, x1, x2)
            if dxs == 0:
                break
            s -= dx / dxs
            s = max(0.0, min(1.0, s))
        return _cb(s, y1, y2)
    if name == "spring_deterministic":
        decay = math.exp(-0.6 * 6.0 * t)
        osc = math.cos(8.0 * t)
        return 1.0 - decay * osc
    if name == "ease_in_back":
        c1 = 1.70158
        c3 = c1 + 1.0
        return c3 * t * t * t - c1 * t * t
    if name == "anticipate":
        s = 2.0
        return t * t * ((s + 1.0) * t - s)
    if name == "ease_out_back":
        c1 = 1.70158
        c3 = c1 + 1.0
        u = t - 1.0
        return 1.0 + c3 * u * u * u + c1 * u * u
    if name == "ease_in_out_back":
        c2 = 1.70158 * 1.525
        if t < 0.5:
            return (pow(2.0 * t, 2) * ((c2 + 1.0) * 2.0 * t - c2)) / 2.0
        return (pow(2.0 * t - 2.0, 2) * ((c2 + 1.0) * (2.0 * t - 2.0) + c2) + 2.0) / 2.0
    if name == "ease_out_elastic":
        c4 = (2.0 * math.pi) / 3.0
        return pow(2.0, -10.0 * t) * math.sin((10.0 * t - 0.75) * c4) + 1.0
    if name == "ease_out_bounce":
        n1 = 7.5625
        d1 = 2.75
        u = t
        if u < 1.0 / d1:
            return n1 * u * u
        if u < 2.0 / d1:
            u -= 1.5 / d1
            return n1 * u * u + 0.75
        if u < 2.5 / d1:
            u -= 2.25 / d1
            return n1 * u * u + 0.9375
        u -= 2.625 / d1
        return n1 * u * u + 0.984375
    if name == "ease_out_expo":
        return 1.0 - pow(2.0, -10.0 * t)
    if name == "ease_out_circ":
        return math.sqrt(1.0 - (t - 1.0) * (t - 1.0))
    raise ValueError(f"unknown easing: {name}")


def _cb(s: float, a: float, b: float) -> float:
    u = 1.0 - s
    return 3 * u * u * s * a + 3 * u * s * s * b + s * s * s


def _cb_deriv(s: float, a: float, b: float) -> float:
    u = 1.0 - s
    return 3 * u * u * a - 6 * u * s * a + 6 * u * s * b - 3 * s * s * b + 3 * s * s


@dataclass(frozen=True, slots=True)
class Keyframe:
    property: str
    frame: int
    value: float
    easing: Easing = Easing.LINEAR

    def __post_init__(self) -> None:
        if self.frame < 0:
            raise ValueError(f"keyframe frame must be >= 0, got {self.frame}")
        if math.isnan(self.value) or math.isinf(self.value):
            raise ValueError(f"keyframe value must be finite, got {self.value}")
        if not self.property:
            raise ValueError("keyframe property must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "property": self.property,
            "frame": self.frame,
            "value": self.value,
            "easing": self.easing.value if isinstance(self.easing, Easing) else self.easing,
        }


def interpolate_keyframes(
    keyframes: list[Keyframe], property_name: str, frame: int
) -> float | None:
    relevant = [k for k in keyframes if k.property == property_name]
    if not relevant:
        return None
    if len(relevant) == 1:
        return relevant[0].value
    for i in range(1, len(relevant)):
        if relevant[i].frame <= relevant[i - 1].frame:
            raise ValueError(
                "keyframes for property must be monotonic in frame"
            )
    if frame <= relevant[0].frame:
        return relevant[0].value
    if frame >= relevant[-1].frame:
        return relevant[-1].value
    for i in range(1, len(relevant)):
        if relevant[i].frame > frame:
            lo = relevant[i - 1]
            hi = relevant[i]
            span = hi.frame - lo.frame
            t = (frame - lo.frame) / span if span > 0 else 0.0
            eased = easing_value(lo.easing, t)
            return lo.value + (hi.value - lo.value) * eased
    return relevant[-1].value


CANONICAL_PRIMITIVES: frozenset[str] = frozenset(
    {
        "FadeIn", "FadeOut", "SlideIn", "SlideOut",
        "ScaleIn", "ScaleOut", "Zoom", "Pan", "Reveal",
        "Typewriter", "BlurIn", "BlurOut", "Pop",
        "Spring", "Stagger", "Highlight", "Spotlight",
        "CameraPush", "CameraPull", "KenBurns",
        "LowerThird", "TitleCard", "Callout", "CodeHighlight",
        "BrowserFrame", "DeviceFrame",
        "Bounce", "Elastic", "Rotate", "Flip3D", "Swing",
        "Wiggle", "Shake", "Orbit", "Parallax", "PathMove",
        "MotionBlurStreak", "GlowPulse", "PulseScale",
    }
)


@dataclass(frozen=True, slots=True)
class MotionPreset:
    primitive: str
    target: str
    start_frame: int
    end_frame: int
    easing: Easing = Easing.EASE_IN_OUT
    parameters: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.primitive not in CANONICAL_PRIMITIVES:
            raise ValueError(
                f"unknown motion primitive '{self.primitive}'; "
                "must be one of the canonical set"
            )
        if not self.target:
            raise ValueError("motion preset target must not be empty")
        if self.end_frame <= self.start_frame:
            raise ValueError("motion preset end_frame must be > start_frame")

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive": self.primitive,
            "target": self.target,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "easing": self.easing.value if isinstance(self.easing, Easing) else self.easing,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class VideoAsset:
    asset_id: str
    kind: AssetKind
    source_path: str
    mime_type: str
    content_hash: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    fps: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.asset_id:
            raise ValueError("asset_id must not be empty")
        if not self.source_path:
            raise ValueError("asset source_path must not be empty")
        if not self.mime_type:
            raise ValueError("asset mime_type must not be empty")
        if not self.content_hash:
            raise ValueError("asset content_hash must not be empty")
        if self.kind is AssetKind.VIDEO and self.duration_seconds is None:
            raise ValueError("video asset must declare duration_seconds")
        if self.kind is AssetKind.VIDEO and self.fps is None:
            raise ValueError("video asset must declare fps")

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "kind": self.kind.value,
            "source_path": self.source_path,
            "mime_type": self.mime_type,
            "content_hash": self.content_hash,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VideoComposition:
    composition_id: str
    name: str
    resolution: Resolution
    fps: int
    duration_frames: int
    background_color: str = "#000000"
    preset: CompositionPreset = CompositionPreset.YOUTUBE_LANDSCAPE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.fps <= 0:
            raise ValueError(f"fps must be > 0, got {self.fps}")
        if self.duration_frames <= 0:
            raise ValueError(
                f"duration_frames must be > 0, got {self.duration_frames}"
            )
        if self.duration_frames / self.fps > 600.0:
            raise ValueError(
                "duration exceeds VideoQualityValidator envelope (600s)"
            )

    def duration_seconds(self) -> float:
        return self.duration_frames / self.fps

    def to_dict(self) -> dict[str, Any]:
        return {
            "composition_id": self.composition_id,
            "name": self.name,
            "resolution": self.resolution.to_dict(),
            "fps": self.fps,
            "duration_frames": self.duration_frames,
            "duration_seconds": self.duration_seconds(),
            "background_color": self.background_color,
            "preset": self.preset.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VideoClip:
    clip_id: str
    track_id: str
    asset_id: str | None = None
    source_start_frame: int = 0
    source_end_frame: int | None = None
    timeline_start_frame: int = 0
    timeline_end_frame: int | None = None
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0
    opacity: float = 1.0
    rotation: float = 0.0
    scale: float = 1.0
    border_radius: float = 0.0
    blend_mode: str = "normal"
    keyframes: list[Keyframe] = field(default_factory=list)
    text_overlay: str | None = None
    source_path: str | None = None

    def __post_init__(self) -> None:
        if not self.clip_id:
            raise ValueError("clip_id must not be empty")
        if not self.track_id:
            raise ValueError("track_id must not be empty")
        if self.asset_id is None and self.source_path is None:
            raise ValueError(
                "clip must reference either an asset_id or a source_path"
            )
        if self.asset_id is not None and self.source_path is not None:
            raise ValueError(
                "clip references both an asset_id and a source_path; pick one"
            )
        if self.opacity < 0.0 or self.opacity > 1.0:
            raise ValueError(f"opacity must be in [0, 1], got {self.opacity}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("clip width/height must be > 0")
        if any(k.frame < 0 for k in self.keyframes):
            raise ValueError("clip keyframes must have non-negative frame")

    def duration_frames(self) -> int | None:
        if self.source_end_frame is None or self.timeline_end_frame is None:
            return None
        return self.timeline_end_frame - self.timeline_start_frame

    def to_dict(self) -> dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "asset_id": self.asset_id,
            "track_id": self.track_id,
            "source_start_frame": self.source_start_frame,
            "source_end_frame": self.source_end_frame,
            "timeline_start_frame": self.timeline_start_frame,
            "timeline_end_frame": self.timeline_end_frame,
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "opacity": self.opacity, "rotation": self.rotation,
            "scale": self.scale, "border_radius": self.border_radius,
            "blend_mode": self.blend_mode,
            "keyframes": [k.to_dict() for k in self.keyframes],
            "text_overlay": self.text_overlay,
            "source_path": self.source_path,
        }


@dataclass(frozen=True, slots=True)
class VideoTrack:
    track_id: str
    composition_id: str
    kind: TrackKind
    name: str
    z_index: int = 0
    clips: list[VideoClip] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.track_id:
            raise ValueError("track_id must not be empty")
        if not self.composition_id:
            raise ValueError("track_id composition_id must not be empty")

    def add_clip(self, clip: VideoClip) -> "VideoTrack":
        if clip.track_id != self.track_id:
            raise ValueError(
                f"clip.track_id {clip.track_id!r} does not match track.track_id {self.track_id!r}"
            )
        return VideoTrack(
            track_id=self.track_id,
            composition_id=self.composition_id,
            kind=self.kind,
            name=self.name,
            z_index=self.z_index,
            clips=self.clips + [clip],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "composition_id": self.composition_id,
            "kind": self.kind.value,
            "name": self.name,
            "z_index": self.z_index,
            "clips": [c.to_dict() for c in self.clips],
        }


@dataclass(frozen=True, slots=True)
class VideoTransition:
    transition_id: str
    kind: str
    duration_frames: int

    def __post_init__(self) -> None:
        if self.kind not in {"crossfade", "dip_to_black", "fade_white", "wipe"}:
            raise ValueError(f"unsupported transition kind: {self.kind}")
        if self.duration_frames <= 0:
            raise ValueError("transition duration_frames must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "kind": self.kind,
            "duration_frames": self.duration_frames,
        }


@dataclass(frozen=True, slots=True)
class VideoScene:
    scene_id: str
    composition_id: str
    name: str
    purpose: str = "intro"
    start_frame: int = 0
    duration_frames: int = 0
    tracks: list[VideoTrack] = field(default_factory=list)
    motion_presets: list[MotionPreset] = field(default_factory=list)
    transition_in: VideoTransition | None = None
    transition_out: VideoTransition | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    __SCENE_PURPOSES__: frozenset[str] = frozenset(
        {"intro", "problem", "architecture", "implementation", "demo",
         "result", "outro", "hook", "context", "step", "summary",
         "transition", "feature", "interaction", "cta"}
    )

    def __post_init__(self) -> None:
        if not self.scene_id:
            raise ValueError("scene_id must not be empty")
        if not self.composition_id:
            raise ValueError("scene_id must reference a composition")
        if self.duration_frames < 0:
            raise ValueError("duration_frames must be >= 0")

    def end_frame(self) -> int:
        return self.start_frame + self.duration_frames

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "composition_id": self.composition_id,
            "name": self.name,
            "purpose": self.purpose,
            "start_frame": self.start_frame,
            "duration_frames": self.duration_frames,
            "tracks": [t.to_dict() for t in self.tracks],
            "motion_presets": [m.to_dict() for m in self.motion_presets],
            "transition_in": self.transition_in.to_dict() if self.transition_in else None,
            "transition_out": self.transition_out.to_dict() if self.transition_out else None,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VideoProject:
    project_id: str
    name: str
    source_project_root: str | None
    schema_version: str
    compositions: list[VideoComposition]
    scenes: list[VideoScene]
    assets: list[VideoAsset]
    created_at: str
    updated_at: str
    version: int
    renderer_versions: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id must not be empty")
        if self.version < 1:
            raise ValueError(f"project version must be >= 1, got {self.version}")
        if not self.compositions:
            raise ValueError("VideoProject must have at least one composition")
        composition_ids = {c.composition_id for c in self.compositions}
        for s in self.scenes:
            if s.composition_id not in composition_ids:
                raise ValueError(
                    f"scene {s.scene_id} references unknown composition_id "
                    f"{s.composition_id!r}"
                )
        for t in (t for s in self.scenes for t in s.tracks):
            if t.composition_id not in composition_ids:
                raise ValueError(
                    f"track {t.track_id} references unknown composition_id"
                )

    def primary_composition(self) -> VideoComposition:
        return self.compositions[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "renderer_versions": dict(self.renderer_versions),
            "project_id": self.project_id,
            "name": self.name,
            "source_project_root": self.source_project_root,
            "compositions": [c.to_dict() for c in self.compositions],
            "scenes": [s.to_dict() for s in self.scenes],
            "assets": [a.to_dict() for a in self.assets],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, default=str)


@dataclass(frozen=True, slots=True)
class RenderRequest:
    project_id: str
    composition_id: str
    project_version: int
    output_format: str
    output_path: str
    props_path: str
    quality: str = "balanced"
    concurrency: int = 1
    width: int = 0
    height: int = 0
    fps: int = 0
    duration_frames: int = 0
    max_runtime_seconds: int = 1800
    preview: bool = False

    def __post_init__(self) -> None:
        if self.output_format not in {"mp4", "webm"}:
            raise ValueError(f"unsupported output_format: {self.output_format}")
        if self.max_runtime_seconds <= 0:
            raise ValueError("max_runtime_seconds must be > 0")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")


@dataclass(frozen=True, slots=True)
class RenderResult:
    render_id: str
    status: str
    renderer: RendererId
    renderer_version: str
    remotion_version: str
    output_path: str
    duration_seconds: float
    width: int
    height: int
    fps: int
    codec: str
    size_bytes: int
    artifact_id: str | None
    exit_code: int
    stderr_summary: str
    stdout_summary: str
    selection_reason: RendererSelectionReason


VideoGenerationRequest = VideoProject
VideoResult = RenderResult


@dataclass(frozen=True, slots=True)
class VideoReference:
    project_id: str
    asset_id: str
    role: str

    def to_dict(self) -> dict[str, Any]:
        return {"project_id": self.project_id, "asset_id": self.asset_id, "role": self.role}


class VideoAspectRatio(StrEnum):
    R_16_9 = "16:9"
    R_9_16 = "9:16"
    R_1_1 = "1:1"
    R_4_3 = "4:3"
    R_21_9 = "21:9"


@dataclass(frozen=True, slots=True)
class VideoArtifact:
    artifact_id: str
    render_id: str
    project_id: str
    path: str
    mime_type: str
    content_hash: str
    size_bytes: int
    duration_seconds: float
    width: int
    height: int
    fps: int
    codec: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "render_id": self.render_id,
            "project_id": self.project_id,
            "path": self.path,
            "mime_type": self.mime_type,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "codec": self.codec,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class VideoJob:
    render_id: str
    project_id: str
    project_version: int
    composition_id: str
    renderer: RendererId
    status: str
    output_format: str
    output_path: str
    props_path: str
    width: int
    height: int
    fps: int
    duration_frames: int
    quality: str
    concurrency: int
    max_runtime_seconds: int
    preview: bool
    selection_reason: RendererSelectionReason
    remotion_version: str = ""
    ffmpeg_version: str = ""
    created_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    size_bytes: int | None = None
    artifact_id: str | None = None
    error_code: str | None = None
    stderr_summary: str = ""
    stdout_summary: str = ""

    def is_terminal(self) -> bool:
        return self.status in (
            VIDEO_STATE_COMPLETED,
            VIDEO_STATE_FAILED,
            VIDEO_STATE_CANCELLED,
            VIDEO_STATE_EXPIRED,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "render_id": self.render_id,
            "project_id": self.project_id,
            "project_version": self.project_version,
            "composition_id": self.composition_id,
            "renderer": self.renderer.value,
            "status": self.status,
            "output_format": self.output_format,
            "output_path": self.output_path,
            "props_path": self.props_path,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration_frames": self.duration_frames,
            "quality": self.quality,
            "concurrency": self.concurrency,
            "max_runtime_seconds": self.max_runtime_seconds,
            "preview": self.preview,
            "selection_reason": self.selection_reason.value,
            "remotion_version": self.remotion_version,
            "ffmpeg_version": self.ffmpeg_version,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "size_bytes": self.size_bytes,
            "artifact_id": self.artifact_id,
            "error_code": self.error_code,
            "stderr_summary": self.stderr_summary,
            "stdout_summary": self.stdout_summary,
        }


VideoJobRecord = VideoJob

__all__ = [
    "VIDEO_SCHEMA_VERSION",
    "VIDEO_RENDERER_VERSION",
    "VIDEO_STATE_CREATED",
    "VIDEO_STATE_QUEUED",
    "VIDEO_STATE_RUNNING",
    "VIDEO_STATE_VALIDATING",
    "VIDEO_STATE_COMPLETED",
    "VIDEO_STATE_FAILED",
    "VIDEO_STATE_CANCELLED",
    "VIDEO_STATE_CANCEL_REQUESTED",
    "VIDEO_STATE_EXPIRED",
    "VIDEO_STATE_TERMINAL_OK",
    "VIDEO_STATE_TERMINAL_FAIL",
    "CompositionPreset",
    "RendererId",
    "AssetKind",
    "TrackKind",
    "Easing",
    "RendererSelectionReason",
    "Resolution",
    "FrameTime",
    "easing_value",
    "Keyframe",
    "interpolate_keyframes",
    "MotionPreset",
    "CANONICAL_PRIMITIVES",
    "VideoAsset",
    "VideoComposition",
    "VideoClip",
    "VideoTrack",
    "VideoTransition",
    "VideoScene",
    "VideoProject",
    "RenderRequest",
    "RenderResult",
    "VideoGenerationRequest",
    "VideoResult",
    "VideoReference",
    "VideoAspectRatio",
    "VideoArtifact",
    "VideoJob",
    "VideoJobRecord",
]
