# Xninetzy Adapter — Codex
<!-- id: xninetzy.codex; version: 2.1.0; scope: codex -->

At session start read `~/.xninetzy/CORE_PROMPT.md`, `~/.xninetzy/CORE_RULES.md` and `~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md`. If one is missing, stop and report it.

- Edit files with `apply_patch`; use absolute paths.
- MCP servers (`xninetzy`, `xn-motion`), permissions, project trust and model settings live in `~/.codex/config.toml`; this file grants none.
