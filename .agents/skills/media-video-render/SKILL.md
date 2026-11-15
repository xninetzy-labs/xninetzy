---
name: media-video-render
description: Renders a VideoProject to MP4/WebM with Remotion or FFmpeg, schedules long renders as jobs and validates output with ffprobe. Use for the final render step.
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_render, video_render_status, video_render_cancel, video_inspect, video_export
  produces: rendered_mp4
  tier: '1'
  engine: ffmpeg,remotion
  keywords: before composition concat declaring deterministic engine existing file heavy motion mux react rendered scenes selection service success through trim via xninetzy
---

# media-video-render

Drive every render through the existing job service. Never block the MCP loop on a long-running render. A render is `CREATED → QUEUED → RUNNING → VALIDATING → COMPLETED` or `FAILED | CANCELLED | EXPIRED`.

Operating procedure:

```
PROJECT + COMPOSITION
   ↓
RECEIVE render_id (planning phase)
   ↓
RENDERER ROUTING (capability-based)
   ↓
SCHEDULE JOB (xninetzy/os/jobs/service.py)
   ↓
EXECUTE (CPU, bounded timeout)
   ↓
VALIDATE (ffprobe)
   ↓
ARTIFACT (video_export finalizes)
```

Workflow:

1. Renderer selection is **capability-driven**, not LLM-defaulted:
   - if `motion_graph_kind ∈ {react, ui-animation, multi-track-overlay}` → `Remotion renderer`
   - else if `motion_graph_kind ∈ {image_transform, single_clip_concat, mux}` → `FFmpeg renderer`
   - else → `FFmpeg renderer` (cheaper)
2. The Remotion renderer writes a deterministic React composition under `~/.local/share/xninetzy/video/remotion/<project_slug>/` and invokes `npx remotion render <composition-id> <out.mp4> --props=<json>`. Chromium runs with `--no-sandbox --disable-gpu --disable-software-rasterizer` to enforce CPU rendering.
3. The FFmpeg renderer composes the filter graph via the typed builder at `xninetzy/interfaces/media/video_backends/ffmpeg.py`. Encode with `libx264 -preset medium -crf 23` (CPU) or `libvpx-vp9` (CPU).
4. Schedule via `JobStore` (claim / lease / crash recovery). If the worker SIGKILLs mid-render, the lease expires and the job is re-queued. Idempotency: the same `project_version + renderer + assets + motion_graph + render_settings` always produces the same output.
5. After render, run the `VideoQualityValidator`:
   - file exists, size > 0,
   - ffprobe returns duration > 0, codec valid, video stream present, audio stream present when expected,
   - container parses,
   - resolution matches composition,
   - fps matches composition.
6. `video_export` produces the final deliverable. Default presets: `youtube_landscape (1920x1080, 30 fps, libx264)`, `shorts_vertical (1080x1920, 30 fps, libx264)`, `instagram_vertical (1080x1920, 30 fps, libx264)`, `square_social (1080x1080, 30 fps, libx264)`, `presentation (1920x1080, 30 fps, libx264)`. Do not silently downgrade.
7. Cache by render-fingerprint. Identical deterministic request → return existing artifact, do not re-render.

Output contract:

- `render_id`, `project_id`, `project_version`.
- `artifact_id` + `path` + `duration_seconds` + `resolution` + `fps` + `codec` + `size_bytes` + `content_hash`.
- `render_manifest` JSON listing renderer + version + timeline_hash + motion_graph_hash + asset_hashes + render_settings + created_at.

Failure modes:

- RENDER_TIMEOUT — schedule a re-render with the same fingerprint, do not retry in-process.
- RENDER_VALIDATION_FAIL — return `VIDEO_OUTPUT_INVALID`; do NOT return `render_id` of an invalid file.
- GPU_ENCODER_REQUESTED — refuse, no final video.

Negative examples:

- "Use NVENC to speed up the export." (CPU only)
- "Render and skip ffprobe validation." (never skip)
- "If the render fails, return the partial file." (never partial success)
