# MCP protocol and compatibility contract

Workflow continuation2026-11-15: existing `workflow_resume`, `workflow_status`, `workflow_cancel` names/parameters remain. Resume uses the saved plan/state; an additive internal/result `checkpoint` envelope and `cancelled` action/run status preserve recovery evidence. Workflow descriptions now state exact resume/failed-run cancellation behavior. Legacy state without a valid checkpoint is held rather than regenerated. Actual installed-wheel STDIO recovery negotiates2025-11-25;571 tools and133 READ/6 DRAFT/409 WRITE/23 FINAL policies remain unchanged. A checkpoint/hash or stored SUCCESS is not approval or live artifact verification. This does not certify native client UX or negotiated protocol Tasks support. [Workflow contract](AGENTIC_WORKFLOW.md) defines compatibility and mixed-version limits.

Internal/domain continuation2026-11-14: wire tool names/signatures and SDK/protocol version are unchanged (571 tools; STDIO2025-11-25). Domain services now also hold raw identity-only/legacy approval, HEBAT owner shortcuts and boolean-only deletion. The deletion tool remains FINAL at MCP even for confirm=false; its internal inspection path does not lower gateway policy. Requests report actual local inbox delivery rather than a removed WhatsApp approval channel. The rebuilt candidate has verified installed-source parity, preventing successful source-STDIO discovery from masking a stale installed package. No new client configuration, supported native approval UI or positive human authorization is claimed. Exact evidence and image identity are in Phase1 and CLIENT_CONNECTION_RESULTS.json.

Verified 2026-11-10. Existing implementation: `xninetzy/interfaces/mcp_server.py` with SDK `mcp.server.fastmcp.FastMCP`; canonical tools come from `tools/registry.py` and the trusted-principal adapter. Current declared dependency remains `mcp>=1.28.1,<2`. Existing environment and lock resolve 1.30.0.

## Observed compatibility matrix

| Feature | Current result | Evidence / boundary |
|---|---|---|
| STDIO initialize | VERIFIED_RUNTIME | Actual SDK subprocess session negotiates 2025-11-25 |
| Tool discovery | VERIFIED_RUNTIME | 571 tools returned over STDIO |
| Basic safe tool call | VERIFIED_RUNTIME | Ten datetime calls succeeded; no provider/owner state needed |
| SDK supported versions | VERIFIED_RUNTIME | 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25 constants |
| 2026-07-28 protocol | NOT_VERIFIED / not advertised by installed SDK | No claim of conformance; requires migration experiment |
| Streamable HTTP | DISABLED / VERIFIED_TEST | Loopback and remote HTTP rejected before state initialization; independently authenticated owner channel unavailable |
| Server resources/prompts | VERIFIED_CODE | Skills/catalog resources and memory prompt registered; no host-policy installation implied |
| Protocol task extensions | DOCUMENTED_ONLY for interoperability | Application tasks tool names are not proof of negotiated protocol Tasks extension |
| Codex / Claude Code / OpenCode parity | NOT_VERIFIED_IN_LIVE_ENVIRONMENT | Configurations inspected; no equivalent native owner workflows run |
| Output validation | VERIFIED_TEST for tested returns | Gateway validates resolvable callable return types and declared output schema; `Any` remains untyped, uniform wire output schemas incomplete |

## Standards and decision

The [2026-07-28 MCP specification](https://modelcontextprotocol.io/specification/2026-07-28) describes a stateless core and per-request capability metadata, distinct from simply setting a Streamable HTTP stateless option. The official [Python SDK latest release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0) is 2.3.0 at this audit date. Its behavior/API changes require a separate migration assessment. The [v1.30 protocol documentation](https://github.com/modelcontextprotocol/python-sdk/blob/v1.30.0/docs/protocol.md) provides constants for advertised/supported versions; the actual installed values above are the runtime evidence.

Retain the existing v1 pin during foundational fixes. Before upgrading, test registration/private-manager access, schemas, resources/prompts, legacy-client negotiation, per-request metadata, cancellation/timeouts, task extension support and exact error shapes in a separate environment. Do not equate the package's latest release or `stateless_http=True` with implemented protocol conformance.

Annotations/descriptions are discovery hints and cannot authorize an action. `MCPPrincipal` replaces trusted fields for canonical BaseTool calls; a local installation principal is not remote-user authentication. No non-loopback exposure is part of this work. Domain approval authenticity, replay safety, output filtering and exact-payload checks remain independent responsibilities.

Continuation verified 2026-11-11: the minimal container and nine local-client transports negotiate2025-11-25 and expose571 tools. Container checks include persisted local write/restart/replay; client checks use isolated temporary stores and safe reads. Neither establishes2026-07-28 conformance, native-client model behavior or trusted owner approval. Model-facing approval is disabled as an authorization source until an independently authenticated channel exists. After explicit owner selection A, nine MCP connection entries are installed with backups; native GUI reload and owner-state runtime are separate unverified boundaries documented in CLIENT_CONNECTIONS.md.

November14: the active Codex session invokes real datetime/skill reads. OpenCode2.x adapter now uses its documented mcp.servers/disabled shape (Kilo remains flat); SDK9/9 succeeds but native isolated OpenCode list remains NOT_VERIFIED. This is client-configuration work, not a server SDK/protocol upgrade. Approval decision claims are now atomic at the service helper, while independent human authorization and external single-use consumption remain required and incomplete.

November14 Phase1 gateway contract: canonical risk is enforced before handler execution, all23 FINAL operations are held, and caller declarations cannot lower canonical/context-provider policy. Local writes respect owner mode and require a normalized principal/tool/payload-bound key. MCP schemas add `idempotency_key` where handlers lack it and hide trusted owner/context fields; business names/arguments are preserved. Timed-out workers remain counted until exit. Bounded outputs are validated/redacted; annotations are discovery hints. Details and intentional compatibility restrictions are in [tool governance](TOOL_GOVERNANCE.md). Existing host processes require reconnection to load changed schemas/source. No host prompt installation occurred.

Rollback: no protocol dependency upgrade occurred. The additive mutation-key schema and intentional rejection of unsafe legacy calls require client rediscovery; revert only reviewed hunks while preserving state/reservations. Re-run safe STDIO/contract fixtures after each future SDK migration.
