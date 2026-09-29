from __future__ import annotations

from dataclasses import dataclass, field

from xninetzy.context.media.video.models import VideoProject


@dataclass(frozen=True, slots=True)
class PlatformSpec:
    platform: str
    label: str
    allowed_aspects: tuple[tuple[int, int], ...]
    min_fps: int
    max_fps: int
    min_duration_seconds: float
    max_duration_seconds: float
    min_width: int
    min_height: int
    recommended_aspect: tuple[int, int]
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "label": self.label,
            "allowed_aspects": [f"{w}:{h}" for w, h in self.allowed_aspects],
            "recommended_aspect": f"{self.recommended_aspect[0]}:{self.recommended_aspect[1]}",
            "fps_range": [self.min_fps, self.max_fps],
            "duration_seconds_range": [self.min_duration_seconds, self.max_duration_seconds],
            "min_resolution": {"width": self.min_width, "height": self.min_height},
            "notes": self.notes,
        }


PLATFORM_SPECS: dict[str, PlatformSpec] = {
    "tiktok": PlatformSpec(
        platform="tiktok",
        label="TikTok",
        allowed_aspects=((9, 16), (1, 1)),
        min_fps=23,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=600.0,
        min_width=720,
        min_height=1280,
        recommended_aspect=(9, 16),
        notes="Vertical 1080x1920 preferred; keep hook in first 3s; leave right/bottom safe area for UI.",
    ),
    "instagram_reels": PlatformSpec(
        platform="instagram_reels",
        label="Instagram Reels",
        allowed_aspects=((9, 16),),
        min_fps=23,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=90.0,
        min_width=1080,
        min_height=1920,
        recommended_aspect=(9, 16),
        notes="1080x1920; up to 90s; captions recommended for muted autoplay.",
    ),
    "instagram_feed": PlatformSpec(
        platform="instagram_feed",
        label="Instagram Feed",
        allowed_aspects=((1, 1), (4, 5)),
        min_fps=23,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=60.0,
        min_width=1080,
        min_height=1080,
        recommended_aspect=(4, 5),
        notes="4:5 (1080x1350) maximizes feed real estate; 1:1 also accepted.",
    ),
    "youtube_shorts": PlatformSpec(
        platform="youtube_shorts",
        label="YouTube Shorts",
        allowed_aspects=((9, 16),),
        min_fps=24,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=180.0,
        min_width=1080,
        min_height=1920,
        recommended_aspect=(9, 16),
        notes="Vertical, up to 180s; 1080x1920 recommended.",
    ),
    "youtube_landscape": PlatformSpec(
        platform="youtube_landscape",
        label="YouTube (landscape)",
        allowed_aspects=((16, 9),),
        min_fps=24,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=600.0,
        min_width=1280,
        min_height=720,
        recommended_aspect=(16, 9),
        notes="1920x1080 recommended; 720p minimum for HD.",
    ),
    "x_twitter": PlatformSpec(
        platform="x_twitter",
        label="X / Twitter",
        allowed_aspects=((16, 9), (1, 1)),
        min_fps=23,
        max_fps=60,
        min_duration_seconds=1.0,
        max_duration_seconds=140.0,
        min_width=720,
        min_height=720,
        recommended_aspect=(16, 9),
        notes="Up to 140s for standard accounts; 16:9 or 1:1.",
    ),
}


@dataclass(frozen=True, slots=True)
class PlatformReadiness:
    platform: str
    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    measured: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "measured": dict(self.measured),
        }


def available_platforms() -> list[str]:
    return sorted(PLATFORM_SPECS)


def _aspect_matches(width: int, height: int, aspect: tuple[int, int], tolerance: float) -> bool:
    if height <= 0 or aspect[1] <= 0:
        return False
    return abs((width / height) - (aspect[0] / aspect[1])) <= tolerance


def validate_for_platform(
    project: VideoProject,
    platform: str,
    *,
    aspect_tolerance: float = 0.02,
) -> PlatformReadiness:
    spec = PLATFORM_SPECS.get(platform.strip().lower())
    if spec is None:
        return PlatformReadiness(
            platform=platform,
            ok=False,
            errors=(
                f"unknown platform '{platform}'; known: {', '.join(available_platforms())}",
            ),
        )
    composition = project.primary_composition()
    width = composition.resolution.width
    height = composition.resolution.height
    fps = composition.fps
    duration = composition.duration_seconds()
    errors: list[str] = []
    warnings: list[str] = []

    if not any(_aspect_matches(width, height, a, aspect_tolerance) for a in spec.allowed_aspects):
        allowed = ", ".join(f"{w}:{h}" for w, h in spec.allowed_aspects)
        errors.append(
            f"aspect {width}x{height} not allowed for {spec.label}; allowed: {allowed}"
        )

    if fps < spec.min_fps or fps > spec.max_fps:
        errors.append(
            f"fps {fps} outside {spec.label} range {spec.min_fps}-{spec.max_fps}"
        )

    if duration > spec.max_duration_seconds:
        errors.append(
            f"duration {duration:.1f}s exceeds {spec.label} max {spec.max_duration_seconds:.0f}s"
        )
    if duration < spec.min_duration_seconds:
        errors.append(
            f"duration {duration:.1f}s below {spec.label} min {spec.min_duration_seconds:.0f}s"
        )

    if width < spec.min_width or height < spec.min_height:
        warnings.append(
            f"resolution {width}x{height} below recommended "
            f"{spec.min_width}x{spec.min_height} for {spec.label}"
        )

    return PlatformReadiness(
        platform=spec.platform,
        ok=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        measured={
            "width": width,
            "height": height,
            "fps": fps,
            "duration_seconds": round(duration, 3),
            "aspect_ratio": round(width / height, 4) if height else None,
        },
    )
