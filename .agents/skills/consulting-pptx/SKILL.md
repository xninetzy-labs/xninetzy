---
name: consulting-pptx
description: 'Builds boardroom-quality consulting decks in two modes: HTML/rules (~80 slide rules, 62 HTML archetypes, check_deck.py at 0 FAIL) or brand-template filling with pptxgenjs, plus deck editing and document-to-slides conversion. Use for consulting-grade, MECE or template-based decks.'
metadata:
  keywords: analyze anyideaz backed canon carnot catalog combines complete convert design discipline documents driven edit excel existing fidelity finishing follow from generate generation include instructions into language maximum mechanical must natural node part pdf pipeline powerpoint ppt pptx presentation python reports skill strength structured tech that this triggers user wants when word work
---

# consulting-pptx (composite, max-strength)

The maximum-strength consulting PowerPoint skill on xninetzy. Combines **two upstream skill bodies**:

| Mode | Source | Strength | Weakness |
|---|---|---|---|
| **HTML/rules mode** | carnot-tech (`modes/html-rules/`) | Strict rule canon (~80 rules), 62-archetype HTML library, mechanical `check_deck.py` checker, AI-flavored word lexicon | HTML output, requires Chrome to print PDF |
| **Template mode** | anyideaz (`modes/template/`) | Preserves brand template (.pptx) — fonts, colors, layouts, embedded imagery | Heavier setup (Node + pptxgenjs + markitdown) |

Choose mode based on user intent:

- "I have a corporate .pptx template, fill it with content" → **template mode** (`modes/template/MODE.md`)
- "I need a clean boardroom deck from scratch, consulting style" → **HTML/rules mode** (`modes/html-rules/MODE.md`)
- "I want both — strict rules AND brand fidelity" → **both**, in parallel; cross-check via `check_deck.py`.

## Canonical lifecycle

0. **Ask first**: before building, run the owner brief and Canva reference round from skill `document-studio` › "Decks: ask first, reference from Canva". A Canva design exported as `.pptx` becomes the template for template mode.
1. **Choose mode** based on whether user supplied a `.pptx` template.
2. **Read rules canon** (`modes/html-rules/references/slide-rules.md`) before designing.
3. **Assemble** using the mode-appropriate script (`modes/html-rules/scripts/new_deck.py` for HTML mode; `modes/template/shared/scripts/run_pptxgenjs.js` after `modes/template/shared/scripts/extract_template.py` for template mode).
4. **Mechanical check** — `modes/html-rules/scripts/check_deck.py` returns FAIL count; must be 0.
5. **Visual check** — `modes/html-rules/scripts/check_layout.mjs` (Playwright) for footer/overflow; optional for template mode.
6. **AI-smell sweep** — `modes/html-rules/references/ai-smell-lexicon.md` to scrub LLM-flavored phrasing.
7. **Fresh-eye review** — `modes/html-rules/references/content-review-prompt.md`.
8. **Deliver** — `.pptx` (template mode) or `.pdf` via headless Chrome (HTML mode).

## Resources inventory

Both upstream skills are vendored under `modes/`. Read the mode's `MODE.md` for its detailed steps before assembling:

- `modes/html-rules/references/` — slide-rules.md, archetype-catalog.md, content-review-prompt.md, ai-smell-lexicon.md
- `modes/html-rules/scripts/` — new_deck.py, check_deck.py, check_layout.mjs
- `modes/html-rules/templates/` — 62 HTML archetypes
- `modes/html-rules/assets/` — SlideCatalog_16x9.pdf, SuperTemplate_62type.pptx
- `modes/template/shared/prompts/` — 6 rule prompts (outline, slide-code, shared-pptxgenjs, preamble, analyze, edit)
- `modes/template/shared/docs/` — slide-types.md, pptxgenjs-api.md, pitfalls.md, copilot-migration.md
- `modes/template/shared/scripts/` — extract_template.py, run_pptxgenjs.js, convert_to_markdown.py, setup_deps.sh

Open these with the client's file tools; paths are relative to this skill's folder.

## When to use

- User asks for "consulting-quality" / "boardroom" / "MECE" / "McKinsey-style" deck.
- User has a corporate template and wants content fit to it.
- User wants maximum-quality slide discipline applied mechanically (FAIL = 0 from `check_deck.py`).

## When NOT to use

- Quick internal one-pager — overhead not worth it.
- Pure text deck (no visuals, no structure beyond bullets).
- User supplies only an outline and wants markdown — use markdown tools, not slide tools.