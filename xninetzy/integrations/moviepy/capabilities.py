from __future__ import annotations

import shutil


def moviepy_available() -> bool:
    try:
        import moviepy  # noqa: F401
    except Exception:
        return False
    return True


def moviepy_version() -> str:
    try:
        import moviepy

        return str(getattr(moviepy, "__version__", "unknown"))
    except Exception:
        return "unavailable"


def ffmpeg_path() -> str | None:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        return exe or None
    except Exception:
        return None


def capability_snapshot() -> dict:
    available = moviepy_available()
    ffmpeg = ffmpeg_path()
    return {
        "moviepy_available": available,
        "moviepy_version": moviepy_version() if available else "unavailable",
        "ffmpeg_available": ffmpeg is not None,
        "ffmpeg_source": (
            "system" if shutil.which("ffmpeg") else ("bundled" if ffmpeg else "missing")
        ),
        "ready": available and ffmpeg is not None,
    }
