from __future__ import annotations

from typing import Any, Callable

from xninetzy.context.media.video.models import (
    RenderRequest,
    RenderResult,
    RendererId,
    VideoProject,
)
from xninetzy.context.media.video.renderers.base import (
    RendererBackend,
    select_renderer,
)


CapabilityProbe = Callable[[RendererId], bool]


class RendererRouter:

    def __init__(
        self,
        *,
        backends: dict[RendererId, RendererBackend],
        capability_probe: CapabilityProbe | None = None,
    ) -> None:
        self._backends = dict(backends)
        self._probe = capability_probe or (
            lambda rid: self._backends.get(rid) is not None
            and self._backends[rid].is_available()
        )

    def available(self) -> dict[RendererId, bool]:
        return {rid: bool(self._probe(rid)) for rid in self._backends}

    def choose(
        self,
        required_capabilities: frozenset[str],
        *,
        user_override: RendererId | None = None,
    ) -> RendererId:
        avail = self.available()
        if user_override is not None and user_override in self._backends:
            if avail.get(user_override, False):
                return user_override
            return RendererId.UNKNOWN
        chosen, _ = select_renderer(required_capabilities, avail, user_override)
        return chosen

    def dispatch(
        self,
        project: VideoProject,
        request: RenderRequest,
        *,
        required_capabilities: frozenset[str] = frozenset(),
        user_override: RendererId | None = None,
    ) -> RenderResult:
        chosen = self.choose(
            required_capabilities, user_override=user_override
        )
        backend = self._backends.get(chosen)
        if backend is None or not backend.is_available():
            raise RuntimeError(
                f"renderer {chosen!r} selected but not available; "
                f"available={self.available()}"
            )
        return backend.render(project, request)

    def cancel(self, render_id: str) -> bool:
        for backend in self._backends.values():
            try:
                if backend.cancel(render_id):
                    return True
            except Exception:
                continue
        return False

    def health_snapshot(self) -> dict[str, Any]:
        return {rid.value: b.health_snapshot() for rid, b in self._backends.items()}


def default_router(
    *,
    ffmpeg: "RendererBackend | None" = None,
    remotion: "RendererBackend | None" = None,
) -> RendererRouter:
    from xninetzy.interfaces.media.video_backends.ffmpeg import FFmpegRenderer
    from xninetzy.interfaces.media.video_backends.remotion import RemotionBackend

    backends: dict[RendererId, RendererBackend] = {}
    if ffmpeg is None:
        ffmpeg = FFmpegRenderer()
    if remotion is None:
        remotion = RemotionBackend()
    backends[RendererId.FFMPEG_CPU] = ffmpeg
    backends[RendererId.REMOTION_CPU] = remotion
    return RendererRouter(backends=backends)


__all__ = [
    "RendererRouter",
    "CapabilityProbe",
    "default_router",
]
