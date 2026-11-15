---
name: media-video-root
description: 'Entry point of the deterministic CPU-only video subsystem: routes requests to make, edit or render video from project assets, captures, images, code or clips to the right media-video-* skill; no generative video models. Use for any video request.'
metadata:
  scope: media
  intent_class: MEDIA
  consumes: media-video-capture, media-video-edit, media-video-motion, media-video-render, media-video-project-demo, media-video-tutorial, media-video-development
  produces: video_project_plan
  tier: '0'
  engine: ffmpeg+remotion
  keywords: activates audio based creator dispatcher editor existing integration intent involves kling mcp model one pika producing rendering runway screen screenshots skills sora sub svg transforming user veo whenever xninetzy
license: Xninetzy-Source-Available-2.2.0
---
# media-video-root

Dispatch the request to exactly one of: `media-video-capture`, `media-video-edit`, `media-video-motion`, `media-video-render`, `media-video-project-demo`, `media-video-tutorial`, `media-video-development`. Never duplicate or invent sub-skills.

Operating procedure:

```
USER REQUEST
   ↓
CLASSIFY INTENT
   ↓
SELECT ONE SUB-SKILL
   ↓
DELEGATE
   ↓
PRODUCE VIDEO PROJECT (deterministic)
```

Routing rules — pick the FIRST matching rule, do not stack:

| Trigger phrases (non-exhaustive) | Sub-skill |
|---|---|
| "record my project" / "screen capture" / "capture browser" / "record window" | `media-video-capture` |
| "trim" / "cut" / "concat" / "merge" / "add transition" / "caption this clip" / "subtitle" | `media-video-edit` |
| "animate" / "motion" / "zoom in" / "fade in" / "camera push" / "lower third" / "title card" / "Ken Burns" / "after effects-style" | `media-video-motion` |
| "render" / "export MP4" / "WebM" / "produce the final video" | `media-video-render` |
| "make a product demo from my project" / "30-second showcase of my running app" / "polished demo of the running project" | `media-video-project-demo` |
| "tutorial" / "how-to" / "step-by-step walkthrough" / "explain how to use" | `media-video-tutorial` |
| "turn my coding session into a video" / "development journey" / "show what I built" / "demo the build process" | `media-video-development` |

If the request involves multiple stages, decompose into a DAG but always pick exactly one entry-point sub-skill at the top of the DAG. The DAG may then transitively load capture → edit → motion → render.

Workflow:

1. Confirm the user's intent in one sentence. Ask only when the trigger phrases above do not match any sub-skill — otherwise the routing is deterministic.
2. Load the matched sub-skill via `xninetzy_skill_get(name)`.
3. Pop the matching `video_*` MCP tool surface (see the sub-skill for the exact tool list). Do NOT expose unrelated MCP tools (career, research, academic) to a video task.
4. Reuse existing Xninetzy primitives (browser gateway `xninetzy/os/auth/browser/gateway.py`, jobs service `xninetzy/os/jobs/`, media_store `xninetzy/interfaces/media/media_store.py`, capability graph `xninetzy/context/capability_graph/`). NEVER create a second registry, queue, or router.
5. Final render MUST go through `video_render` (RiskClass.WRITE). No FINAL gate; no approval-required.
6. Validate the rendered MP4 via ffprobe — `file exists AND size > 0 AND container valid AND duration > 0 AND video stream present`. Do NOT treat a non-zero file as success.

Output contract:

- One selected sub-skill (and optional DAG).
- Sequence of `video_*` MCP tool calls.
- A render-manifest listing `project_version`, `renderer` (`ffmpeg` | `remotion`), `renderer_version`, `asset_hashes`, `motion_graph_hash`, `timeline_hash`, `render_settings`.

Failure modes:

- AMBIGUOUS_INTENT — fall through to `media-video-edit` if uncertain, not a random guess.
- MISSING_PROJECT — surface `video_project_create` instead of fabricating assets.
- MISSING_BROWSER_SESSION — fall back to manual file / image import, do not spawn a fresh browser session silently.
- GENERATIVE_REQUEST_DETECTED — reject prompts asking for Veo / Sora / Runway / Kling / Pika; reply with one sentence explaining Xninetzy only does deterministic video.

Negative examples (must NOT route here):

- "Generate a synthetic 30-second ad clip."
- "Use Sora to spin up an intro."
- "Translate this document into Indonesian." (not a video task)
- "Find React internships." (career, not media)
