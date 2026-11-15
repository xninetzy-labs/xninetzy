# Local MCP client connection implementation

Continuation from HEAD `74ff58b`; previous hardening is preserved. Updated2026-11-14: **nine MCP configuration entries installed for eight hosts using owner-selected database A; isolated transport checks pass**. OpenCode2.x schema follow-up is installed; its native health remains unverified. The active Codex session now performs real MCP safe reads. No global prompt installation or permission relaxation occurred.

## Discovery and results

| Installed host | Existing state | Candidate result |
|---|---|---|
| Codex | User TOML points to removed services/ai + app.xninetzy module | Correct module/absolute interpreter; native Codex parses candidate; SDK handshake/read passes |
| Claude Code | Correct module/root; explicit data selection absent | Actual native `claude mcp get xninetzy` reports Connected with isolated state; candidate SDK read passes |
| OpenCode2.2.6 | Both global JSON/JSONC require mcp.servers + disabled rather than old flat/enabled shape | Xninetzy-only migration installed with backups; SDK passes; native isolated list still returns No MCP servers configured, root cause UNKNOWN |
| Gemini | Obsolete module/layout | Corrected candidate SDK transport/read passes |
| Qwen | Obsolete module/layout | Corrected candidate SDK transport/read passes |
| Kilo | Correct module; no explicit environment/store | Correct local command-array/environment schema; candidate SDK transport/read passes |
| Cursor | Correct module; no explicit store | Candidate SDK transport/read passes; GUI activation unverified |
| VS Code Copilot | Built-in Copilot Chat exists; servers.xninetzy absent | Candidate entry uses VS Code servers schema; SDK transport/read passes; GUI activation unverified |
| Copilot standalone shim | Installed launcher exits127 because standalone CLI is missing | Not represented as a working standalone client; VS Code host is the installed alternative |
| ArkCLI 1.0.25 | BytePlus service CLI; inspected native help does not establish a generic MCP host | Unsupported/unverified as a generic local host; no invented config adapter or cloud changes |

Nine candidate configuration entries represent **eight MCP hosts**, because OpenCode has two files. Each candidate initialized with protocol `2025-11-25`, listed **571 tools** and completed `datetime_now` with an ISO result. [Machine-readable evidence](../evaluation/CLIENT_CONNECTION_RESULTS.json) records per-entry elapsed times and the distinction between SDK and native checks. No paid model invocation, external mutation, owner database open or production migration was part of those checks. Native Kilo help may initialize Kilo's own local state; it is not described as universally side-effect-free.

## Implementation and use

`scripts/connect_mcp_clients.py` preserves unrelated configuration values, owner enable/disable choices and tool approval policies. It chooses an absolute existing repository interpreter, the current package module and explicit shared-store environment; no runtime dependency installation is introduced. JSON formatting is normalized; TOML unrelated sections stay outside the edited spans and its parsed roundtrip must match. Comment-bearing JSONC, duplicate JSON keys, symlink config files and remote transport conversions are refused for manual review.

```bash
# No host configuration changes or owner database use:
.venv/bin/python scripts/connect_mcp_clients.py --smoke

# Review a redacted plan for an owner-selected existing database:
.venv/bin/python scripts/connect_mcp_clients.py --store /absolute/selected.sqlite3

# Only after the intended shared store is explicitly selected:
.venv/bin/python scripts/connect_mcp_clients.py --store /absolute/selected.sqlite3 --apply
```

Planning reports hashes, command/module, chosen path and preservation status; it does not print other MCP tokens/environment values. Installation makes a mode0600 backup beside each host file, checks the pre-plan hash, fsyncs a same-directory temporary file and atomically replaces that file. Atomicity is per file, not a multi-client transaction; concurrent changes abort rather than overwrite. Review any partially applied receipt/backups before retrying. This tool repairs connections only; it does not grant permissions, install skills, rotate credentials or deploy global prompts.

## Owner-selected shared store and installation

Both `/home/misbahul45/code/xninetzy/services/ai/data/xninetzy.sqlite3` (A) and `/home/misbahul45/code/data/xninetzy.sqlite3` (B) exist. The owner explicitly answered **A**, resolving the pending choice. All nine entries now select A through `MCP_HOST_SQLITE_PATH`, `SQLITE_PATH` and its parent through `MCP_HOST_DATA_DIR`. B remains intact; neither store was moved, merged or migrated.

Executed the documented plan and `--apply` with A. Verified every saved file against its reviewed candidate and receipt hashes; every original has a protected0600 backup. Unrelated configuration, enable/disable and permission flags are preserved. The private receipt lists exact backup paths and hashes at `/home/misbahul45/.xninetzy/mcp-client-install-20261110T171832470918Z.json`; credential-bearing backups and receipt contents are not copied into the repository. A second plan reports **zero changes for all nine files**. Native `codex mcp get xninetzy --json` parses the installed command and A path correctly without candidate overrides.

