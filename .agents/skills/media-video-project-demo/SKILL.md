---
name: media-video-project-demo
description: 'Builds a deterministic 30-second product or feature demo from a running Xninetzy project: capture key states, intro → feature → demo → result, motion and MP4 render. Use for quick product demos.'
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_project_inspect, video_project_create, video_asset_import, video_scene_create, video_motion_apply, video_render
  produces: project_demo_mp4
  tier: '1'
  engine: ffmpeg,remotion
  template: project_demo
  keywords: app applies assembles browser build camera captures cpu existing gateway highlight inspects live lower only opens push renders third timeline transition via video
---

# media-video-project-demo

Deterministic template — 30 s default, configurable. Reads the project, never invents UI states.

Operating procedure:

```
USER PROJECT ROOT
   ↓
INSPECT (entrypoints, framework, README, assets, logo)
   ↓
RUN (find run command; never modify app behaviour)
   ↓
DETECT (web = local URL; desktop = native)
   ↓
CAPTURE (browser gateway or FFmpeg x11grab)
   ↓
TEMPLATE FILL (intro / feature / demo / result)
   ↓
ASSEMBLE TIMELINE + MOTION
   ↓
RENDER + VALIDATE
```

Workflow:

1. `video_project_inspect(project_root)`:
   - read `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` to detect framework,
   - read `README.md` for product summary,
   - find `public/` for the project logo,
   - find screenshot asset paths if any (PNG/JPEG/SVG under `assets/`, `screenshots/`, `public/`),
   - detect `entrypoints` (HTTP port, desktop binary).
2. **Never modify the project** to make the video look better. Capture whatever the project actually does.
3. For **web apps**: detect `localhost`/`127.0.0.1`/<%= custom %>` URL in the README, then call `xninetzy.os.auth.browser.gateway.launch_local_browser(...)` and open the URL. Capture the running dashboard, key features, and result state. NO cloud browser.
4. For **desktop apps**: use FFmpeg x11grab + a `window=` crop. Honour exclusion windows.
5. Apply the deterministic `project_demo` template (T1):

   | Time | Section | Asset | Motion |
   |---|---|---|---|
   | 0–3 s | intro | project logo + title | FadeIn + slide-up |
   | 3–7 s | what | README summary | FadeIn |
   | 7–12 s | architecture | static screenshot | ScaleIn + CameraPush |
   | 12–22 s | running demo | captured browser segment | CameraPan + Highlight |
   | 22–27 s | result | result screenshot | Reveal |
   | 27–30 s | outro | logo + CTA | FadeOut |

6. The model may extend or compress each slot, but the section ORDER is part of the project-demo template contract.
7. Motion primitives are picked from `media-video-motion`, never invented. Camera pushes and lower thirds are typed presets.
8. Vertical/horizontal/square variants: pick the right `video_export` preset. Do not silently resize.
9. Final render MUST validate via ffprobe per `media-video-render`.

Output contract:

- `project_id` + `project_version` (the timeline is `project` v2, every render is a new version).
- A render manifest with all asset hashes, motion graph hash, renderer, renderer version.
- A `project_demo.json` describing the demo (sections, durations, asset refs, motion refs).

Failure modes:

- NO_RUNNABLE_ENTRY — return `video_project_inspect` result with `entrypoints=[]` and ask the user to start the project first. Do NOT spawn a server.
- MISSING_LOGO — fall back to a deterministic text-only intro; do not fabricate graphics.
- GPU_ENCODER_REQUESTED — refuse.

Negative examples:

- "Generate a synthetic UI screen."
- "Use Veo to fill in the dashboard."
