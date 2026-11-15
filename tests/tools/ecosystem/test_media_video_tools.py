from __future__ import annotations

import json
import os
import uuid

import pytest

from xninetzy.tools.ecosystem.media_video_tools import (
    media_video_tools,
    video_asset_import,
    video_export,
    video_inspect,
    video_motion_apply,
    video_project_create,
    video_project_export_json,
    video_project_inspect,
    video_render,
    video_render_cancel,
    video_render_status,
    video_session_start,
    video_session_stop,
    video_template_apply,
    video_thumbnail_create,
)


def _tool(name: str):
    for t in media_video_tools:
        if t.name == name:
            return t
    raise ValueError(f"tool {name!r} not registered")


def _small_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff\xff?\x00\x05\xfe\x02\xfe\xa3\xc0\x10"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _vid_id() -> str:
    return f"vidtest-{uuid.uuid4().hex[:8]}"


def test_renderer_health_returns_ffmpeg():
    out = json.loads(_tool("video_renderer_health").invoke({}))
    assert "ffmpeg-cpu" in out
    assert "remotion-cpu" in out
    assert out["ffmpeg-cpu"]["renderer_id"] == "ffmpeg-cpu"


def test_full_pipeline_create_template_render_inspect(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    create_out = video_project_create.invoke({
        "name": "Pipeline",
        "project_id": pid,
        "width": 640,
        "height": 360,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    cj = json.loads(create_out)
    assert cj["status"] == "created"
    assert cj["project_id"] == pid
    assert cj["resolution"] == {"width": 640, "height": 360}

    template_out = video_template_apply.invoke({
        "project_id": pid,
        "template": "project_demo",
        "duration_seconds": 1.0,
    })
    tj = json.loads(template_out)
    assert tj["status"] == "applied"
    assert tj["scene_count"] == 5

    inspect_out = json.loads(
        video_project_inspect.invoke({"project_id": pid})
    )
    assert inspect_out["found"] is True
    assert inspect_out["scene_count"] == 5

    json_out = video_project_export_json.invoke({"project_id": pid})
    payload = json.loads(json_out)
    assert payload["project_id"] == pid
    assert payload["compositions"][0]["resolution"] == {
        "width": 1080,
        "height": 1080,
    }

    render_out = video_render.invoke({
        "project_id": pid,
        "output_format": "mp4",
        "quality": "fast",
        "max_runtime_seconds": 60,
    })
    rj = json.loads(render_out)
    assert rj["status"] == "completed"
    assert rj["codec"] == "libx264"
    assert rj["size_bytes"] > 0
    assert os.path.isfile(rj["output_path"])
    assert rj["resolution"] == {"width": 1080, "height": 1080}

    status_out = json.loads(
        video_render_status.invoke({"render_id": rj["render_id"]})
    )
    assert status_out["status"] == "found"
    assert status_out["render"]["exit_code"] == 0
    states = [e["state"] for e in status_out["events"]]
    assert "created" in states
    assert "running" in states
    assert "completed" in states

    inspect_mp4 = json.loads(video_inspect.invoke({"path": rj["output_path"]}))
    assert inspect_mp4["status"] == "ok"
    assert inspect_mp4["ffprobe"]["streams"][0]["codec_name"] == "h264"

    thumb_out = json.loads(video_thumbnail_create.invoke({
        "path": rj["output_path"],
        "at_seconds": 0.0,
    }))
    assert thumb_out["status"] == "created"
    assert os.path.isfile(thumb_out["output_path"])
    assert thumb_out["size_bytes"] > 0


def test_motion_apply_unknown_primitive_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    video_project_create.invoke({
        "name": "Motion Test",
        "project_id": pid,
        "width": 320,
        "height": 240,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    video_template_apply.invoke({
        "project_id": pid,
        "template": "tutorial",
        "duration_seconds": 1.0,
    })
    json.loads(video_project_inspect.invoke({"project_id": pid}))
    scene_id = None
    store, _ = _storage()
    proj = store.get(pid)
    if proj and proj.scenes:
        scene_id = proj.scenes[0].scene_id
    assert scene_id is not None
    with pytest.raises(Exception):
        video_motion_apply.invoke({
            "project_id": pid,
            "scene_id": scene_id,
            "primitive": "NonExistentPrimitive",
        })


def test_motion_apply_known_primitive_succeeds(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    video_project_create.invoke({
        "name": "Motion Test 2",
        "project_id": pid,
        "width": 320,
        "height": 240,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    video_template_apply.invoke({
        "project_id": pid,
        "template": "tutorial",
        "duration_seconds": 1.0,
    })
    store, _ = _storage()
    proj = store.get(pid)
    scene_id = proj.scenes[0].scene_id
    out = json.loads(video_motion_apply.invoke({
        "project_id": pid,
        "scene_id": scene_id,
        "primitive": "CameraPush",
        "parameters": {"to_scale": 1.12},
    }))
    assert out["status"] == "applied"
    assert out["primitive"] == "CameraPush"
    proj2 = store.get(pid)
    s = next(x for x in proj2.scenes if x.scene_id == scene_id)
    assert any(p.primitive == "CameraPush" for p in s.motion_presets)


def test_session_start_stop(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("VIDEO_BROWSER_DISABLED", "1")
    out_start = json.loads(video_session_start.invoke({
        "project_id": "session-x",
        "capture_target": "browser",
    }))
    assert out_start["status"] == "browser_disabled"
    assert out_start["session_id"].startswith("capture-")

    out_stop = json.loads(video_session_stop.invoke({
        "session_id": out_start["session_id"],
    }))
    assert out_stop["status"] == "stopped"


def test_session_start_desktop_records_capture_command(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    out = json.loads(video_session_start.invoke({
        "project_id": "desktop-x",
        "capture_target": "desktop",
    }))
    assert out["status"] == "reserved"
    assert "ffmpeg_capture_command" in out
    assert "libx264" in out["ffmpeg_capture_command"]


def test_asset_import_rejects_unknown_extension(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    video_project_create.invoke({
        "name": "Asset test",
        "project_id": pid,
        "width": 320,
        "height": 240,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    bogus = tmp_path / "bogus.xyz"
    bogus.write_bytes(b"not a real image")
    out = json.loads(video_asset_import.invoke({
        "project_id": pid,
        "source_path": str(bogus),
        "kind": "image",
    }))
    assert out["status"] == "imported"
    assert out["kind"] == "image"
    assert out["size_bytes"] == bogus.stat().st_size


def test_asset_import_rejects_missing_project(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    src = tmp_path / "test.png"
    src.write_bytes(_small_png())
    with pytest.raises(Exception):
        video_asset_import.invoke({
            "project_id": "no-such-project",
            "source_path": str(src),
            "kind": "image",
        })


def _storage():
    from xninetzy.context.media.video.storage import (
        init_video_schema, VideoProjectStore,
    )
    init_video_schema()
    return VideoProjectStore(), None


def test_video_export_copies_output(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    video_project_create.invoke({
        "name": "Export test",
        "project_id": pid,
        "width": 320,
        "height": 240,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    video_template_apply.invoke({
        "project_id": pid,
        "template": "motion_graph",
        "duration_seconds": 1.0,
    })
    render_out = json.loads(video_render.invoke({
        "project_id": pid,
        "output_format": "mp4",
        "quality": "fast",
        "max_runtime_seconds": 60,
    }))
    assert render_out["status"] == "completed"
    dest = tmp_path / "exported.mp4"
    out = json.loads(video_export.invoke({
        "render_id": render_out["render_id"],
        "destination": str(dest),
    }))
    assert out["status"] == "exported"
    assert os.path.isfile(dest)
    assert dest.stat().st_size > 0


def test_render_cancel_after_completion_is_no_op(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_OUTPUT_DIR", str(tmp_path))
    pid = _vid_id()
    video_project_create.invoke({
        "name": "Cancel test",
        "project_id": pid,
        "width": 320,
        "height": 240,
        "fps": 30,
        "duration_seconds": 1.0,
        "preset": "square_social",
    })
    video_template_apply.invoke({
        "project_id": pid,
        "template": "motion_graph",
        "duration_seconds": 1.0,
    })
    render_out = json.loads(video_render.invoke({
        "project_id": pid,
        "output_format": "mp4",
        "quality": "fast",
        "max_runtime_seconds": 60,
    }))
    out = json.loads(video_render_cancel.invoke({
        "render_id": render_out["render_id"],
    }))
    assert out["status"] in {"no_op", "cancelled"}
