---
name: pptx-skills
description: 'Template-driven PowerPoint pipeline (pptxgenjs, python-pptx): analyze a template, generate a deck from it, convert Word/PDF/Excel to slides, or edit a deck from natural-language instructions. Use for template-based deck work.'
metadata:
  keywords: and backed complete document documents existing generation include into node ppt slide structured this triggers user wants when with
---

# pptx-skills (anyideaz)

Three-phase PowerPoint generation pipeline:

1. **Analyze** — `scripts/extract_template.py` reads a `.pptx` template and emits `guideline.md`, `context.json`, and `sample_code.js`.
2. **Generate** — `scripts/run_pptxgenjs.js` builds a deck from outline + preamble + body code, emitting `.pptx`.
3. **Edit** — same scripts with delta-only changes; backup via `code.js.bak`.

Companion rule prompts in `shared/prompts/`:
- `outline-rules.md` — outline structure rules
- `slide-code-rules.md` — pptxgenjs JS code rules
- `shared-pptxgenjs-rules.md` — pptxgenjs library rules
- `preamble-rules.md` — deck preamble rules
- `analyze-rules.md` — template analysis rules
- `edit-rules.md` — delta-edit rules

Document references in `shared/docs/`:
- `slide-types.md`, `pptxgenjs-api.md`, `pitfalls.md`, `copilot-migration.md`.

Setup (one-time):
```bash
bash shared/scripts/setup_deps.sh
```

## When to use

- Template-driven deck creation where the brand/layout must match an existing `.pptx`.
- Bulk content extraction from documents into structured slide outlines.
- Surgical natural-language edits to existing decks without regenerating from scratch.

## When NOT to use

- Pure free-form deck creation with no template — use the HTML/rules mode (`../html-rules/MODE.md`) instead (HTML parts library + slide rules canon).
- Decks that must render in environments without Node.js.

## Operational notes

- `run_pptxgenjs.js` shells out to `node` and writes `.pptx` to user-supplied path.
- `extract_template.py` reads `.pptx` and writes `guideline.md`, `context.json`, `sample_code.js`.
- `convert_to_markdown.py` converts Word/PDF/Excel to markdown via `markitdown`.
- All scripts are pure file I/O — no network egress.