from __future__ import annotations

from xninetzy.context.media.video.storage import _project_from_dict


def test_project_decoder_restores_track_and_keyframes():
    project = _project_from_dict({
        "project_id": "synthetic-project", "name": "fixture", "created_at": "2026-11-10",
        "updated_at": "2026-11-10", "schema_version": "1", "version": 1,
        "compositions": [{"composition_id": "composition", "name": "fixture",
                          "resolution": {"width": 640, "height": 360},
                          "fps": 30, "duration_frames": 30}],
        "scenes": [{
            "scene_id": "scene", "composition_id": "composition", "name": "fixture",
            "tracks": [{
                "track_id": "track", "composition_id": "composition", "kind": "video",
                "name": "fixture", "clips": [{
                    "clip_id": "clip", "track_id": "track", "asset_id": "synthetic-asset",
                    "keyframes": [{"property": "opacity", "frame": 0, "value": 0.5,
                                   "easing": "linear"}],
                }],
            }],
        }],
    })
    track = project.scenes[0].tracks[0]
    assert track.track_id == "track"
    assert track.clips[0].keyframes[0].value == 0.5
