---
name: document-studio
description: Turns content into themed DOCX, PDF and PPTX in one Xninetzy `artifact_render` call, with reusable themes, brand or Canva templates, previews and QA. Use for any report, assignment, deck or PDF built from content instead of writing python-docx or python-pptx code.
metadata:
  keywords: ppt project proyek readme bikin generate convert docx pptx pdf word powerpoint slide slides deck presentasi presentation laporan report makalah dokumen document theme template canva brand cover daftar isi toc render export
---

# Document Studio

Rendering, styling and QA are automated in Xninetzy. Your job is the content: write it once as Markdown, then call the tool.

## Decks: ask first, reference from Canva

Every new deck (PPT, PPTX, slides, presentation) starts with one question round to the owner before any rendering; `artifact_render` returns `awaiting_input` for `pptx`/`slides_pdf` until `deck_brief_confirmed=true`.

1. **Ask** in one message (AskUserQuestion in Claude Code): purpose and audience, slide count or talk length, language, and the reference: (a) one of the owner's Canva designs, (b) a new Canva design generated from the brief, (c) a brand `.pptx`/`.potx` file, (d) a built-in theme. Propose your recommendation first.
2. **Show Canva candidates** for (a): `search-designs` with the topic (an empty query lists recent designs), then 3–5 titles with `get-design-thumbnail`. For (b): `generate-design` with the brief as a presentation, show the candidates, then `create-design-from-candidate` only for the one the owner picked; it creates a design in their Canva account.
3. **Turn the choice into a theme**: `get-export-formats`, `export-design` as `pptx`, download the file to `UNTRACKED_OUTPUT_DIR/canva/<design_id>.pptx`, then `artifact_theme_from_file(path, name="canva-<slug>")`. Pass the file as `template_path` instead when the owner wants the Canva layouts themselves. `get-design-content` and `get-presenter-notes` reuse the deck's text when asked.
4. **Render** with `artifact_render(..., theme=…, deck_brief_confirmed=true)` and follow the workflow below from step 5.

Canva tools appear with a client prefix (`mcp__canva__search-designs` in Claude Code). When Canva is not connected or needs login, say so with the login step (Claude Code `/mcp`, Codex `codex mcp login canva`, OpenCode `opencode mcp auth canva`) and offer (c) or (d). `license_required` on export means premium elements: offer another design. Free plans export at standard quality; autofill and brand templates need Canva Pro.

## Workflow

1. **Gather content** from the sources (project documents via `document_ingest` or Read). Never invent facts, numbers or citations.
2. **Pick a theme** with `artifact_theme_list`: `academic-hebat` for HEBAT/UNAIR assignments (HEBAT Document Standard), `professional`, `minimal`, `consulting`, or an owner theme. For a deck, the theme is the reference the owner chose above.
3. **Write one Markdown source** using the dialect in `references/markdown-dialect.md`. The same source can produce the document and the deck. Save it as a `.md` file when the owner wants to keep or revise it; otherwise pass it inline.
4. **Render**: `artifact_render(source_path=… or markdown=…, formats=[…], theme=…, output_name=…)`. Formats: `docx`, `pdf` (from the DOCX), `pptx`, `slides_pdf` (from the PPTX). Pass `template_path` to reuse a brand `.docx`/`.pptx`.
5. **Inspect**: open each `previews.*.contact_sheet` image and look at it. Check overflow, empty or crowded slides, captions, table of contents numbers, and the QA findings and warnings in the result.
6. **Fix and re-render** by editing the Markdown, keeping the same `output_name` so files are replaced.
7. **Report** the file paths, the theme, and what you saw in the previews. For submit-bound work, run the validation pass from CORE_RULES before delivery.

## Themes and Canva

- New look from settings: `artifact_theme_save(name, overrides, base)`; inspect fields with `artifact_theme_get`.
- From a Canva design or brand file: export or download it as PowerPoint (`.pptx`), then `artifact_theme_from_file(path, name)`. It samples the colors and fonts actually used, fixes unreadable contrast and replaces fonts that are not installed with Arial (`keep_fonts=true` keeps them).
- The Canva MCP flow is in "Decks: ask first, reference from Canva" above.

## Use the docx or pptx skill instead when

- editing an existing Office file in place, tracked changes, comments or form filling;
- a feature the studio lacks: native charts, SmartArt, animations, complex multi-column page layouts. Say which feature is missing rather than silently writing one-off generation code.

## Defaults worth knowing

- A title slide and cover come from the front matter; `academic-hebat` adds an Indonesian cover, "Daftar Isi" with real page numbers, and page numbers in the footer.
- Long slides shrink to the theme minimum font, then continue on "(lanjutan)" slides; long tables split across slides; a slide with several tables, images or code blocks is split into one visual per slide.
- Output goes to `GENERATED_DOCUMENTS_DIR/<output_name>/` with `manifest.json` and previews.
