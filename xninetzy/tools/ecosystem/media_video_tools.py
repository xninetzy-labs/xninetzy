"""MCP tools for the deterministic Video Creator + Editor subsystem.

CPU-only. NO generative video model integration. All rendering
goes through ``xninetzy.interfaces.media.video_backends.{ffmpeg,remotion}``
which sit behind ``xninetzy.context.media.video.renderers.*``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.core.logging import logging
from xninetzy.db.idempotency import idempotent_call
from xninetzy.ecosystem.event_bus import record_event

logger = logging.getLogger(__name__)


def _engine():
    from xninetzy.context.media.video.project_engine import VideoProjectEngine
    return VideoProjectEngine()


def _router():
    from xninetzy.context.media.video.renderers import default_router
    return default_router()


def _storage():
    from xninetzy.context.media.video.storage import (
        init_video_schema, VideoProjectStore, VideoJobStore,
    )
    init_video_schema()
    return VideoProjectStore(), VideoJobStore()


def _ffprobe_meta(path: str) -> dict[str, Any]:
    from xninetzy.interfaces.media.video_backends.ffmpeg import probe_metadata
    return probe_metadata("ffprobe", path)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_bytes(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _ensure_safe_path(path: str, allowed_roots: tuple[str, ...]) -> str:
    from xninetzy.context.media.video.validators import validate_path_within_roots
    if not validate_path_within_roots(path, allowed_roots):
        raise ValueError(
            f"path {path!r} is outside allowed roots {allowed_roots!r}"
        )
    return os.path.abspath(path)


def _default_output_dir() -> str:
    raw = os.environ.get("VIDEO_OUTPUT_DIR") or os.path.join(
        os.path.expanduser("~"), "Documents", "xninetzy", "output", "video"
    )
    return os.path.abspath(raw)


@tool
def video_project_create(
    name: str,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    duration_seconds: float = 30.0,
    preset: str = "youtube_landscape",
    source_project_root: str = "",
    project_id: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Buat VideoProject baru (editable source of truth).

    Args:
        name: Nama project (mis. "My App Demo")
        width: Lebar composition (default 1920)
        height: Tinggi composition (default 1080)
        fps: Frame rate composition (default 30)
        duration_seconds: Durasi total (default 30.0; max 600.0)
        preset: youtube_landscape | shorts_vertical | instagram_vertical |
                square_social | presentation | custom
        source_project_root: Path ke project sumber (opsional, untuk dev-video)
        project_id: UUID kustom (opsional; auto-generated jika kosong)
        chat_id: Chat identifier untuk event bus
        idempotency_key: Kunci opsional agar retry tidak duplikat
    """

    from xninetzy.context.media.video.models import (
        CompositionPreset,
        resolution_for_preset,
    )

    def _create() -> str:
        engine = _engine()
        preset_enum = CompositionPreset(preset) if preset else CompositionPreset.CUSTOM
        target_width, target_height = width, height
        if preset_enum is not CompositionPreset.CUSTOM:
            preset_resolution = resolution_for_preset(preset_enum)
            target_width = preset_resolution.width
            target_height = preset_resolution.height
        composition = engine.create_composition(
            name=name,
            width=target_width,
            height=target_height,
            fps=fps,
            duration_seconds=duration_seconds,
            preset=preset_enum,
        )
        project = engine.create_project(
            project_id=project_id or None,
            name=name,
            source_project_root=source_project_root or None,
            composition=composition,
        )
        try:
            record_event(
                chat_id, "video_project_created", "", "video_project",
                project.project_id, {"name": name, "duration": duration_seconds},
            )
        except Exception:
            logger.warning("record_event failed for video_project_create", exc_info=True)
        return _ok({
            "status": "created",
            "project_id": project.project_id,
            "version": project.version,
            "composition_id": composition.composition_id,
            "resolution": composition.resolution.to_dict(),
            "fps": composition.fps,
            "duration_seconds": composition.duration_seconds(),
            "preset": composition.preset.value,
        })

    result, _ = idempotent_call("video_project_create", idempotency_key, {}, _create)
    return result


@tool
def video_project_inspect(project_id: str) -> str:
    """Lihat metadata VideoProject (composition, scenes, assets, hash).

    Args:
        project_id: ID VideoProject
    """
    engine = _engine()
    return _ok(engine.inspect(project_id))


