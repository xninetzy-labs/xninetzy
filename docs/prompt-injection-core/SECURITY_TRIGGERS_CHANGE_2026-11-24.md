# Global security triggers and approval-channel diagnosis

Owner instructions: “dan juga trigger security ini semuanya di global system prompt saya” and “ini buat approve smeua channleku”. These explicitly authorize the prompt and global CLI configuration changes. No application permission was inferred from a prompt.

CORE_PROMPT and CLI_SHARED_INSTRUCTIONS are revision 2.4.1. Security requests route to the installed free `pentesting-cyber-mcp` gateway, coordinated by XN-Bridge, before generic skill discovery. The reference `references/security-testing.md` covers every installed security category, exact tool discovery, scope capture, bounded active tests, aliases, paid/API-key exclusions and evidence requirements. Existing career/social routing and real approval controls are preserved.

The Codex and Claude native adapters reference the new route. Nine existing marked global instruction blocks were updated without replacing their other content. Standard MCP initialization instructions deliver the same routing to every gateway client, including clients whose native global-instruction format was not independently established. This proves installed configuration and protocol delivery, not guaranteed language-model compliance in every application.

Fifteen MCP configuration files share the same XN-Bridge data store and gateway runtime revision. Pi has native extensions for both the scanner gateway and XN-Bridge. The global `~/.local/bin/xnbridge` launcher makes the documented terminal commands available independently of the current workspace.

The legacy error `approval_channel_unverified` was traced to `xninetzy/context/policy/gate.py` and `xninetzy/interfaces/mcp_tool_adapter.py`. Consequential operations are deliberately held because independent positive authorization is unimplemented. It is not a missing per-CLI approval checkbox. Those application guards were not weakened, and no status, database row, confirmation Boolean or owner identity was fabricated.

XN-Bridge has an implemented encrypted signer and terminal approval flow. The installed doctor reported `fingerprint=None`: actual owner-key setup remains required. `xnbridge approval-init` requires a TTY and an owner-entered passphrase of at least ten characters; `xnbridge approve <id>` binds a single signed approval to the displayed payload and target. The agent did not generate or approve an owner credential on the owner's behalf. This flow does not clear legacy Xninetzy's unimplemented boundary.

Backups and the exact changed-file receipt are private under `~/.xninetzy/backups/2026-11-24-security-triggers/` and `~/.xninetzy/backups/2026-11-24-security-channels/`. Restore those reviewed files together with the matching canonical manifest to roll back. Reconnect cached MCP processes or start a new CLI session to load the new gateway instructions.
