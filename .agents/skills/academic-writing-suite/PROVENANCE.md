# Provenance

Vendored 2026-11-25 by owner request from the article "15 AI Academic Writing Skills" (Kimi). Static review per `skill-security-review`: nothing executed; only Markdown copied; no scripts, plugin manifests, tests, installers or images. All upstream licenses are MIT; the notices are reproduced in `THIRD_PARTY_LICENSES.md`.

| Route | Upstream (commit) | Files | Change |
|---|---|---|---|
| `ml-sections/` | github.com/Master-cai/Research-Paper-Writing-Skills (77e7c2c) | 38 | `SKILL.md` renamed `guide.md`, `agents/openai.yaml` dropped |
| `cs-systems/` | github.com/SNL-UCSB/paper-writing-skill (66f53c0) | 26 | `SKILL.md` renamed `guide.md`; `setup` script, README, CHANGELOG, DESIGN, USAGE, CLAUDE.md, `examples/` dropped |
| `econ/` | github.com/hanlulong/econ-writing-skill (f2bf7a2) | 5 | `SKILL.md` renamed `guide.md`; link targets rewritten; packaging and tests dropped |
| `journal-adapt/` | github.com/WantongC/journal-adapt-writing-skill (cc79265) | 9 | `SKILL.md` renamed `guide.md`; `examples/jeem` and docs dropped |
| `humanities/` | github.com/lishix520/academic-paper-skills (c325557) | 6 | `SKILL.md` renamed `guide.md`; 4 scripts, README, CONTRIBUTING dropped |
| `latex-review/` | github.com/andrehuang/academic-writing-agents (d4d9d3a) | 14 | orchestrator and principles renamed; absolute `/Users/owl/.claude/...` path rewritten; `paper-crawler.md` dropped (curl egress) |
| `humanize.md` | github.com/blader/humanizer (a32f244) | 1 | `SKILL.md` renamed; scripts and plugin manifests dropped |

`*.index.md` files are generated heading maps (line ranges) added for sliced reading. Nested `SKILL.md` files were renamed so no client registers duplicate skills.

Original to this repository: `references/cite-style.md`, `references/polish.md`, `references/rebuttal.md` (implement the behavior described for Kimi's `cite-style-converter`, `scholarly-writing-refiner` and the rebuttal part of `sci-review`; Kimi's own skill text is not public).

## Not installed
- `Aut_Sci_Write` (357766f): 105 scripts, API-key downloaders, an AGPL component and a stage that targets AI-detector scores (excluded on integrity grounds); search, download, PPT and extraction are already covered by the `paper_research` MCP, `research` and `document-studio`.
- `ai-research-skills` (b3b6157) and `Awesome-Scientific-Skills` (e67760e): catalogs and link lists with no `SKILL.md` to install.
- Kimi `academic-paper-reviewer` is covered by `paper-review`; `sci-paper` by `scientific-paper-writer`, `research-paper-writer` and `ml-sections/`; `astro-observation-report` is a gravitational-wave niche and was skipped.