@tool
def video_project_export_json(project_id: str) -> str:
    """Serialize VideoProject menjadi video-project.json (canonical JSON).

    Args:
        project_id: ID VideoProject
    """
    engine = _engine()
    return engine.export_video_project_json(project_id)


@tool
def video_template_apply(
    project_id: str,
    template: str,
    duration_seconds: float = 30.0,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Apply a deterministic template (project_demo | tutorial |
    development_journey | motion_graph) to the project.

    Args:
        project_id: ID VideoProject yang sudah ada
        template: project_demo | tutorial | development_journey | motion_graph
        duration_seconds: Durasi total (default 30)
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """

    from xninetzy.context.media.video.models import CompositionPreset
    from xninetzy.context.media.video.templates import (
        TemplateContext,
        project_demo_template,
        tutorial_template,
        development_journey_template,
        motion_graph_template,
    )

    fns = {
        "project_demo": project_demo_template,
        "tutorial": tutorial_template,
        "development_journey": development_journey_template,
        "motion_graph": motion_graph_template,
    }
    if template not in fns:
        raise ValueError(
            f"unknown template {template!r}; expected one of {sorted(fns)}"
        )

    def _apply() -> str:
        store, _ = _storage()
        project = store.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        preset = project.primary_composition().preset
        ctx = TemplateContext(
            project_id=project_id,
            name=project.name,
            fps=project.primary_composition().fps,
            preset=preset if preset != CompositionPreset.CUSTOM else CompositionPreset.YOUTUBE_LANDSCAPE,
            source_project_root=project.source_project_root,
            duration_seconds=duration_seconds,
            assets=tuple(project.assets),
        )
        built = fns[template](ctx)
        from dataclasses import replace
        merged = replace(
            built,
            project_id=project.project_id,
            source_project_root=project.source_project_root,
            created_at=project.created_at,
            updated_at=_now_iso(),
            version=project.version + 1,
            assets=project.assets,
            metadata=project.metadata,
        )
        store.upsert(merged)
        try:
            record_event(
                chat_id, "video_template_applied", "", "video_project",
                project_id, {"template": template, "scene_count": len(merged.scenes)},
            )
        except Exception:
            logger.warning("record_event failed for video_template_apply", exc_info=True)
        return _ok({
            "status": "applied",
            "template": template,
            "project_id": project_id,
            "scene_count": len(merged.scenes),
            "scene_purposes": [s.purpose for s in merged.scenes],
            "version": merged.version,
        })

    result, _ = idempotent_call(
        f"video_template_apply:{template}", idempotency_key,
        {"project_id": project_id, "template": template}, _apply,
    )
    return result


@tool
def video_asset_import(
    project_id: str,
    source_path: str,
    kind: str = "image",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Daftarkan media asset ke VideoProject (path + content_hash + metadata).

    Args:
        project_id: ID VideoProject target
        source_path: Path absolut ke file media (PNG/JPG/MP4/WAV/SVG/...)
        kind: video | image | svg | audio | font | logo | screenshot | code | text | data
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """
    from xninetzy.context.media.video.models import AssetKind, VideoAsset

    def _import() -> str:
        abs_path = _ensure_safe_path(
            source_path,
            (os.path.expanduser("~"), "/tmp", _default_output_dir()),
        )
        if not os.path.isfile(abs_path):
            raise ValueError(f"asset not found: {abs_path}")
        content_hash = _hash_bytes(abs_path)
        size_bytes = os.path.getsize(abs_path)
        mime = _mime_from_path(abs_path)
        kind_enum = AssetKind(kind)
        asset = VideoAsset(
            asset_id=f"asset-{uuid.uuid4().hex[:8]}",
            kind=kind_enum,
            source_path=abs_path,
            mime_type=mime,
            content_hash=content_hash,
            width=None,
            height=None,
            duration_seconds=None,
            fps=None,
            metadata={"size_bytes": size_bytes},
        )
        engine = _engine()
        engine.import_asset(project_id, asset)
        try:
            record_event(
                chat_id, "video_asset_imported", "", "video_asset",
                asset.asset_id, {"project_id": project_id, "kind": kind},
            )
        except Exception:
            logger.warning("record_event failed for video_asset_import", exc_info=True)
        return _ok({
            "status": "imported",
            "asset_id": asset.asset_id,
            "kind": kind,
            "mime_type": mime,
            "size_bytes": size_bytes,
            "content_hash": content_hash,
        })

    result, _ = idempotent_call(
        "video_asset_import", idempotency_key,
        {"project_id": project_id, "source_path": source_path}, _import,
    )
    return result


def _mime_from_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
    }.get(ext, "application/octet-stream")


