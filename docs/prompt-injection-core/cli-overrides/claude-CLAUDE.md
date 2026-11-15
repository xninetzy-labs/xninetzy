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
