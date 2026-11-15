# Xninetzy Continuity and Tool Map — Shared
<!-- id: xninetzy.continuity; version: 2.2.0; scope: shared-client-guidance -->

Read with CORE_PROMPT.md and CORE_RULES.md. The `xninetzy` MCP server holds shared owner state for every CLI; the current repository is authoritative for its own code. Do not create client-specific memory, skill catalogs or workflows.

## Continuity
At session start, resume, compaction, task pivot or workspace switch: identify the workspace and task, then retrieve narrowly as CORE_RULES.md › Memory describes. A memory from one project does not apply to another without evidence. If canonical memory is unavailable, say so; never invent retrieved context.

## Domain tools
- Personal knowledge: `knowledge_search` to inspect evidence, `knowledge_answer` for the final cited answer.
- Relationships: `graph_v3_search`, then `graph_v3_neighborhood` or `graph_v3_path`.
- Research: `research_light` for bounded questions; `deep_research_topic` only for an owner-authorized deep session.
- HEBAT `hebat_*` · Cyber Campus and KRS `portal_*` · UACC SSO `uacc_*` · Obsidian `obsidian_*` · memory `memory_*` · validation `skill_validate_*`, `skill_healthcheck`.
- New documents, decks and PDFs from content: skill `document-studio` → `artifact_render` (themes: `artifact_theme_list`, Canva or brand `.pptx` → `artifact_theme_from_file`); never write one-off python-docx/python-pptx code for them. Edit existing Office files with the docx/pptx skills.
- Decks: before any new PPT or slides, ask the owner for purpose, audience, length, language and a reference, offering their Canva designs (`search-designs` with thumbnails), a new Canva design (`generate-design`), a brand file or a built-in theme. Canva choice: `export-design` as PPTX → `artifact_theme_from_file` → `artifact_render(deck_brief_confirmed=true)`. Canva disconnected: say so and offer the others.
- UI implementation or restyle: skill `figcraft-ui-sync`. The owner's FigCraft file (`figcraft` MCP) is the design source: read its styles and components before coding, match them, then update the FigCraft frames to the shipped UI and compare screenshots.
- Code: `codebase-memory-mcp` (`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`); index the repository when it is missing. Grep for literals and configuration.
- Tool prefixes differ by client; confirm a tool exists before relying on it. Verify a write by re-reading canonical state, not by a narrative result.

## Reverse engineering (REA)
Load skill `reverse-engineer-anything` and use the `rea` MCP when the question depends on a shipped artifact without source: binary, APK/IPA, ASAR/Electron, .NET, firmware, WASM, pcap/HAR, build diffs, installed apps or websites. For a repository with source, use `codebase-memory-mcp` instead.
Authorized targets only. Static analysis may proceed; ask before runtime capture, launching or instrumenting a target, adb/device actions or installing an engine.
Shell use: `set -a; . ~/.local/share/rea-tools/env.sh; set +a`, then `rea doctor --json` lists the engines (IDA and JEB are not installed). Report REA's evidence and limits as returned; never fill gaps by guessing.

## XN-Motion (product videos)
For product, promo, demo, launch, feature-update or architecture-explainer videos from a local project or a public website; it is not a general video editor. Follow the server's `create-product-video` flow, starting with `environment_check`.
Use facts only from inspection or the owner. Claims marked `marketing_claim`, `unverified_claim` or `contradicted_claim` stay out unless the owner confirms them.
Ask before `website_inspect` and before a final `render_start`. The owner approves the exact storyboard: never approve for them, guess `approval_record` codes or enable `XN_MOTION_AUTO_APPROVE`.
After `qa_run`, inspect the contact sheet or rendered frames and report what you saw. Reads are limited to `/home/misbahul45/code`; output goes to `~/.local/share/xn-motion`. Docs: `/home/misbahul45/code/XN-Motion`.
