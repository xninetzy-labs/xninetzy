# Canonical tool execution governance

November16 compact-discovery continuation: `tool_catalog(query, offset, compact)`
and `skill_list(query, limit, offset, compact)` extend existing tools with optional
arguments. Omitted arguments retain previous output. Compact tool rows keep name,
description, risk, requires_approval and requires_idempotency; filtering/pagination
changes disclosure only, never the execution catalog or authorization. Names,
descriptions and aliases remain untrusted as permission grants. Full578-tool MCP
enumeration is retained for compatibility. Seven tools were added by prior owner
work since the older571 snapshot; this batch adds no canonical tool.

Use a small filtered metadata result before requesting relevant procedures or
client tool schemas. Native clients may still inject the entire catalog; this
server cannot claim a startup/context reduction from compact result support.
The existing skill-context helper now honors its configured character budget
while keeping the trust guard or returning no metadata. It is not a tokenizer or
an independently enforced host context window. Runtime policy checks, trusted
principal injection, exact approvals, write keys and kill switches are unchanged.

Verified scope: local single-owner STDIO MCP, 2026-11-14. This document describes the current gateway, not a production authorization certification.

`VERIFIED_CODE`: `tools/execution_policies.json` owns explicit risk classifications for all 571 registered names. `manifest_for` reads this packaged, versioned catalog; unknown names receive FINAL policy with `policy_known=False` and are denied. Tool descriptions, argument names, learned configuration, aliases and caller-selected side-effect declarations cannot lower canonical risk. Registration additions require a reviewed catalog entry and contract tests. The current distribution is READ133 / DRAFT6 / WRITE409 / FINAL23. Some stateful queries are conservatively WRITE; this inventory is not exhaustive proof of each handler's semantics.

`VERIFIED_CODE`: `interfaces/mcp_tool_adapter.py` applies the gateway to BaseTool and plain callable registrations:

1. Resolve explicit policy, installation principal and kill switch.
2. Deny unknown policy and consequential operations; preserve explicit owner restrictions and the global write action mode.
3. Replace trusted context and owner fields server-side, validate business arguments, reject unexpected fields, and cap input at64KiB.
4. Require a nonblank idempotency key for WRITE. Reserve the normalized principal/tool/key/payload in existing SQLite state before execution.
5. Execute under a bounded deadline and concurrency limit. A timed-out worker retains its slot until it actually exits.
6. Validate declared output types, sanitize credentials and identity fields, and cap returned output at the manifest budget (currently32KiB).
7. Persist the replayable sanitized outcome; optional telemetry cannot invalidate a committed result.

Owner namespaces with declared defaults such as `system` are preserved for legacy single-owner data. This is not tenant isolation for a multi-user server. Tool annotations are conservative discovery hints, never authorization evidence. Typed callable returns are checked when resolvable; `Any` remains untyped. Uniform typed business result envelopes and semantic outcome verification remain future work.

## Approval boundary

Internal/domain continuation: `set_approval_status(..., 'approved', ...)` now always returns `approval_channel_unverified`; configured IDs and display names cannot authenticate a person. `validate_approval` still checks record/action/hash/expiry, then refuses legacy status as authorization evidence. No issued record is usable for a consequential action in this build. Stored rows are not deleted or rewritten. Owner rejection uses exact configured principal IDs and the actual STDIO fallback; this reversible operation grants no permission.

The private `_apply_status_decision` retains the historical conditional transition/effect algorithm for unit regression and future reviewed integration. Public code invokes it only for authorized rejection; it is not a registered tool, human approval API or isolation boundary against privileged Python execution. Existing race/rollback and learning-effect tests are explicitly kernel tests, not successful human approval scenarios. HEBAT upload paths now require policy/validation even for owner identity. The removal tool holds confirm=true before reads/effects; its inspection path remains and the boolean-authorized mutation branch is removed. QA/KRS fixtures prove matching legacy approved records cannot submit/arm. Other direct/internal provider paths still need bounded coverage; no universal sandbox claim follows.

Request/inbox messages share truthful delivery status and never advertise removed WhatsApp buttons or `/approve` commands. Failed notification logs contain neither payload text nor exception messages. Inbox persistence is not evidence of consent.

