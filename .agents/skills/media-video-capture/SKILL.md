---
name: media-video-capture
description: Captures a running project (browser tab, local web app, monitor, terminal) into a deterministic video asset via the browser gateway and CPU FFmpeg; never records keystrokes or secrets. Use for screen-capture footage.
metadata:
  scope: media
  intent_class: MEDIA
  consumes: xninetzy browser gateway, ffmpeg x11grab/avfoundation/gdigrab, xninetzy os jobs service
  produces: captured_video_segment
  tier: '1'
  engine: ffmpeg,cpu-capture
  keywords: desktop existing nvenc only out passwords qsv scope using windows xninetzy
---

# media-video-capture

Operate capture through the existing Xninetzy primitives, never through an ad-hoc browser daemon or untyped shell.

Operating procedure:

```
REQUEST
   ↓
DETECT SOURCE (browser tab / desktop monitor / specific window)
   ↓
VERIFY AUTH BOUNDARY (browser = local-owner session, no remote)
   ↓
LAUNCH OR REUSE BROWSER SESSION (xninetzy/os/auth/browser/gateway.py)
   ↓
CAPTURE (browser CDP screencast OR ffmpeg x11grab)
   ↓
SEGMENT & ENCODE (libx264 / libx265 / libvpx-vp9 — CPU)
   ↓
STORE (xninetzy/interfaces/media/media_store.py + .dev-video/raw/)
   ↓
RETURN asset_id
```

Workflow:

1. If the capture target is a **web app** — call `xninetzy.os.auth.browser.gateway.launch_local_browser(session_id=..., owner=..., headless=True)` to obtain a Playwright persistent context. Use the existing local-owner profile under `~/.local/share/xninetzy/auth/profiles/<owner>/<session>`. NEVER start a fresh Playwright instance outside this gateway.
2. If the capture target is a **desktop monitor** — invoke `ffmpeg -f x11grab -video_size WxH -framerate N -i :0.0+X,Y out.mp4` on Linux, `-f avfoundation` on macOS, `-f gdigrab` on Windows. CPU encoder is mandatory: `-c:v libx264 -preset medium -crf 23`. Reject `-c:v nvenc`, `-c:v h264_nvenc`, `-c:v h264_qsv`, `-c:v h264_amf`, `-c:v h264_vaapi`, `-c:v vt_h264`, or any GPU-accelerated encoder.
3. If the capture target is a **specific browser tab** — keep the existing Playwright session open, attach Page.captureScreenshot via CDP, pipe PNGs to `ffmpeg -f image2pipe -framerate N -i - out.mp4`. Do not screenshot cookie or credential surfaces.
4. Honour exclusion windows: if the user names an excluded app (password manager, banking, keychain, SSH vault), record nothing and return `VIDEO_CAPTURE_UNAVAILABLE`.
5. Segment by event boundary (user-pressed `marker`, detected DOM change, fixed time window). Default segment length: 30 s.
6. Detect display backend: `X11` via `$DISPLAY`, Wayland via `XDG_SESSION_TYPE=wayland` → use `pipewire` source, macOS via `avfoundation`. Branch on the result; do not assume X11 on Linux.

Output contract:

- `asset_id` (content-addressable hash).
- `path` (under `.dev-video/raw/<session_id>/segment_NNN.mp4` or media_store).
- `codec` (`h264` | `vp9` | ...), `width`, `height`, `fps`, `duration_seconds`, `display_backend`.
- `redaction_status` (`clean` | `redacted` | `skipped-secret-window`).
- `events.jsonl` with safe event markers (no raw shell args, no keystrokes).

Failure modes:

- BROWSER_BACKEND_OFFLINE — fall back to FFmpeg x11grab if the source is the desktop; otherwise return `VIDEO_CAPTURE_UNAVAILABLE`.
- SECRET_PHRASE_DETECTED — abort capture, append a placeholder segment with `redaction_status="skipped-secret-window"`. Do NOT store the raw frames.
- GPU_ENCODER_REQUESTED — refuse; remain CPU only.
- REMOTE_BROWSER_REQUESTED — refuse unless the owner explicitly arms a CDP endpoint via env var.

Negative examples (must NOT trigger capture):

- "Record me typing my password."
- "Capture my banking tab."
- "Use NVENC to encode this segment faster." (CPU only)
