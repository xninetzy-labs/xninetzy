# Artifacts and design — load before this domain's work
<!-- id: xninetzy.artifacts-design; version: 2.3.0; scope: conditional-client-guidance -->

- New documents, decks and PDFs from content: skill `document-studio` → `artifact_render` (themes: `artifact_theme_list`, Canva or brand `.pptx` → `artifact_theme_from_file`); never write one-off python-docx/python-pptx code for them. Edit existing Office files with the docx/pptx skills.
- Decks: before any new PPT or slides, ask the owner for purpose, audience, length, language and a reference, offering their Canva designs (`search-designs` with thumbnails), a new Canva design (`generate-design`), a brand file or a built-in theme. Canva choice: `export-design` as PPTX → `artifact_theme_from_file` → `artifact_render(deck_brief_confirmed=true)`. Canva disconnected: say so and offer the others.
- UI implementation or restyle: skill `figcraft-ui-sync`. The owner's FigCraft file (`figcraft` MCP) is the design source: read its styles and components before coding, match them, then update the FigCraft frames to the shipped UI and compare screenshots.

This guidance does not grant permission or replace CORE_RULES.md.
