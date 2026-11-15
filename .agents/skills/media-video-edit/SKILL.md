---
name: media-video-edit
description: 'Deterministic FFmpeg editing of existing clips: trim, concat, crossfade, text overlay, scale and SRT/VTT captions; no AI transcription or auto-cut. Use to edit existing footage.'
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_clip_trim, video_clip_add, video_transition_add, video_text_add, video_audio_add
  produces: edited_video_segment
  tier: '1'
  engine: ffmpeg
  keywords: add apply caption cpu filter graphs image import mov mp4 only operates primitives segments transition video webm with
---

# media-video-edit

Apply deterministic editing operations to existing video assets. Every operation is a typed argument; never pass a user-supplied raw shell string.

Operating procedure:

```
ASSETS (already imported via video_asset_import)
   ↓
EDIT OPS (typed)
   ↓
COMPILED FILTER GRAPH (deterministic)
   ↓
ffmpeg exec (CPU)
   ↓
NEW asset_id
```

Workflow:

1. Resolve the source `asset_id`s from the media_store. Reject if any asset is missing, corrupt, or > `VIDEO_MAX_INPUT_SIZE_MB`.
2. Accept **typed edit ops only**:
   - `TRIM { asset_id, start_seconds, end_seconds }`
   - `CONCAT { asset_ids: [...] }` — if A/V lengths differ, the longest wins; intermediate segments are joined by `concat` demuxer (no re-encode when `copy` is allowed).
   - `TRANSITION { a_asset_id, b_asset_id, transition: crossfade | dip_to_black, duration_seconds }` — uses `xfade` filter.
   - `TEXT { asset_id, text, font_id, x, y, font_size, color, background, opacity, start_seconds, end_seconds }` — `drawtext` filter, CPU drawtext path.
   - `SCALE { asset_id, width, height, mode: fit | fill | stretch }` — `scale`, with `pad` if `fit` and `setsar`.
   - `AUDIO { asset_id, music_path, mode: replace | mix, gain_db, fade_in_seconds, fade_out_seconds }` — `amerge` + `volume` + `afade`.
3. Do **NOT** auto-transcribe. Captioning requires a supplied SRT/VTT file. If the user asks to transcribe, reply that audio transcription is out of scope for this skill and offer `media_read_audio` from the existing media toolset.
4. After every op, re-run ffprobe to verify duration + streams. Save the source `asset_id` and op hash to the timeline asset manifest.
5. Cache the rendered segment on a render-fingerprint hash to avoid re-running the same op on retry.

Output contract:

- New `asset_id(s)` with codec, duration, width, height, fps, size, content_hash.
- A `timeline_event.jsonl` line per op (typed).

Failure modes:

- INVALID_CLIP_BOUNDARY — return `VIDEO_DURATION_INVALID` or `VIDEO_INPUT_NOT_READABLE`.
- ENCODER_GPU_REQUESTED — refuse; CPU only.
- TIMELINE_NON_DETERMINISTIC — re-run with explicit `setpts=PTS-STARTPTS` and `asetpts=PTS-STARTPTS` to enforce deterministic frame ordering.

Negative examples:

- "Use Whisper to add captions."
- "Auto-cut the boring parts."
