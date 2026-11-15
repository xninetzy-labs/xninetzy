---
name: media-video-motion
description: Deterministic motion primitives (FadeIn, SlideIn, Zoom, CameraPush, KenBurns, LowerThird, TitleCard, Callout, CodeHighlight, Typewriter) via Remotion or FFmpeg keyframes. Use to add motion graphics to a video.
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_scene_create, video_motion_apply, video_preview
  produces: motion_graph
  tier: '1'
  engine: remotion,ffmpeg
  keywords: after backed cpu effects filter for graph graphs implemented interpolated keyframe light like only react richer scenes
---

# media-video-motion

Apply keyframe-animated transform + opacity + color + blur + text to a scene. Every animation must be reproducible from the same project version + asset hashes + renderer version.

Operating procedure:

```
SCENE (target scene_id)
   ↓
CHOOSE PRIMITIVE(S) OR KEYFRAME GRAPH
   ↓
RESOLVE INTERPOLATION (linear | ease_in | ease_out | ease_in_out | cubic_bezier | spring-deterministic)
   ↓
COMPILE MOTION GRAPH (renderer-neutral)
   ↓
RENDERER ROUTING (Remotion for React/UI; FFmpeg for light motion)
   ↓
PREVIEW (cheap) vs FINAL RENDER (full)
```

Workflow:

1. The model never invents new motion primitives. Pick from the canonical set: `FadeIn, FadeOut, SlideIn, SlideOut, ScaleIn, ScaleOut, Zoom, Pan, Reveal, Typewriter, BlurIn, BlurOut, Pop, Spring (deterministic), Stagger, Highlight, Spotlight, CameraPush, CameraPull, KenBurns, LowerThird, TitleCard, Callout, CodeHighlight, BrowserFrame, DeviceFrame`.
2. Each preset is a typed dataclass in `xninetzy/context/media/video/motion/presets.py` — never invented inline. The skill references the preset name; the underlying runtime resolves it.
3. Keyframe format: `Keyframe(property=scale, time=0s, value=1.0, easing="ease_in_out")`. Properties cover `position`, `scale`, `rotation`, `opacity`, `blur`, `color`, `text_content` (for typewriter), and `clip_path`.
4. Renderer routing:
   - If scene has React/UI motion (browser frame, multi-track overlay, animated SVG) → route to **Remotion renderer** (`xninetzy/context/media/video/renderers/remotion.py`).
   - If scene has light transform + opacity on a single image/clip → route to **FFmpeg renderer** (`xninetzy/interfaces/media/video_backends/ffmpeg.py`) using a filter graph like `[i]scale=eval=frame+...:ow=..., crop=..., overlay=..., drawtext=...`.
5. Preview: call `video_preview` which uses Remotion Studio (`npx remotion studio`) when available, or renders the FFmpeg filter graph to a 5-frame contact sheet.
6. After every motion application, run `VideoQualityValidator` against the motion graph — clip overlap, property out of bounds, NaN, unsupported easing.

Output contract:

- `motion_graph_hash` — SHA-256 of the canonical JSON serialization of the motion graph.
- `render_settings` — renderer id, renderer version, fps, codec.
- An explicit `property=..., time=..., value=..., easing=...` list applied.

Failure modes:

- UNKNOWN_PRIMITIVE — reject; only canonical primitives are supported.
- NAN_OR_INF_KEYFRAME — reject the apply, return `VIDEO_MOTION_INVALID`.
- REMOTION_RUNTIME_MISSING — fall back to FFmpeg filter graph approximation; warn the user.

Negative examples:

- "Use an AI camera animation model."
- "Generate a Bezier curve that vaguely feels cinematic."
