# Xninetzy Adapter — Codex
<!-- id: xninetzy.codex; version: 2.4.1; scope: codex -->

At session start read `~/.xninetzy/CORE_PROMPT.md`, `~/.xninetzy/CORE_RULES.md` and `~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md`. If one is missing, stop and report it.

- Edit files with `apply_patch`; use absolute paths.
- MCP servers (including `xninetzy`, `xn-bridge`, `xn-interact`, `xn-motion`), permissions, project trust and model settings live in `~/.codex/config.toml`; this file grants none.
- Skills `xn-bridge`, `xn-career` and `xn-social` are in `~/.codex/skills`; career and social work follow CORE_PROMPT routing rules 3 and 4.
- Security requests trigger CORE_PROMPT's security route and `~/.xninetzy/references/security-testing.md` in every workspace; use the installed free MCP gateway and the exact schema for each relevant operation.