@tool
def video_scene_create(
    project_id: str,
    name: str,
    purpose: str = "intro",
    duration_seconds: float = 3.0,
    motion_primitives: list[str] | None = None,
    motion_parameters: dict[str, dict[str, float]] | None = None,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Tambahkan scene baru ke VideoProject dengan motion primitives.

    Args:
        project_id: ID VideoProject target
        name: Nama scene (mis. "Login")
        purpose: intro | problem | architecture | implementation | demo | result | outro | hook | context | step | summary | feature | transition | interaction | cta
        duration_seconds: Durasi scene (default 3.0)
        motion_primitives: Daftar nama primitive (mis. ["FadeIn","CameraPush"])
        motion_parameters: Dict parameter per primitive (mis. {"CameraPush": {"to_scale": 1.06}})
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """

    from xninetzy.context.media.video.models import (
        Easing,
        MotionPreset,
        VideoScene,
    )

    def _create() -> str:
        store, _ = _storage()
        project = store.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        comp = project.primary_composition()
        cursor = sum(s.duration_frames for s in project.scenes)
        duration_frames = int(duration_seconds * comp.fps)
        presets: list[MotionPreset] = []
        primitives = motion_primitives or []
        params_by_primitive = motion_parameters or {}
        for prim_name in primitives:
            params = params_by_primitive.get(prim_name, {})
            presets.append(MotionPreset(
                primitive=prim_name,
                target="scene",
                start_frame=cursor,
                end_frame=cursor + duration_frames,
                easing=Easing.EASE_IN_OUT,
                parameters=params,
            ))
        scene = VideoScene(
            scene_id=f"scene-{uuid.uuid4().hex[:8]}",
            composition_id=comp.composition_id,
            name=name,
            purpose=purpose,
            start_frame=cursor,
            duration_frames=duration_frames,
            motion_presets=presets,
        )
        engine = _engine()
        engine.add_scene(project_id, scene)
        try:
            record_event(
                chat_id, "video_scene_created", "", "video_scene",
                scene.scene_id, {"project_id": project_id, "purpose": purpose},
            )
        except Exception:
            logger.warning("record_event failed for video_scene_create", exc_info=True)
        return _ok({
            "status": "created",
            "scene_id": scene.scene_id,
            "name": name,
            "purpose": purpose,
            "start_frame": cursor,
            "duration_frames": duration_frames,
            "motion_primitives": primitives,
        })

    result, _ = idempotent_call(
        "video_scene_create", idempotency_key,
        {"project_id": project_id, "name": name, "purpose": purpose}, _create,
    )
    return result


@tool
def video_motion_apply(
    project_id: str,
    scene_id: str,
    primitive: str,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    easing: str = "ease_in_out",
    parameters: dict[str, float] | None = None,
    target: str = "scene",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Tambahkan motion preset ke scene (validated against canonical primitives).

    Args:
        project_id: ID VideoProject target
        scene_id: ID scene target
        primitive: Nama primitive (FadeIn | SlideIn | CameraPush | ...)
        start_seconds: Batas awal (None = pakai scene.start_frame)
        end_seconds: Batas akhir (None = pakai scene.end_frame)
        easing: linear | ease_in | ease_out | ease_in_out | cubic_bezier | spring_deterministic
        parameters: Dict parameter (mis. {"to_scale": 1.06})
        target: Target scene element (default "scene")
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """
    from xninetzy.context.media.video.models import Easing, MotionPreset

    def _apply() -> str:
        store, _ = _storage()
        project = store.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        comp = project.primary_composition()
        fps = comp.fps
        target_scene = next((s for s in project.scenes if s.scene_id == scene_id), None)
        if target_scene is None:
            raise ValueError(f"scene {scene_id!r} not found in project {project_id!r}")
        s_frame = (
            int(start_seconds * fps) if start_seconds is not None
            else target_scene.start_frame
        )
        e_frame = (
            int(end_seconds * fps) if end_seconds is not None
            else target_scene.end_frame()
        )
        preset = MotionPreset(
            primitive=primitive,
            target=target,
            start_frame=s_frame,
            end_frame=e_frame,
            easing=Easing(easing),
            parameters=parameters or {},
        )
        from dataclasses import replace
        updated_scene = replace(
            target_scene,
            motion_presets=target_scene.motion_presets + [preset],
        )
        new_scenes = [
            replace(s, motion_presets=updated_scene.motion_presets) if s.scene_id == scene_id else s
            for s in project.scenes
        ]
        from dataclasses import replace as _replace
        updated = _replace(
            project,
            scenes=new_scenes,
            updated_at=_now_iso(),
            version=project.version + 1,
        )
        store.upsert(updated)
        try:
            record_event(
                chat_id, "video_motion_applied", "", "video_scene",
                scene_id, {"primitive": primitive},
            )
        except Exception:
            logger.warning("record_event failed for video_motion_apply", exc_info=True)
        return _ok({
            "status": "applied",
            "project_id": project_id,
            "scene_id": scene_id,
            "primitive": primitive,
            "start_frame": s_frame,
            "end_frame": e_frame,
            "easing": easing,
        })

    result, _ = idempotent_call(
        "video_motion_apply", idempotency_key,
        {"project_id": project_id, "scene_id": scene_id, "primitive": primitive},
        _apply,
    )
    return result


@tool
def video_render(
    project_id: str,
    output_format: str = "mp4",
    quality: str = "balanced",
    max_runtime_seconds: int = 600,
    concurrency: int = 1,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Render VideoProject via RendererRouter (FFmpeg CPU atau Remotion CPU).

    Args:
        project_id: ID VideoProject target
        output_format: mp4 | webm
        quality: fast | balanced | high
        max_runtime_seconds: Batas waktu render (default 600)
        concurrency: 1..4
        chat_id: Chat identifier
        idempotency_key: Kunci opsional agar tidak double-render
    """

    def _render() -> str:
        store, job_store = _storage()
        project = store.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        comp = project.primary_composition()
        output_dir = _default_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        render_id = f"r-{uuid.uuid4().hex[:10]}"
        output_path = os.path.join(output_dir, f"{project_id}-{render_id}.{output_format}")
        props_path = os.path.join(output_dir, f"{project_id}-{render_id}.props.json")
        from xninetzy.context.media.video.models import RenderRequest
        request = RenderRequest(
            project_id=project_id,
            composition_id=comp.composition_id,
            project_version=project.version,
            output_format=output_format,
            output_path=output_path,
            props_path=props_path,
            quality=quality,
            concurrency=concurrency,
            max_runtime_seconds=max_runtime_seconds,
        )
        job_store.create(
            render_id=render_id,
            project_id=project_id,
            project_version=project.version,
            composition_id=comp.composition_id,
            renderer="ffmpeg-cpu",
            output_format=output_format,
            output_path=output_path,
            props_path=props_path,
            width=comp.resolution.width,
            height=comp.resolution.height,
            fps=comp.fps,
            duration_frames=comp.duration_frames,
            quality=quality,
            concurrency=concurrency,
            max_runtime_seconds=max_runtime_seconds,
            preview=False,
            idempotency_key=idempotency_key,
            selection_reason="default_local_cpu_ffmpeg",
        )
        job_store.transition(render_id, "running", "render started")
        router = _router()
        from xninetzy.context.media.video.errors import VideoError
        try:
            result = router.dispatch(
                project, request,
                required_capabilities=frozenset(),
            )
        except VideoError as exc:
            job_store.transition(
                render_id, "failed", f"{exc.code}: {exc.message}"
            )
            job_store.record_exit(
                render_id,
                exit_code=exc.code,
                stdout_summary="",
                stderr_summary=exc.message[:4000],
                size_bytes=None,
                artifact_id=None,
                error_code=exc.code,
            )
            return _ok({
                "status": "failed",
                "render_id": render_id,
                "error_code": exc.code,
                "message": exc.message,
            })
        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        job_store.record_exit(
            render_id,
            exit_code=result.exit_code,
            stdout_summary=result.stdout_summary,
            stderr_summary=result.stderr_summary,
            size_bytes=size,
            artifact_id=result.artifact_id,
            error_code=None,
        )
        job_store.transition(render_id, "validating", "ffprobe")
        meta = _ffprobe_meta(output_path)
        job_store.transition(render_id, "completed", "render ok")
        try:
            record_event(
                chat_id, "video_render_completed", "", "video_render",
                render_id, {"output_path": output_path, "size": size},
            )
        except Exception:
            logger.warning("record_event failed for video_render", exc_info=True)
        return _ok({
            "status": "completed",
            "render_id": render_id,
            "renderer": result.renderer.value,
            "codec": result.codec,
            "size_bytes": size,
            "duration_seconds": result.duration_seconds,
            "resolution": {"width": result.width, "height": result.height},
            "fps": result.fps,
            "output_path": output_path,
            "props_path": props_path,
            "ffprobe": meta,
        })

    result, _ = idempotent_call(
        "video_render", idempotency_key, {"project_id": project_id, "quality": quality}, _render,
    )
    return result


@tool
def video_render_status(render_id: str) -> str:
    """Query status render job (state, exit, sizes, stderr summary).

    Args:
        render_id: ID render job
    """
    _, job_store = _storage()
    rec = job_store.get(render_id)
    if rec is None:
        return _ok({"status": "not_found", "render_id": render_id})
    events = job_store.events(render_id)
    return _ok({
        "status": "found",
        "render": rec,
        "events": events,
    })


@tool
def video_render_cancel(render_id: str) -> str:
    """Cancel a running render (best-effort).

    Args:
        render_id: ID render job
    """
    _, job_store = _storage()
    rec = job_store.get(render_id)
    if rec is None:
        return _ok({"status": "not_found", "render_id": render_id})
    if rec["status"] in {"completed", "failed", "cancelled"}:
        return _ok({
            "status": "no_op",
            "render_id": render_id,
            "current_state": rec["status"],
        })
    job_store.transition(render_id, "cancel_requested", "cancel requested by tool")
    router = _router()
    cancelled = router.cancel(render_id)
    job_store.transition(render_id, "cancelled", "cancelled")
    return _ok({
        "status": "cancelled",
        "render_id": render_id,
        "cancelled": cancelled,
    })


@tool
def video_inspect(path: str) -> str:
    """Probe file video via ffprobe (codec, fps, duration, streams).

    Args:
        path: Path ke file MP4/WebM/etc.
    """
    abs_path = _ensure_safe_path(
        path, (os.path.expanduser("~"), "/tmp", _default_output_dir())
    )
    if not os.path.isfile(abs_path):
        return _ok({"status": "not_found", "path": abs_path})
    meta = _ffprobe_meta(abs_path)
    size = os.path.getsize(abs_path)
    content_hash = _hash_bytes(abs_path)
    return _ok({
        "status": "ok",
        "path": abs_path,
        "size_bytes": size,
        "content_hash": content_hash,
        "ffprobe": meta,
    })


@tool
def video_export(
    render_id: str,
    destination: str = "",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Copy final MP4 ke destination (default: Documents/xninetzy/output/video).

    Args:
        render_id: ID render job
        destination: Path absolut destination (kosong = default)
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """

    def _export() -> str:
        _, job_store = _storage()
        rec = job_store.get(render_id)
        if rec is None:
            raise ValueError(f"unknown render_id {render_id!r}")
        src = rec["output_path"]
        if not os.path.isfile(src):
            raise ValueError(f"render output missing: {src}")
        dest = (
            destination or os.path.join(
                os.path.expanduser("~"), "Documents", "xninetzy", "output",
                "video", os.path.basename(src),
            )
        )
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        try:
            record_event(
                chat_id, "video_export_completed", "", "video_render",
                render_id, {"destination": dest},
            )
        except Exception:
            logger.warning("record_event failed for video_export", exc_info=True)
        return _ok({
            "status": "exported",
            "render_id": render_id,
            "source": src,
            "destination": dest,
            "size_bytes": os.path.getsize(dest),
        })

    result, _ = idempotent_call(
        "video_export", idempotency_key, {"render_id": render_id}, _export,
    )
    return result


@tool
def video_thumbnail_create(
    path: str,
    output_path: str = "",
    at_seconds: float = 0.0,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Extract thumbnail dari MP4 via ffmpeg seek.

    Args:
        path: Path ke MP4 source
        output_path: Destination thumbnail (kosong = auto di OUTPUT_DIR)
        at_seconds: Timestamp untuk seek (default 0.0)
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """

    from xninetzy.interfaces.media.video_backends.ffmpeg import which

    def _create() -> str:
        ffmpeg_bin = which("ffmpeg")
        src = _ensure_safe_path(
            path, (os.path.expanduser("~"), "/tmp", _default_output_dir())
        )
        if not os.path.isfile(src):
            raise ValueError(f"video not found: {src}")
        out = output_path or os.path.join(
            _default_output_dir(),
            f"{os.path.splitext(os.path.basename(src))[0]}-{int(time.time())}.png",
        )
        os.makedirs(os.path.dirname(out), exist_ok=True)
        import subprocess
        proc = subprocess.run(
            [
                ffmpeg_bin, "-y", "-nostdin",
                "-ss", f"{at_seconds:.4f}",
                "-i", src,
                "-frames:v", "1",
                "-q:v", "2",
                out,
            ],
            capture_output=True, text=True, check=False, timeout=60, shell=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg thumbnail failed: exit={proc.returncode} "
                f"stderr={proc.stderr[-400:]}"
            )
        size = os.path.getsize(out)
        try:
            record_event(
                chat_id, "video_thumbnail_created", "", "video_thumbnail",
                out, {"source": src, "size": size},
            )
        except Exception:
            logger.warning("record_event failed for video_thumbnail_create", exc_info=True)
        return _ok({
            "status": "created",
            "source": src,
            "output_path": out,
            "size_bytes": size,
            "at_seconds": at_seconds,
        })

    result, _ = idempotent_call(
        "video_thumbnail_create", idempotency_key,
        {"path": path, "at_seconds": at_seconds}, _create,
    )
    return result


def _dev_video_dir(project_id: str) -> str:
    base = os.environ.get("VIDEO_DEV_VIDEO_DIR") or os.path.join(
        os.path.expanduser("~"), ".local", "share", "xninetzy", "dev-video",
        project_id,
    )
    os.makedirs(base, exist_ok=True)
    return base


def _async_run(coro):
    try:
        import asyncio
    except ImportError as exc:
        raise RuntimeError("asyncio is unavailable") from exc
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.close()
        except Exception:
            pass


def _browser_session_path(session_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    base = os.environ.get("VIDEO_BROWSER_SESSION_DIR") or os.path.join(
        os.path.expanduser("~"), ".local", "share", "xninetzy", "video-sessions"
    )
    return os.path.join(base, safe)


def _try_launch_browser(session_id: str, owner: str, profile_dir: str) -> dict[str, Any]:
    try:
        from xninetzy.os.auth.browser.gateway import launch_local_browser
    except Exception as exc:
        return {"ok": False, "reason": f"browser_gateway_unavailable: {exc}"}
    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(
                _async_run,
                launch_local_browser(
                    session_id=session_id,
                    owner=owner,
                    headless=True,
                    profile_dir=Path(profile_dir),
                ),
            )
            try:
                result = future.result(timeout=15)
            except concurrent.futures.TimeoutError:
                return {"ok": False, "reason": "launch_timeout_15s"}
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "reason": f"launch_failed: {str(exc)[:200]}"}


def _try_close_browser(session_id: str) -> bool:
    try:
        from xninetzy.os.auth.browser.gateway import close_local_browser
    except Exception:
        return False
    try:
        return _async_run(close_local_browser(session_id=session_id))
    except Exception:
        return False


@tool
def video_session_start(
    project_id: str,
    capture_target: str = "browser",
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Start capture session — wires ke existing browser gateway untuk
    target=browser; desktop / window stub untuk screenshot / x11grab.

    Args:
        project_id: ID VideoProject target
        capture_target: browser | desktop | window
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """
    if capture_target not in {"browser", "desktop", "window"}:
        raise ValueError(
            f"unknown capture_target {capture_target!r}; "
            "expected browser|desktop|window"
        )

    def _start() -> str:
        session_id = f"capture-{uuid.uuid4().hex[:8]}"
        record: dict[str, Any] = {
            "session_id": session_id,
            "project_id": project_id,
            "capture_target": capture_target,
            "started_at": _now_iso(),
            "raw_dir": _dev_video_dir(project_id),
        }

        if capture_target == "browser":
            profile_dir = _browser_session_path(session_id)
            record["profile_dir"] = profile_dir
            if os.environ.get("VIDEO_BROWSER_DISABLED") == "1":
                record["browser_launch"] = {"ok": False, "reason": "disabled_by_env"}
                record["status"] = "browser_disabled"
            else:
                browser = _try_launch_browser(session_id, owner=chat_id, profile_dir=profile_dir)
                record["browser_launch"] = browser
                record["status"] = "started" if browser.get("ok") else "browser_unavailable"

        elif capture_target == "desktop":
            display = os.environ.get("DISPLAY", "")
            session_backend = os.environ.get("XDG_SESSION_TYPE", "")
            record["display"] = display
            record["session_backend"] = session_backend
            record["ffmpeg_capture_command"] = (
                f"ffmpeg -f x11grab -video_size {{WIDTH}}x{{HEIGHT}} -framerate {{FPS}} "
                f"-i {display or ':0.0'}+0,0 -c:v libx264 -preset medium -crf 23 "
                f"-movflags +faststart {record['raw_dir']}/desktop.mp4"
            )
            record["status"] = "reserved"

        elif capture_target == "window":
            record["ffmpeg_capture_command"] = (
                f"ffmpeg -f x11grab -video_size {{WIDTH}}x{{HEIGHT}} -framerate {{FPS}} "
                f"-i :0.0+0,0 -c:v libx264 -preset medium -crf 23 "
                f"-movflags +faststart {record['raw_dir']}/window.mp4"
            )
            record["status"] = "reserved"

        try:
            record_event(
                chat_id, "video_session_started", "", "video_session",
                session_id, {"project_id": project_id, "target": capture_target},
            )
        except Exception:
            logger.warning("record_event failed for video_session_start", exc_info=True)
        return _ok(record)

    result, _ = idempotent_call(
        "video_session_start", idempotency_key,
        {"project_id": project_id, "capture_target": capture_target}, _start,
    )
    return result


@tool
def video_session_stop(
    session_id: str,
    chat_id: str = "system",
    idempotency_key: str = "",
) -> str:
    """Stop capture session — closes browser gateway handle when applicable.

    Args:
        session_id: ID capture session
        chat_id: Chat identifier
        idempotency_key: Kunci opsional
    """

    def _stop() -> str:
        if os.environ.get("VIDEO_BROWSER_DISABLED") == "1":
            closed = False
        else:
            closed = _try_close_browser(session_id)
        try:
            record_event(
                chat_id, "video_session_stopped", "", "video_session",
                session_id, {"browser_closed": closed},
            )
        except Exception:
            logger.warning("record_event failed for video_session_stop", exc_info=True)
        return _ok({
            "status": "stopped",
            "session_id": session_id,
            "browser_closed": closed,
        })

    result, _ = idempotent_call(
        "video_session_stop", idempotency_key,
        {"session_id": session_id}, _stop,
    )
    return result


@tool
def video_renderer_health() -> str:
    """Health snapshot untuk FFmpeg + Remotion renderers."""
    from xninetzy.context.media.video.renderers import default_router
    router = default_router()
    snap = router.health_snapshot()
    out: dict[str, Any] = {}
    for rid, s in snap.items():
        out[rid] = s
    return _ok(out)


@tool
def video_platform_targets() -> str:
    """Daftar spesifikasi platform sosial media (aspect, fps, durasi, resolusi)."""
    from xninetzy.context.media.video.social import PLATFORM_SPECS

    return _ok({name: spec.to_dict() for name, spec in sorted(PLATFORM_SPECS.items())})


@tool
def video_validate_for_platform(project_id: str, platform: str) -> str:
    """Cek apakah VideoProject siap upload ke platform (tiktok, instagram_reels,
    instagram_feed, youtube_shorts, youtube_landscape, x_twitter).

    Memvalidasi aspect ratio, fps, durasi, dan resolusi komposisi utama terhadap
    spesifikasi platform sebelum render/upload. Mengembalikan ok + errors/warnings.

    Args:
        project_id: ID VideoProject.
        platform: Nama platform target.
    """
    from xninetzy.context.media.video.social import validate_for_platform

    store, _ = _storage()
    project = store.get(project_id)
    if project is None:
        return _ok({"ok": False, "errors": [f"unknown project_id {project_id!r}"]})
    report = validate_for_platform(project, platform)
    return _ok(report.to_dict())


media_video_tools = [
    video_project_create,
    video_project_inspect,
    video_project_export_json,
    video_template_apply,
    video_asset_import,
    video_scene_create,
    video_motion_apply,
    video_render,
    video_render_status,
    video_render_cancel,
    video_inspect,
    video_export,
    video_thumbnail_create,
    video_session_start,
    video_session_stop,
    video_renderer_health,
    video_platform_targets,
    video_validate_for_platform,
]
