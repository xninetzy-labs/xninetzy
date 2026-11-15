from __future__ import annotations

import pytest

import json
import os
import time
import uuid


def test_remotion_renderer_renders_short_video(tmp_path):
    from xninetzy.interfaces.media.video_backends.remotion import (
        RemotionBackend, REMOTION_PROJECT_ROOT,
    )

    if not REMOTION_PROJECT_ROOT.exists():
        pytest.skip("remotion runtime not installed; run scripts/setup_remotion_renderer.py")
    backend = RemotionBackend()
    if not backend.is_available():
        pytest.skip(f"remotion unavailable under {REMOTION_PROJECT_ROOT}")

    from xninetzy.context.media.video.templates import (
        TemplateContext, project_demo_template,
    )
    from xninetzy.context.media.video.models import RenderRequest
    from xninetzy.interfaces.media.video_backends.ffmpeg import probe_metadata

    ctx = TemplateContext(
        project_id=f"rt-{uuid.uuid4().hex[:6]}",
        name="Remotion render smoke",
        duration_seconds=1.0,
    )
    project = project_demo_template(ctx)
    out_path = tmp_path / "remotion.mp4"
    props_path = tmp_path / "props.json"

    request = RenderRequest(
        project_id=ctx.project_id,
        composition_id="ProjectDemo",
        project_version=1,
        output_format="mp4",
        output_path=str(out_path),
        props_path=str(props_path),
        quality="fast",
        width=project.compositions[0].resolution.width,
        height=project.compositions[0].resolution.height,
        fps=project.compositions[0].fps,
        duration_frames=project.compositions[0].duration_frames,
        max_runtime_seconds=300,
    )
    t0 = time.monotonic()
    result = backend.render(project, request)
    elapsed = time.monotonic() - t0

    assert result.renderer.value == "remotion-cpu"
    assert result.exit_code == 0
    assert os.path.isfile(out_path)
    assert result.size_bytes > 0
    assert result.size_bytes == os.path.getsize(out_path)

    meta = probe_metadata("ffprobe", str(out_path))
    assert meta["streams"][0]["codec_name"] == "h264"
    assert meta["streams"][0]["width"] > 0
    assert meta["streams"][0]["height"] > 0

    assert os.path.getsize(props_path) > 0
    props_payload = json.loads(props_path.read_text())
    assert props_payload["composition"]["composition_id"] == "ProjectDemo"
    assert len(props_payload["scenes"]) == 5

    _ = elapsed


def test_remotion_renderer_health_snapshot():
    from xninetzy.interfaces.media.video_backends.remotion import (
        RemotionBackend,
    )
    backend = RemotionBackend()
    snap = backend.health_snapshot()
    assert snap["renderer_id"] == "remotion-cpu"
    assert snap["entry_file"] == "src/index.tsx"
    assert "--disable-gpu" in snap["chromium_args"]
    assert "--no-sandbox" in snap["chromium_args"]
    if snap["available"]:
        assert snap["remotion_version"]


def test_capability_based_router_picks_remotion_when_react_required(tmp_path):
    from xninetzy.context.media.video.renderers import default_router

    router = default_router()
    available = router.available()
    chosen = router.choose(frozenset({"react_composition"}))
    if available.get("remotion-cpu"):
        assert chosen.value == "remotion-cpu"
    else:
        assert chosen.value == "ffmpeg-cpu"


def test_capability_based_router_picks_ffmpeg_for_pure_compose(tmp_path):
    from xninetzy.context.media.video.renderers import default_router

    router = default_router()
    chosen = router.choose(frozenset())
    assert chosen.value == "ffmpeg-cpu"


def test_user_override_selects_remotion_when_available():
    from xninetzy.context.media.video.models import RendererId
    from xninetzy.context.media.video.renderers import default_router

    router = default_router()
    if not router.available().get("remotion-cpu"):
        pytest.skip("remotion unavailable; override test skipped")
    chosen = router.choose(frozenset(), user_override=RendererId.REMOTION_CPU)
    assert chosen.value == "remotion-cpu"
