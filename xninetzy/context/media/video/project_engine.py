"""VideoProjectEngine: high-level orchestration over the domain model.

Handles create / inspect / version / mutation with idempotent storage.
Runs in the context layer (NO network, NO subprocess). All binary
work is delegated to ``xninetzy.interfaces.media.video_backends.*``
via ``xninetzy.context.media.video.renderers.*``.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from xninetzy.context.media.video.models import (
    CompositionPreset,
    Resolution,
    VideoAsset,
    VideoComposition,
    VideoProject,
    VideoScene,
)
from xninetzy.context.media.video.storage import (
    VideoAssetStore,
    VideoProjectStore,
    content_hash,
    init_video_schema,
)
from xninetzy.context.media.video.templates import TemplateContext


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class VideoProjectEngine:

    def __init__(
        self,
        *,
        project_store: VideoProjectStore | None = None,
        asset_store: VideoAssetStore | None = None,
    ) -> None:
        init_video_schema()
        self._projects = project_store or VideoProjectStore()
        self._assets = asset_store or VideoAssetStore()

    def create_composition(
        self,
        *,
        name: str,
        width: int,
        height: int,
        fps: int,
        duration_seconds: float,
        preset: CompositionPreset = CompositionPreset.YOUTUBE_LANDSCAPE,
        background_color: str = "#000000",
    ) -> VideoComposition:
        return VideoComposition(
            composition_id=_slug("comp"),
            name=name,
            resolution=Resolution(width, height),
            fps=fps,
            duration_frames=int(duration_seconds * fps),
            preset=preset,
            background_color=background_color,
        )

    def create_project(
        self,
        *,
        project_id: str | None = None,
        name: str,
        source_project_root: str | None = None,
        composition: VideoComposition,
        metadata: dict[str, Any] | None = None,
    ) -> VideoProject:
        pid = project_id or _slug("proj")
        now = _now_iso()
        project = VideoProject(
            project_id=pid,
            name=name,
            source_project_root=source_project_root,
            schema_version="1",
            compositions=[composition],
            scenes=[],
            assets=[],
            created_at=now,
            updated_at=now,
            version=1,
            metadata=dict(metadata or {}),
        )
        self._projects.upsert(project)
        return project

    def import_asset(self, project_id: str, asset: VideoAsset) -> str:
        if not self._projects.get(project_id):
            raise ValueError(f"unknown project_id {project_id!r}")
        self._assets.upsert(project_id, asset)
        return asset.content_hash

    def add_scene(self, project_id: str, scene: VideoScene) -> VideoProject:
        project = self._projects.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        if any(s.scene_id == scene.scene_id for s in project.scenes):
            raise ValueError(f"scene_id {scene.scene_id!r} already exists")
        updated = VideoProject(
            project_id=project.project_id,
            name=project.name,
            source_project_root=project.source_project_root,
            schema_version=project.schema_version,
            compositions=project.compositions,
            scenes=project.scenes + [scene],
            assets=project.assets,
            created_at=project.created_at,
            updated_at=_now_iso(),
            version=project.version + 1,
            renderer_versions=project.renderer_versions,
            metadata=project.metadata,
        )
        self._projects.upsert(updated)
        return updated

    def build_from_template(
        self,
        template_fn,
        ctx: TemplateContext,
    ) -> VideoProject:
        project = template_fn(ctx)
        self._projects.upsert(project)
        return project

    def inspect(self, project_id: str) -> dict[str, Any]:
        project = self._projects.get(project_id)
        if project is None:
            return {"found": False, "project_id": project_id}
        return {
            "found": True,
            "project_id": project.project_id,
            "name": project.name,
            "version": project.version,
            "source_project_root": project.source_project_root,
            "schema_version": project.schema_version,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "composition_count": len(project.compositions),
            "scene_count": len(project.scenes),
            "asset_count": len(project.assets),
            "total_duration_seconds": project.compositions[0].duration_seconds()
                if project.compositions else 0.0,
            "project_hash": content_hash(project.to_json()),
        }

    def export_video_project_json(self, project_id: str) -> str:
        project = self._projects.get(project_id)
        if project is None:
            raise ValueError(f"unknown project_id {project_id!r}")
        return project.to_json()


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


__all__ = ["VideoProjectEngine"]
