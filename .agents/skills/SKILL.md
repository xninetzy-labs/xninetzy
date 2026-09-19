---

...

...

...
name: "consulting-pptx"
description: "Maximum-strength boardroom-quality PowerPoint skill. Combines carnot-tech consulting slide rules canon (~80 rules, 62 HTML archetypes, mechanical rule checker) with anyideaz template-driven pptxgenjs pipeline (analyze, generate, edit). Use when the user wants the highest-quality consulting deck, with strict slide-design discipline AND template fidelity. Triggers include: consulting-quality slides, boardroom deck, MECE slides, McKinsey-style deck, structured consulting presentation, template-driven slide deck, highest-quality PPT."
metadata:
  scope: "general"
  owner: "xninetzy"
  upstream: "https://github.com/carnot-tech/consulting-pptx-skill + https://github.com/anyideaz/pptx-skills"
  license: "MIT"
  language: "en"
  version: "1.0.0"
  lifecycle: "choose-mode design-rules assemble mechanical-check visual-check deliver"
  trust_level: "owner-installed"
  composed_of: "consulting-pptx-skill,pptx-skills"
  external_subprocess: "true"
  external_subprocess_bins: "python3 node playwright google-chrome"
...

# consulting-pptx (composite, max-strength)

The maximum-strength consulting PowerPoint skill on xninetzy. Combines **two upstream skill bodies**:

| Mode | Source | Strength | Weakness |
|---|---|---|---|
| **HTML/rules mode** | carnot-tech (this repo: `consulting-pptx-skill/`) | Strict rule canon (~80 rules), 62-archetype HTML library, mechanical `check_deck.py` checker, AI-flavored word lexicon | HTML output, requires Chrome to print PDF |
| **Template mode** | anyideaz (this repo: `pptx-skills/`) | Preserves brand template (.pptx) — fonts, colors, layouts, embedded imagery | Heavier setup (Node + pptxgenjs + markitdown) |

Choose mode based on user intent:

- "I have a corporate .pptx template, fill it with content" → **template mode** (pptx-skills)
- "I need a clean boardroom deck from scratch, consulting style" → **HTML/rules mode** (consulting-pptx-skill)
- "I want both — strict rules AND brand fidelity" → **both**, in parallel; cross-check via `check_deck.py`.

## Canonical lifecycle

1. **Choose mode** based on whether user supplied a `.pptx` template.
2. **Read rules canon** (`references/slide-rules.md` from carnot-tech) before designing.
3. **Assemble** using the mode-appropriate script (`scripts/new_deck.py` for HTML mode; `scripts/run_pptxgenjs.js` after `scripts/extract_template.py` for template mode).
4. **Mechanical check** — `consulting-pptx-skill/scripts/check_deck.py` returns FAIL count; must be 0.
5. **Visual check** — `consulting-pptx-skill/scripts/check_layout.mjs` (Playwright) for footer/overflow; optional for template mode.
6. **AI-smell sweep** — `references/ai-smell-lexicon.md` to scrub LLM-flavored phrasing.
7. **Fresh-eye review** — `references/content-review-prompt.md` (carnot-tech).
8. **Deliver** — `.pptx` (template mode) or `.pdf` via headless Chrome (HTML mode).

## Resources inventory

This composite skill **references** the two upstream skills rather than duplicating them. The actual rule canon, archetype catalog, scripts, and templates live in:

- `consulting-pptx-skill/references/` — slide-rules.md, archetype-catalog.md, content-review-prompt.md, ai-smell-lexicon.md
- `consulting-pptx-skill/scripts/` — new_deck.py, check_deck.py, check_layout.mjs
- `consulting-pptx-skill/templates/` — 62 HTML archetypes
- `consulting-pptx-skill/assets/` — SlideCatalog_16x9.pdf, SuperTemplate_62type.pptx
- `pptx-skills/shared/prompts/` — 6 rule prompts (outline, slide-code, shared-pptxgenjs, preamble, analyze, edit)
- `pptx-skills/shared/docs/` — slide-types.md, pptxgenjs-api.md, pitfalls.md, copilot-migration.md
- `pptx-skills/shared/scripts/` — extract_template.py, run_pptxgenjs.js, convert_to_markdown.py, setup_deps.sh

Call `skill_get('consulting-pptx-skill')` or `skill_get('pptx-skills')` to load the full body when you need the detailed steps.

## When to use

- User asks for "consulting-quality" / "boardroom" / "MECE" / "McKinsey-style" deck.
- User has a corporate template and wants content fit to it.
- User wants maximum-quality slide discipline applied mechanically (FAIL = 0 from `check_deck.py`).

## When NOT to use

- Quick internal one-pager — overhead not worth it.
- Pure text deck (no visuals, no structure beyond bullets).
- User supplies only an outline and wants markdown — use markdown tools, not slide tools.