# MCP protocol and compatibility contract

Verified 2026-11-10. Existing implementation: `xninetzy/interfaces/mcp_server.py` with SDK `mcp.server.fastmcp.FastMCP`; canonical tools come from `tools/registry.py` and the trusted-principal adapter. Current declared dependency remains `mcp>=1.28.1,<2`. Existing environment and lock resolve 1.30.0.

## Observed compatibility matrix

| Feature | Current result | Evidence / boundary |
|---|---|---|
| STDIO initialize | VERIFIED_RUNTIME | Actual SDK subprocess session negotiates 2025-11-25 |
| Tool discovery | VERIFIED_RUNTIME | 571 tools returned over STDIO |
| Basic safe tool call | VERIFIED_RUNTIME | Ten datetime calls succeeded; no provider/owner state needed |
| SDK supported versions | VERIFIED_RUNTIME | 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25 constants |
| 2026-07-28 protocol | NOT_VERIFIED / not advertised by installed SDK | No claim of conformance; requires migration experiment |
| Streamable HTTP | VERIFIED_CODE only | Loopback enforced; remote authentication not supplied; live origin/authorization tests incomplete |
| Server resources/prompts | VERIFIED_CODE | Skills/catalog resources and memory prompt registered; no host-policy installation implied |
| Protocol task extensions | DOCUMENTED_ONLY for interoperability | Application tasks tool names are not proof of negotiated protocol Tasks extension |
| Codex / Claude Code / OpenCode parity | NOT_VERIFIED_IN_LIVE_ENVIRONMENT | Configurations inspected; no equivalent native owner workflows run |
| Full structured output schemas | UNKNOWN | Generated LangChain schemas mostly untyped; MCP runtime enforcement needs separate audit |

## Standards and decision

The [2026-07-28 MCP specification](https://modelcontextprotocol.io/specification/2026-07-28) describes a stateless core and per-request capability metadata, distinct from simply setting a Streamable HTTP stateless option. The official [Python SDK latest release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0) is 2.3.0 at this audit date. Its behavior/API changes require a separate migration assessment. The [v1.30 protocol documentation](https://github.com/modelcontextprotocol/python-sdk/blob/v1.30.0/docs/protocol.md) provides constants for advertised/supported versions; the actual installed values above are the runtime evidence.

Retain the existing v1 pin during foundational fixes. Before upgrading, test registration/private-manager access, schemas, resources/prompts, legacy-client negotiation, per-request metadata, cancellation/timeouts, task extension support and exact error shapes in a separate environment. Do not equate the package's latest release or `stateless_http=True` with implemented protocol conformance.

Annotations/descriptions are discovery hints and cannot authorize an action. `MCPPrincipal` replaces trusted fields for canonical BaseTool calls; a local installation principal is not remote-user authentication. No non-loopback exposure is part of this work. Domain approval authenticity, replay safety, output filtering and exact-payload checks remain independent responsibilities.

Rollback: no protocol dependency upgrade or wire-contract migration was performed. New malformed explicit side-effect declarations fail closed; existing valid classes and legacy omitted classification remain supported with documented limits. Re-run safe STDIO/contract fixtures after each future SDK migration.
