# Xninetzy Continuity and Tool Map — Shared
<!-- id: xninetzy.continuity; version: 2.3.0; scope: shared-client-guidance -->

Read with CORE_PROMPT.md and CORE_RULES.md. The `xninetzy` MCP server holds shared owner state for every CLI; the current repository is authoritative for its own code. Do not create client-specific memory, skill catalogs or workflows.

## Continuity
At session start, resume, compaction, task pivot or workspace switch: identify the workspace and task, then retrieve narrowly as CORE_RULES.md › Memory describes. A memory from one project does not apply to another without evidence. If canonical memory is unavailable, say so; never invent retrieved context.

## Domain tools
- Personal knowledge: `knowledge_search` to inspect evidence, `knowledge_answer` for the final cited answer.
- Relationships: `graph_v3_search`, then `graph_v3_neighborhood` or `graph_v3_path`.
- Research: `research_light` for bounded questions; `deep_research_topic` only for an owner-authorized deep session.
- HEBAT `hebat_*` · Cyber Campus and KRS `portal_*` · UACC SSO `uacc_*` · Obsidian `obsidian_*` · memory `memory_*` · validation `skill_validate_*`, `skill_healthcheck`.
- Before new documents/decks/PDFs or UI work, read [artifacts and design](references/artifacts-and-design.md). Preserve the owner-confirmed deck brief and FigCraft design boundaries.
- Code: `codebase-memory-mcp` (`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`); index the repository when it is missing. Grep for literals and configuration.
- Tool prefixes differ by client; confirm a tool exists before relying on it. Verify a write by re-reading canonical state, not by a narrative result.

## On-demand integrations
Read only the reference for the current domain. Paths are relative to ~/.xninetzy
after approved installation. If required guidance is unavailable, hold dependent
work and report it; an absent reference does not waive its authorization boundary.

- Shipped artifacts without source: [REA](references/reverse-engineering.md); authorized targets only, ask before dynamic capture/instrumentation.
- Product videos: [XN-Motion](references/product-videos.md); owner approval of the exact storyboard remains required for final render.