All23 FINAL operations are held before their handlers with `approval_channel_unverified`. Arbitrary approval IDs, `confirm=true`, retrieved instructions, prior workflow approvals, tool metadata and model-facing `hitl_approve` cannot authenticate owner consent. External mutation and irreversible classes in the context policy also require the independently authenticated channel, which is currently unavailable. Service-level decision claims are atomic, but do not establish genuine human approval or external single-use consumption. Do not describe these operations as usable or H1 as complete.

The global default write mode remains `approval`. A local WRITE runs only when existing owner policy permits automatic execution; test/container fixtures explicitly select `auto` for synthetic local data. FINAL is held even under `auto`. No owner policy file or deployment environment was changed by these fixtures.

HTTP is rejected before database initialization, including loopback, because this build lacks verified HTTP principal authentication. Supported operational profile is local STDIO. A local process principal does not authenticate a remote caller.

## Compatibility and state

Tool names and business parameters are preserved. MCP schemas hide injected identity fields and add an optional `idempotency_key` where a WRITE handler lacks one; actual mutation execution requires it. Clients must rediscover tools after reconnecting. Calls formerly accepted without a key, with spoofed identity, with an unverified approval, or under an owner-restricted write mode intentionally fail closed. Existing in-flight host processes need reconnection to load revised source; source changes do not hot-replace them.

Gateway reservations use a new `gateway-v1:` scope inside the existing `idempotency_keys` table; legacy payload-sensitive domain keys remain unchanged. Reusing a key with different normalized payload is rejected. Pending, timed-out, cancelled, validation-failed and uncertain outcomes are never automatically reclaimed. Successful results replay across clients with the same installation principal. No schema migration or owner data reset is required. Legacy reservations do not retroactively map to gateway keys: reconcile pre-upgrade pending/in-flight work before retrying it. External exactly-once delivery is not claimed.

Automatic memory, graph and improvement mutations run only inside an actual permitted WRITE attempt, before its gateway result commit. READ/DRAFT results do not invoke these canonical-state hooks, and successful replay does not invoke them again. Per-call audit/metrics remain separate. This intentionally corrects earlier automatic memory writes from reads and duplicate artifacts on replay; it does not delete historical memories or promise transactional exactly-once behavior across optional stores. Optional hook failures remain isolated and expose only exception types.

Identifier redaction scans fixed domain markers and their adjacent token once; a long unrelated token cannot repeatedly rescan a greedy prefix. Existing identifier masks, ordinary emails, leading punctuation and nonoverlapping matching are preserved by contract tests and2000 seeded comparisons against the previous matcher. The measured adversarial fixture and limitations are in PERFORMANCE_BASELINE.md.

SQLite's conditional writes and transactions provide the reservation/claim primitive ([UPDATE](https://www.sqlite.org/lang_update.html), [transactions](https://www.sqlite.org/lang_transaction.html)); they cannot atomically commit a third-party side effect. Recovery requires inspecting canonical/provider evidence before an owner-authorized correction. Never delete a pending reservation merely to make a retry succeed.

## Controlled improvement

Learned `context_config` updates accept only bounded retrieval/routing tuning: `LIGHTNING_EXPLORATION_RATE`, `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, `GRAPH_RETRIEVAL_TOP_K`, `GRAPH_RRF_K`. Booleans, invalid ranges and other settings are rejected. Legacy protected override rows are ignored without deletion. Settings reads use the selected existing SQLite file in read-only mode and do not create a missing database. Apply/rollback update cached settings only after successful persistence. This does not make arbitrary learned provider registration trusted; unknown provider side-effect metadata is held at execution.

## Verification and rollback

Regression evidence and exact runs are in [Phase1](../implementation/PHASE_1_REPORT.md). Wire smoke uses a network-disabled disposable container with read-only root, temporary state, safe reads/local writes, denials and restart/replay. Neither mocked handlers nor wire smoke verify institutional submissions, human approval issuance, live graph behavior or cross-client model reasoning.

Rollback is a review of individual source/test/catalog hunks or a separately verified image. Preserve owner configuration, namespaces, databases, reservations and backups. Reverting policy protection restores reproduced unsafe behavior and requires deliberate review; do not automate a security downgrade.
