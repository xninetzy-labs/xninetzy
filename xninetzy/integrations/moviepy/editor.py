from __future__ import annotations

from xninetzy.integrations.moviepy.capabilities import ffmpeg_path, moviepy_available
from xninetzy.integrations.moviepy.reframe import ReframeError, plan_reframe


class MoviePyUnavailable(RuntimeError):
    pass


def _require_ready() -> None:
    if not moviepy_available():
        raise MoviePyUnavailable(
            "moviepy is not installed. Install the optional extra: "
            "pip install 'xninetzy-mcp[moviepy]'"
        )
    if ffmpeg_path() is None:
        raise MoviePyUnavailable(
            "ffmpeg not found. Install ffmpeg or the imageio-ffmpeg bundle."
        )


def _configure_ffmpeg() -> None:
    import os

    path = ffmpeg_path()
    if path:
        os.environ.setdefault("IMAGEIO_FFMPEG_EXE", path)


def reframe_video(
    input_path: str,
    output_path: str,
    target_width: int,
    target_height: int,
    mode: str = "crop",
    background_color: tuple[int, int, int] = (0, 0, 0),
    fps: int | None = None,
) -> dict:
    _require_ready()
    _configure_ffmpeg()
    from moviepy import ColorClip, CompositeVideoClip, VideoFileClip

    clip = VideoFileClip(input_path)
    try:
        plan = plan_reframe(clip.w, clip.h, target_width, target_height, mode=mode)
        out_fps = fps or int(round(clip.fps or 30))
        if plan.mode == "crop":
            resized = clip.resized(new_size=(plan.scaled_width, plan.scaled_height))
            framed = resized.cropped(
                x1=plan.crop_x1,
                y1=plan.crop_y1,
                x2=plan.crop_x2,
                y2=plan.crop_y2,
            )
        else:
            resized = clip.resized(new_size=(plan.scaled_width, plan.scaled_height))
            background = ColorClip(
                size=(plan.target_width, plan.target_height),
                color=background_color,
            ).with_duration(clip.duration)
            positioned = resized.with_position((plan.pad_x, plan.pad_y))
            framed = CompositeVideoClip(
                [background, positioned],
                size=(plan.target_width, plan.target_height),
            )
        framed = framed.with_fps(out_fps)
        framed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=out_fps,
            logger=None,
        )
        result = {
            "status": "ok",
            "output_path": output_path,
            "plan": plan.to_dict(),
            "fps": out_fps,
            "duration_seconds": round(float(clip.duration or 0.0), 3),
        }
    finally:
        try:
            clip.close()
        except Exception:
            pass
    return result


def concat_videos(
    input_paths: list[str],
    output_path: str,
    target_width: int | None = None,
    target_height: int | None = None,
    crossfade_seconds: float = 0.0,
    fps: int | None = None,
) -> dict:
    _require_ready()
    _configure_ffmpeg()
    if len(input_paths) < 2:
        raise ReframeError("concat requires at least two input clips")
    from moviepy import VideoFileClip, concatenate_videoclips, vfx

    clips = []
    try:
        for path in input_paths:
            clip = VideoFileClip(path)
            if target_width and target_height:
                clip = clip.resized(new_size=(target_width, target_height))
            clips.append(clip)
        out_fps = fps or int(round(clips[0].fps or 30))
        if crossfade_seconds > 0:
            faded = [clips[0]]
            for clip in clips[1:]:
                faded.append(clip.with_effects([vfx.CrossFadeIn(crossfade_seconds)]))
            final = concatenate_videoclips(
                faded, method="compose", padding=-crossfade_seconds
            )
        else:
            final = concatenate_videoclips(clips, method="compose")
        final = final.with_fps(out_fps)
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=out_fps,
            logger=None,
        )
        result = {
            "status": "ok",
            "output_path": output_path,
            "clip_count": len(clips),
            "crossfade_seconds": crossfade_seconds,
            "fps": out_fps,
            "duration_seconds": round(float(final.duration or 0.0), 3),
        }
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
    return result