Post-install `--smoke`: **9/9** SDK transports initialize, identify server `xninetzy`, list571 tools and return a valid datetime result. The saved command/non-state configuration is exercised with temporary mutable paths and disabled background hooks; this deliberately does not start migration-capable MCP processes against A. Database A/B and the three shared global instruction file hashes remain unchanged before/after this batch. GUI reload, every native host session and production owner-state execution are **NOT_VERIFIED**, rather than inferred from an SDK probe. Restart/reconnect MCP in already-running clients to load the saved configuration.

Post-install smoke initially exposed a parser defect: the installer emitted quoted TOML headers but only recognized bare headers on subsequent reads. Three new regressions failed before the fix; all12 connection tests now pass. Table selection now uses TOML parsing to recognize equivalent bare/double/single-quoted paths, retains full-document roundtrip validation and does not change the already-correct installed settings. This correction is in `scripts/connect_mcp_clients.py` and `tests/tools/test_client_connection_config.py`.

`--smoke` cannot be combined with `--apply` or `--store`. It overrides mutable paths and disables automatic graph/memory/telemetry hooks in temporary child environments; native owner settings are never edited. SDK transport success is not proof of GUI/native session activation, model skill selection, authentic approvals or production readiness.

## Verification, rollback and sources

Connection config tests cover unrelated settings/secret preservation, nested Codex tool policies, VS Code key schema, read-only plans, secure backups, stale-plan races, invalid/symlink/duplicate JSON inputs, disabled-state preservation, existing timeout/cwd handling and refusal to convert remote transports. Full repository Ruff passes with its existing configuration. Broader regression outcomes are recorded in Phase 1/3 after the current run.

Rollback after installation: stop/reload only the affected client, compare its current hash with `after_sha256` in the private receipt, verify its backup against `before_sha256`, then restore that protected backup atomically while preserving the target file mode. Do not overwrite subsequent owner edits. The same directory contains each original backup; no database rollback is needed because neither store changed. Repository source/tests can be reverted by their reviewed hunks while preserving unrelated changes.

Primary references consulted: [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [Kilo MCP](https://kilo.ai/docs/automate/mcp/using-in-cli), [Cursor MCP](https://prod.cursor.com/help/customization/mcp), [VS Code configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration). Installed Gemini/Qwen/Codex/Claude help and sanitized configuration inspection establish local flags/shapes. No source implies that Markdown instructions grant host permissions.

## Native follow-up, 2026-11-14

The current [OpenCode2 MCP contract](https://opencode.ai/docs/mcp-servers/) uses mcp.servers and disabled. Native `opencode mcp add <isolated-alias> --global --env <temporary settings> -- <python> -m xninetzy.interfaces.mcp_server` writes that exact nested shape. The helper now targets this verified installed2.x profile, preserving Kilo's separate flat map. It migrates only Xninetzy, preserves disabled-owner semantics and refuses conflicting legacy/current entries or enable flags. Three migration regressions failed first; further enabled-flag cases failed before correction; all16 client tests now pass. Two OpenCode files were installed with private receipt `/home/misbahul45/.xninetzy/mcp-opencode-v2-install-20261114T102613327525Z.json`; unrelated parsed settings are identical and both replans are unchanged.

Fresh SDK smoke passes9/9 with temporary stores. This does not clear native OpenCode: `opencode mcp list --standalone` still returns No MCP servers configured in isolated XDG directories, including after native add and a project-config probe. Its isolated paths were confirmed with `opencode debug paths config`; the actual owner background service was not restarted. Root cause remains UNKNOWN. Do not interpret native exit0 as a connection pass. Namespace/UID permissions prevented bwrap isolation; these CLI probes are temporary-config tests, not OS-sandbox-certified tests.

Native Claude `mcp get <isolated-alias>` reports Connected after `mcp add-json --scope user` inside a temporary CLAUDE_CONFIG_DIR. Passing session --mcp-config flags to the management subcommand did not register that alias; that failed attempt is not counted as runtime success. No model prompt/account mutation was used. Claude's own promptQueueUseCount can change on invocation; the installed owner MCP entry was separately verified unchanged. Preserve such later metadata on rollback.

The active Codex host session actually invokes Xninetzy datetime_now, skill_suggest_for_request and skill_get successfully on November14. This advances beyond registration parsing, but does not prove every GUI/native client, policy boundary or owner-state migration. No explicit owner-state mutation is part of these probes; application telemetry may follow existing configuration. Earlier unchanged-database hashes describe the November11 installation checkpoint, not absence of owner activity across days.
