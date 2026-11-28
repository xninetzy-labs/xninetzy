# Xninetzy Adapter — Claude Code
<!-- id: xninetzy.claude; version: 2.4.1; scope: claude-code -->

Shared contract, imported at launch:
@~/.xninetzy/CORE_PROMPT.md
@~/.xninetzy/CORE_RULES.md
@~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md

If CORE_PROMPT.md, CORE_RULES.md or CLI_SHARED_INSTRUCTIONS.md is absent from context, Read it from `~/.xninetzy/`. If a file does not exist, stop and report it.

- The workspace `CLAUDE.md` loads automatically and adds project rules.
- MCP tools appear as `mcp__<server>__<tool>`; load deferred tools with ToolSearch before calling them.
- Editing existing `docx`, `pptx`, `xlsx` or `pdf` files uses the synced `anthropic-skills:*` skills (local copies are off via `skillOverrides`); new documents and decks use `document-studio`.
- Permissions and model settings live in `~/.claude/settings.json`; this file grants none.
- Security requests trigger CORE_PROMPT's security route and `~/.xninetzy/references/security-testing.md` in every workspace; use the installed free MCP gateway and the exact schema for each relevant operation.

<!-- xn-bridge-trigger:begin; owner instruction 2026-11-17, extended 2026-11-19; rollback: cp ~/.claude/backups/CLAUDE.md.pre-xn-bridge-trigger ~/.claude/CLAUDE.md -->
## XN-Bridge routing
Career requests follow CORE_PROMPT routing rule 3 and social media requests rule 4 in every directory; cross-server work uses XN-Bridge as CORE_PROMPT describes. A `UserPromptSubmit` hook in `~/.claude/settings.json` adds a reminder on career and social media keywords. The `xn-bridge`, `xn-interact`, `osm`, `gmaps`, `careers-crawl` and `gmail-send` servers and the `xn-bridge`, `xn-career` and `xn-social` skills are registered at user scope. If `mcp__xn-bridge__*` is missing, or `mcp__xn-interact__*` for social work, report `awaiting input`; never substitute generic search, crawl, mail, browser or posting tools for external work.
<!-- xn-bridge-trigger:end -->
