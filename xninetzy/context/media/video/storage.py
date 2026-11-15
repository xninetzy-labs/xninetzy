from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from xninetzy.core.logging import logging
from xninetzy.db.sqlite import connect
from xninetzy.context.media.video.errors import VideoError
from xninetzy.context.media.video.models import (
    AssetKind,
    CompositionPreset,
    Easing,
    Keyframe,
    MotionPreset,
    Resolution,
    TrackKind,
    VideoAsset,
    VideoClip,
    VideoComposition,
    VideoProject,
    VideoScene,
    VideoTrack,
    VideoTransition,
)

logger = logging.getLogger(__name__)


VIDEO_SCHEMA_VERSION: str = "video-schema-1.0.0"


_DDL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS video_projects (
        project_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_project_root TEXT,
        schema_version TEXT NOT NULL,
        version INTEGER NOT NULL,
        project_json TEXT NOT NULL,
        project_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_video_projects_updated_at
        ON video_projects(updated_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS video_assets (
        asset_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        source_path TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        width INTEGER,
        height INTEGER,
        duration_seconds REAL,
        fps REAL,
        size_bytes INTEGER,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES video_projects(project_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_video_assets_project
        ON video_assets(project_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS video_jobs (
        render_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        project_version INTEGER NOT NULL,
        composition_id TEXT NOT NULL,
        renderer TEXT NOT NULL,
        status TEXT NOT NULL,
        output_format TEXT NOT NULL,
        output_path TEXT NOT NULL,
        props_path TEXT NOT NULL,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        fps INTEGER NOT NULL,
        duration_frames INTEGER NOT NULL,
        quality TEXT NOT NULL,
        concurrency INTEGER NOT NULL,
        max_runtime_seconds INTEGER NOT NULL,
        preview INTEGER NOT NULL,
        idempotency_key TEXT NOT NULL,
        created_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        exit_code INTEGER,
        stderr_summary TEXT NOT NULL DEFAULT '',
        stdout_summary TEXT NOT NULL DEFAULT '',
        size_bytes INTEGER,
        artifact_id TEXT,
        error_code TEXT,
        selection_reason TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES video_projects(project_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_video_jobs_status ON video_jobs(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_video_jobs_project
        ON video_jobs(project_id, project_version DESC)
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_video_jobs_idempotency
        ON video_jobs(idempotency_key)
        WHERE idempotency_key != ''
    """,
    """
    CREATE TABLE IF NOT EXISTS video_render_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        render_id TEXT NOT NULL,
        state TEXT NOT NULL,
        message TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (render_id) REFERENCES video_jobs(render_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_video_render_events_render
        ON video_render_events(render_id, id)
    """,
)


S_CREATED = "created"
S_QUEUED = "queued"
S_RUNNING = "running"
S_VALIDATING = "validating"
S_COMPLETED = "completed"
S_FAILED = "failed"
S_CANCELLED = "cancelled"


_VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    S_CREATED: frozenset({S_QUEUED, S_RUNNING, S_FAILED, S_CANCELLED}),
    S_QUEUED: frozenset({S_RUNNING, S_FAILED, S_CANCELLED}),
    S_RUNNING: frozenset({S_VALIDATING, S_FAILED, S_CANCELLED}),
    S_VALIDATING: frozenset({S_COMPLETED, S_FAILED}),
    S_COMPLETED: frozenset(),
    S_FAILED: frozenset(),
    S_CANCELLED: frozenset(),
}


def init_video_schema() -> dict[str, Any]:
    receipt = {"created": [], "indexed": [], "schema_version": VIDEO_SCHEMA_VERSION}
    with connect() as conn:
        for stmt in _DDL:
            conn.execute(stmt)
            kind = stmt.lstrip().upper().split()[1] if stmt.lstrip().upper().startswith("CREATE") else ""
            if kind == "TABLE" and "IF NOT EXISTS" in stmt:
                receipt["created"].append(_between(stmt, "TABLE", "("))
            elif kind == "INDEX":
                receipt["indexed"].append(_between(stmt, "INDEX", "ON"))
    logger.info("video schema initialised: %s", receipt)
    return receipt


def _between(stmt: str, after: str, before: str) -> str:
    out: list[str] = []
    parts = stmt.split()
    seen_after = False
    for tok in parts:
        if seen_after:
            if tok.startswith(before):
                return " ".join(out).strip()
            out.append(tok.strip(",").strip("`").strip('"'))
        elif tok.upper() == after:
            seen_after = True
    return " ".join(out).strip()


def content_hash(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _make_error(code: str, render_id: str | None = None,
                message: str | None = None) -> VideoError:
    return VideoError(code=code, message=message or code, job_id=render_id)


def _validate_transition(previous: str, new: str) -> None:
    allowed = _VALID_TRANSITIONS.get(previous, frozenset())
    if new not in allowed and previous != new:
        raise _make_error(
            "VIDEO_INVALID_ARGUMENT",
            message=f"invalid render state transition {previous!r} -> {new!r}",
        )


class VideoProjectStore:
    def upsert(self, project: VideoProject) -> str:
        body = project.to_json()
        h = content_hash(body)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO video_projects
                    (project_id, name, source_project_root, schema_version,
                     version, project_json, project_hash, created_at,
                     updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name=excluded.name,
                    source_project_root=excluded.source_project_root,
                    schema_version=excluded.schema_version,
                    version=excluded.version,
                    project_json=excluded.project_json,
                    project_hash=excluded.project_hash,
                    updated_at=excluded.updated_at,
                    metadata_json=excluded.metadata_json
                """,
                (
                    project.project_id,
                    project.name,
                    project.source_project_root,
                    project.schema_version,
                    project.version,
                    body,
                    h,
                    project.created_at,
                    project.updated_at,
                    json.dumps(dict(project.metadata)),
                ),
            )
        return h

    def get(self, project_id: str) -> VideoProject | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT project_json FROM video_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        if not row:
            return None
        return _decode_project(row["project_json"])

    def delete(self, project_id: str) -> bool:
        with connect() as conn:
            cur = conn.execute(
                "DELETE FROM video_projects WHERE project_id = ?", (project_id,)
            )
        return cur.rowcount > 0

    def list_projects(self, limit: int = 50) -> list[VideoProject]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT project_json FROM video_projects "
                "ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_decode_project(r["project_json"]) for r in rows]


class VideoAssetStore:
    def upsert(self, project_id: str, asset: VideoAsset) -> str:
        with connect() as conn:
            row = conn.execute(
                "SELECT size_bytes FROM video_assets WHERE asset_id = ?",
                (asset.asset_id,),
            ).fetchone()
            size = row["size_bytes"] if row else None
            conn.execute(
                """
                INSERT INTO video_assets
                    (asset_id, project_id, kind, source_path, mime_type,
                     content_hash, width, height, duration_seconds, fps,
                     size_bytes, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    kind=excluded.kind,
                    source_path=excluded.source_path,
                    mime_type=excluded.mime_type,
                    content_hash=excluded.content_hash,
                    width=excluded.width,
                    height=excluded.height,
                    duration_seconds=excluded.duration_seconds,
                    fps=excluded.fps,
                    metadata_json=excluded.metadata_json
                """,
                (
                    asset.asset_id,
                    project_id,
                    asset.kind.value,
                    asset.source_path,
                    asset.mime_type,
                    asset.content_hash,
                    asset.width,
                    asset.height,
                    asset.duration_seconds,
                    asset.fps,
                    size,
                    json.dumps(dict(asset.metadata)),
                    _now_iso(),
                ),
            )
        return asset.content_hash

    def delete(self, asset_id: str) -> bool:
        with connect() as conn:
            cur = conn.execute(
                "DELETE FROM video_assets WHERE asset_id = ?", (asset_id,)
            )
        return cur.rowcount > 0


class VideoJobStore:
    def create(
        self,
        *,
        render_id: str,
        project_id: str,
        project_version: int,
        composition_id: str,
        renderer: str,
        output_format: str,
        output_path: str,
        props_path: str,
        width: int,
        height: int,
        fps: int,
        duration_frames: int,
        quality: str,
        concurrency: int,
        max_runtime_seconds: int,
        preview: bool,
        idempotency_key: str,
        selection_reason: str,
    ) -> str:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO video_jobs
                    (render_id, project_id, project_version, composition_id,
                     renderer, status, output_format, output_path, props_path,
                     width, height, fps, duration_frames, quality,
                     concurrency, max_runtime_seconds, preview,
                     idempotency_key, created_at, selection_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    render_id, project_id, project_version, composition_id,
                    renderer, S_CREATED, output_format,
                    output_path, props_path, width, height, fps,
                    duration_frames, quality, concurrency,
                    max_runtime_seconds, int(bool(preview)),
                    idempotency_key, _now_iso(), selection_reason,
                ),
            )
            conn.execute(
                """
                INSERT INTO video_render_events
                    (render_id, state, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (render_id, S_CREATED, "job created", _now_iso()),
            )
        return render_id

    def transition(self, render_id: str, new_state: str, message: str = "") -> None:
        with connect() as conn:
            row = conn.execute(
                "SELECT status FROM video_jobs WHERE render_id = ?",
                (render_id,),
            ).fetchone()
            if row is None:
                raise _make_error("VIDEO_JOB_NOT_FOUND", render_id=render_id)
            previous = row["status"]
            _validate_transition(previous, new_state)
            updates = {"status": new_state}
            if new_state == S_RUNNING:
                updates["started_at"] = _now_iso()
            if new_state == S_COMPLETED:
                updates["finished_at"] = _now_iso()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE video_jobs SET {set_clause} WHERE render_id = ?",
                (*updates.values(), render_id),
            )
            conn.execute(
                """
                INSERT INTO video_render_events
                    (render_id, state, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (render_id, new_state, message[:2000], _now_iso()),
            )

    def record_exit(
        self,
        render_id: str,
        *,
        exit_code: int,
        stdout_summary: str,
        stderr_summary: str,
        size_bytes: int | None,
        artifact_id: str | None,
        error_code: str | None,
    ) -> None:
        with connect() as conn:
            conn.execute(
                """
                UPDATE video_jobs SET
                    exit_code = ?, stdout_summary = ?, stderr_summary = ?,
                    size_bytes = ?, artifact_id = ?, error_code = ?,
                    finished_at = ?
                WHERE render_id = ?
                """,
                (
                    exit_code, stdout_summary[:4000], stderr_summary[:4000],
                    size_bytes, artifact_id, error_code, _now_iso(), render_id,
                ),
            )

    def get(self, render_id: str) -> dict[str, Any] | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM video_jobs WHERE render_id = ?", (render_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_jobs(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM video_jobs WHERE status = ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM video_jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    def events(self, render_id: str) -> list[dict[str, Any]]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT id, render_id, state, message, created_at "
                "FROM video_render_events WHERE render_id = ? ORDER BY id",
                (render_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def _decode_project(body: str) -> VideoProject:
    data = json.loads(body)
    return _project_from_dict(data)


def _project_from_dict(data: dict[str, Any]) -> VideoProject:
    compositions = []
    for c in data.get("compositions", []):
        r = c["resolution"]
        compositions.append(
            VideoComposition(
                composition_id=c["composition_id"],
                name=c["name"],
                resolution=Resolution(r["width"], r["height"]),
                fps=c["fps"],
                duration_frames=c["duration_frames"],
                background_color=c.get("background_color", "#000000"),
                preset=CompositionPreset(c.get("preset", "youtube_landscape")),
                metadata=c.get("metadata", {}),
            )
        )

    scenes: list[VideoScene] = []
    for s in data.get("scenes", []):
        tracks = []
        for t in s.get("tracks", []):
            clips: list[VideoClip] = []
            for cl in t.get("clips", []):
                keyframes = [
                    Keyframe(
                        property=k["property"],
                        frame=k["frame"],
                        value=k["value"],
                        easing=Easing(k["easing"]),
                    )
                    for k in cl.get("keyframes", [])
                ]
                clips.append(
                    VideoClip(
                        clip_id=cl["clip_id"],
                        asset_id=cl.get("asset_id"),
                        track_id=cl["track_id"],
                        source_start_frame=cl.get("source_start_frame", 0),
                        source_end_frame=cl.get("source_end_frame"),
                        timeline_start_frame=cl.get("timeline_start_frame", 0),
                        timeline_end_frame=cl.get("timeline_end_frame"),
                        x=cl.get("x", 0.0),
                        y=cl.get("y", 0.0),
                        width=cl.get("width", 1.0),
                        height=cl.get("height", 1.0),
                        opacity=cl.get("opacity", 1.0),
                        rotation=cl.get("rotation", 0.0),
                        scale=cl.get("scale", 1.0),
                        border_radius=cl.get("border_radius", 0.0),
                        blend_mode=cl.get("blend_mode", "normal"),
                        keyframes=keyframes,
                        text_overlay=cl.get("text_overlay"),
                        source_path=cl.get("source_path"),
                    )
                )
            tracks.append(
                VideoTrack(
                    track_id=t["track_id"],
                    composition_id=t["composition_id"],
                    kind=TrackKind(t["kind"]),
                    name=t["name"],
                    z_index=t.get("z_index", 0),
                    clips=clips,
                )
            )
        ti = s.get("transition_in")
        to = s.get("transition_out")
        scenes.append(
            VideoScene(
                scene_id=s["scene_id"],
                composition_id=s["composition_id"],
                name=s["name"],
                purpose=s.get("purpose", "intro"),
                start_frame=s.get("start_frame", 0),
                duration_frames=s.get("duration_frames", 0),
                tracks=tracks,
                motion_presets=[
                    MotionPreset(
                        primitive=mp["primitive"],
                        target=mp.get("target", "scene"),
                        start_frame=mp["start_frame"],
                        end_frame=mp["end_frame"],
                        easing=Easing(mp.get("easing", "linear")),
                        parameters=mp.get("parameters", {}),
                    )
                    for mp in s.get("motion_presets", [])
                ],
                transition_in=VideoTransition(
                    transition_id=ti["transition_id"],
                    kind=ti["kind"],
                    duration_frames=ti["duration_frames"],
                ) if ti else None,
                transition_out=VideoTransition(
                    transition_id=to["transition_id"],
                    kind=to["kind"],
                    duration_frames=to["duration_frames"],
                ) if to else None,
                metadata=s.get("metadata", {}),
            )
        )

    assets: list[VideoAsset] = []
    for a in data.get("assets", []):
        assets.append(
            VideoAsset(
                asset_id=a["asset_id"],
                kind=AssetKind(a["kind"]),
                source_path=a["source_path"],
                mime_type=a["mime_type"],
                content_hash=a["content_hash"],
                width=a.get("width"),
                height=a.get("height"),
                duration_seconds=a.get("duration_seconds"),
                fps=a.get("fps"),
                metadata=a.get("metadata", {}),
            )
        )

    return VideoProject(
        project_id=data["project_id"],
        name=data["name"],
        source_project_root=data.get("source_project_root"),
        schema_version=data["schema_version"],
        compositions=compositions,
        scenes=scenes,
        assets=assets,
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        version=data["version"],
        renderer_versions=data.get("renderer_versions", {}),
        metadata=data.get("metadata", {}),
    )


__all__ = [
    "VIDEO_SCHEMA_VERSION",
    "init_video_schema",
    "content_hash",
    "VideoProjectStore",
    "VideoAssetStore",
    "VideoJobStore",
    "S_CREATED", "S_QUEUED", "S_RUNNING", "S_VALIDATING",
    "S_COMPLETED", "S_FAILED", "S_CANCELLED",
]
