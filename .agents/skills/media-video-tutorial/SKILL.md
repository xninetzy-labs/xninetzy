---
name: media-video-tutorial
description: Builds a deterministic coding tutorial video from a codebase and screenshots (hook → context → steps → result → summary) with code highlighting; never generates code or transcribes audio. Use for tutorial videos.
metadata:
  scope: media
  intent_class: MEDIA
  consumes: video_scene_create, video_motion_apply, video_text_add, video_render
  produces: tutorial_mp4
  tier: '1'
  engine: ffmpeg,remotion
  template: tutorial
  keywords: auto build cpu highlights only step syntax typed user via
---

# media-video-tutorial

Deterministic template. Every step is a typed scene with explicit asset references. The model MUST NEVER invent screenshots, code, or quoted lines that do not exist in the source material.

Operating procedure:

```
USER REQUEST (tutorial goal)
   ↓
INGEST (codebase path OR supplied snippets)
   ↓
INSPECT FACTS (entrypoints, key files, package list, README claim)
   ↓
PLAN STEPS (3–7 typed steps)
   ↓
SOURCE SCREENSHOTS / CLIPS per step (via browser gateway if the app runs)
   ↓
ASSEMBLE TIMELINE (deterministic)
   ↓
RENDER + VALIDATE
```

Workflow:

1. The tutorial template has the following fixed sections, in order:
   - **Hook** (≤3 s) — frame one fact from the source (e.g., a real metric or a real filename).
   - **Context** (5–10 s) — what the project is, who it's for. Pulled from the README / docstrings, not invented.
   - **Step 1**, **Step 2**, ... (10–25 s each) — each step is a typed scene that references one or more assets. Step assets are real screenshots / real file outputs.
   - **Result** (3–10 s) — measurable outcome from the source (test passes, deploy succeeds, etc.), or a final screenshot of the finished UI.
   - **Summary** (≤5 s) — recap of facts.
2. Code annotation: highlight a real line range (file + line_number + character_range). The annotation is rendered via `CodeHighlight` motion primitive + `drawtext` (FFmpeg) or a syntax-highlight React component (Remotion). NEVER auto-generate code.
3. Manual captions may be supplied as SRT/VTT; auto-transcription is out of scope.
4. Audio: user-supplied voiceover and/or background music. No TTS, no AI music generation.
5. `video_text_add` parameters are explicit: `{ scene_id, text, font, font_size, color, background, x, y, start_seconds, end_seconds, easing }`.
6. Render the tutorial via `media-video-render`. Validation per ffprobe.

Output contract:

- `tutorial.json` listing steps with typed asset references.
- A render manifest per `media-video-render`.

Failure modes:

- MISSING_FACTS — return `tutorial.json` with `facts=[]` and ask the user to confirm rather than fabricate.
- NO_RUNNABLE_CODEBASE — quote real files via `read_file`; never generate.
- OUT_OF_SCOPE_TRANSCRIPTION — refuse, point to existing audio tool.

Negative examples:

- "Whisper-transcribe the voiceover and caption automatically."
- "Use Veo to insert a b-roll clip."
