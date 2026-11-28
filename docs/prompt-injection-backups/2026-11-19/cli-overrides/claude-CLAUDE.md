# Xninetzy Adapter — Claude Code
<!-- id: xninetzy.claude; version: 2.2.0; scope: claude-code -->

Shared contract, imported at launch:
@~/.xninetzy/CORE_PROMPT.md
@~/.xninetzy/CORE_RULES.md
@~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md

If CORE_PROMPT.md, CORE_RULES.md or CLI_SHARED_INSTRUCTIONS.md is absent from context, Read it from `~/.xninetzy/`. If a file does not exist, stop and report it.

- The workspace `CLAUDE.md` loads automatically and adds project rules.
- MCP tools appear as `mcp__<server>__<tool>`; load deferred tools with ToolSearch before calling them.
- Editing existing `docx`, `pptx`, `xlsx` or `pdf` files uses the synced `anthropic-skills:*` skills (local copies are off via `skillOverrides`); new documents and decks use `document-studio`.
- Permissions and model settings live in `~/.claude/settings.json`; this file grants none.

<!-- xn-bridge-trigger:begin; owner instruction 2026-11-17; rollback: cp ~/.claude/backups/CLAUDE.md.pre-xn-bridge-trigger ~/.claude/CLAUDE.md -->
## Career trigger — XN-Bridge
Career requests follow CORE_PROMPT routing rule 3 in every directory. A `UserPromptSubmit` hook in `~/.claude/settings.json` adds a reminder on career keywords. The `xn-bridge`, `osm`, `gmaps`, `careers-crawl` and `gmail-send` servers and the `xn-career` and `xn-bridge` skills are registered at user scope. If `mcp__xn-bridge__*` is missing, report `awaiting input`; never substitute generic search, crawl, mail or browser tools for external work.
<!-- xn-bridge-trigger:end -->
