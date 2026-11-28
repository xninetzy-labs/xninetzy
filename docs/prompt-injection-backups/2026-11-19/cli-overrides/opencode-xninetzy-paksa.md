# Xninetzy Adapter — OpenCode
<!-- id: xninetzy.opencode; version: 2.2.0; scope: opencode -->

At session start read `~/.xninetzy/CORE_PROMPT.md`, `~/.xninetzy/CORE_RULES.md` and `~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md`. If one is missing, stop and report it.

- MCP servers (`xninetzy`, `xn-motion`), permissions and models live in `~/.config/opencode/opencode.jsonc`; this file grants none.
- Use `~/...` for user paths and absolute paths for repository files.
