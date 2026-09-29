from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import tool

from xninetzy.integrations.moviepy.capabilities import capability_snapshot
from xninetzy.integrations.moviepy.editor import MoviePyUnavailable
from xninetzy.integrations.moviepy.reframe import ReframeError


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _resolve_target(width: int, height: int, platform: str) -> tuple[int, int]:
    if platform:
        from xninetzy.context.media.video.social import PLATFORM_SPECS

        spec = PLATFORM_SPECS.get(platform.strip().lower())
        if spec is not None:
            aspect_w, aspect_h = spec.recommended_aspect
            if aspect_w == aspect_h:
                return 1080, 1080
            if aspect_h > aspect_w:
                return 1080, 1920
            return 1920, 1080
    return width, height


@tool
def moviepy_status() -> str:
    """Snapshot kapabilitas MoviePy + ffmpeg untuk editing video sosial media."""
    return _ok(capability_snapshot())


@tool
def moviepy_reframe(
    input_path: str,
    output_path: str,
    platform: str = "",
    target_width: int = 1080,
    target_height: int = 1920,
    mode: str = "crop",
    fps: int = 0,
) -> str:
    """Ubah aspect ratio video untuk platform sosial (mis. landscape -> 9:16).

    Gunakan ``platform`` (tiktok, instagram_reels, youtube_shorts, ...) untuk
    memilih target ratio otomatis, atau ``target_width``/``target_height``
    manual. ``mode`` = crop (isi penuh, center-crop) atau pad (fit + bar warna).
    Output ditulis di dalam artifact roots (ARTIFACT_ALLOWLIST).

    Args:
        input_path: Path video sumber.
        output_path: Path output (di dalam artifact roots).
        platform: Nama platform target (opsional, menimpa target_width/height).
        target_width: Lebar target (dipakai jika platform kosong).
        target_height: Tinggi target (dipakai jika platform kosong).
        mode: crop | pad.
        fps: FPS output (0 = ikuti sumber).
    """
    if not os.path.isfile(input_path):
        return _ok({"status": "error", "error": f"input not found: {input_path}"})
    from xninetzy.core.paths import ArtifactPathError, resolve_artifact_output

    try:
        safe_output = str(
            resolve_artifact_output(
                output_path,
                create_parents=True,
                extra_roots=(os.path.dirname(os.path.abspath(input_path)),),
            )
        )
    except ArtifactPathError as exc:
        return _ok({"status": "error", "error": str(exc)})
    width, height = _resolve_target(target_width, target_height, platform)
    from xninetzy.integrations.moviepy.editor import reframe_video

    try:
        result = reframe_video(
            input_path,
            safe_output,
            width,
            height,
            mode=mode,
            fps=(fps or None),
        )
    except MoviePyUnavailable as exc:
        return _ok({"status": "unavailable", "error": str(exc)})
    except ReframeError as exc:
        return _ok({"status": "error", "error": str(exc)})
    except Exception as exc:
        return _ok({"status": "error", "error": f"reframe failed: {exc}"})
    return _ok(result)


@tool
def moviepy_concat(
    input_paths: list[str],
    output_path: str,
    target_width: int = 0,
    target_height: int = 0,
    crossfade_seconds: float = 0.0,
    fps: int = 0,
) -> str:
    """Gabungkan beberapa klip menjadi satu, opsional crossfade + normalisasi ukuran.

    Args:
        input_paths: Daftar path klip (urutan dipertahankan).
        output_path: Path output (di dalam artifact roots).
        target_width: Normalisasi lebar (0 = tidak dinormalisasi).
        target_height: Normalisasi tinggi (0 = tidak dinormalisasi).
        crossfade_seconds: Durasi crossfade antar klip (0 = potong keras).
        fps: FPS output (0 = ikuti klip pertama).
    """
    paths = [p for p in (input_paths or []) if isinstance(p, str) and p.strip()]
    if len(paths) < 2:
        return _ok({"status": "error", "error": "concat requires at least two input clips"})
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        return _ok({"status": "error", "error": f"inputs not found: {missing}"})
    from xninetzy.core.paths import ArtifactPathError, resolve_artifact_output

    try:
        safe_output = str(
            resolve_artifact_output(
                output_path,
                create_parents=True,
                extra_roots=(os.path.dirname(os.path.abspath(paths[0])),),
            )
        )
    except ArtifactPathError as exc:
        return _ok({"status": "error", "error": str(exc)})
    from xninetzy.integrations.moviepy.editor import concat_videos

    try:
        result = concat_videos(
            paths,
            safe_output,
            target_width=(target_width or None),
            target_height=(target_height or None),
            crossfade_seconds=crossfade_seconds,
            fps=(fps or None),
        )
    except MoviePyUnavailable as exc:
        return _ok({"status": "unavailable", "error": str(exc)})
    except ReframeError as exc:
        return _ok({"status": "error", "error": str(exc)})
    except Exception as exc:
        return _ok({"status": "error", "error": f"concat failed: {exc}"})
    return _ok(result)


moviepy_tools = [
    moviepy_status,
    moviepy_reframe,
    moviepy_concat,
]
