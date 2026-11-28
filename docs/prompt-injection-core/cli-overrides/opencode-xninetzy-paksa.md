# Xninetzy Adapter — OpenCode
<!-- id: xninetzy.opencode; version: 2.4.0; scope: opencode -->

At session start read `~/.xninetzy/CORE_PROMPT.md`, `~/.xninetzy/CORE_RULES.md` and `~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md`. If one is missing, stop and report it.

- MCP servers (including `xninetzy`, `xn-bridge`, `xn-interact`, `xn-motion`), permissions and models live in `~/.config/opencode/opencode.json`; this file grants none.
- Career and social work follow CORE_PROMPT routing rules 3 and 4 through XN-Bridge.
- Use `~/...` for user paths and absolute paths for repository files.
