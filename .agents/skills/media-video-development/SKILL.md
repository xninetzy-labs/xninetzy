---
name: media-video-development
description: Builds a development-journey video (problem → implementation → failure → debugging → resolution → demo) from existing .dev-video session artifacts. Use for dev-story videos.
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_session_start, video_session_stop, video_asset_import, video_timeline_build, video_scene_create, video_motion_apply, video_render
  produces: development_journey_mp4
  tier: '1'
  engine: ffmpeg+remotion
  keywords: build capture demonstration deterministic events json jsonl keystroke only prior reuses sections sessions storyboard xninetzy
license: Xninetzy-Source-Available-2.2.0
---

# media-video-development

Reuse the prior Xninetzy Development Video artifacts (`session.json`, `events.jsonl`, `storyboard.json`) under `.dev-video/` instead of inventing content.

Operating procedure:

```
USER PROJECT (with .dev-video/ artifacts)
   ↓
READ session.json + events.jsonl (events only — no keystrokes)
   ↓
READ storyboard.json (highlights)
   ↓
BUILD TIMELINE (deterministic by event timestamps)
   ↓
BUILD SCENES (problem / impl / failure / debug / resolution / demo)
   ↓
APPLY MOTION (typed primitives)
   ↓
RENDER + VALIDATE
```

Workflow:

1. Event schema (typed, JSONL):
   - `{ ts, type, status, source, meta }` where `type ∈ {shell, file_change, git, build, test, process}`.
   - **NEVER** include raw keystroke sequences, password / token / secret values, full process args containing secrets, or screenshot pixels that contain credential surfaces.
   - Redaction policy: any `meta` field matching `(?i)(?:api[_ -]?key|password|passwd|secret|token|cookie|...)` must be hash-redacted before persistence.
2. The `storyboard.json` already encodes the highlights; the video timeline is a typed projection of `events.jsonl` + `storyboard.json`. If neither exists, fall back to `media-video-project-demo`.
3. Sections (deterministic order, durations configurable):
   - **Problem** — first failed test or first committed file before fix.
   - **Implementation** — diff range with caption overlay (`drawtext`).
   - **Failure** — capture the error message from `events.jsonl` (redacted) with a `Highlight` motion primitive.
   - **Debugging** — diff, log lines, terminal output.
   - **Resolution** — green test, successful build.
   - **Demonstration** — running app captured via the existing browser gateway.
4. Each section opens with a real event marker (the timestamp + a one-line summary). The model MUST NOT add narration the source does not support; it lists what is missing.
5. Audio: only user-supplied voiceover / music. NO TTS, NO AI music, NO auto-transcription.
6. Render per `media-video-render`.

Output contract:

- `development_journey.json` with section anchors + asset references + redaction_status.
- A render manifest per `media-video-render`.

Failure modes:

- MISSING_ARTIFACTS — fall through to `media-video-project-demo`.
- RAW_SECRET_DETECTED — abort the affected scene, append `redaction_status="skipped-secret-block"`.
- NO_BROWSER_SESSION_AVAILABLE — show static code-diff scenes only.

Negative examples:

- "Capture every keystroke I typed today."
- "Auto-narrate the diff." (no TTS)
