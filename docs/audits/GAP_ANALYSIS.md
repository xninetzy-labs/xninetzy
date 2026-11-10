# Prioritized implementation backlog

Date: 2026-11-10. Scope/evidence: [current truth](CURRENT_SYSTEM_TRUTH.md), [security register](SECURITY_RISK_REGISTER.md), [tool inventory](TOOL_INVENTORY.md), [routing/context probes](../evaluation/GLOBAL_AGENTIC_BASELINE.md). No feature is declared absent merely because it was not exercised.

Priority is an explicit impact/effort judgment, not an invented failure-frequency metric. Impact, effort and regression risk use low/medium/high. Observed frequency below refers to deterministic reproductions or samples only; production incident rates are UNKNOWN.

| ID | Verified problem | Impact: user / reliability / security | Frequency evidence | Effort / regression risk | Dependency / measurable outcome | Priority / status |
|---|---|---|---|---|---|---|
| GAP-01 | Arbitrary approval integer satisfies context policy helper | high/high/high | Synthetic helper reproduction; external reachability not fully traced | high/high | Principal+operation+payload-bound validation and atomic consumption | P0 OPEN |
| GAP-02 | Baseline explicit unknown side effect defaults to read-only | high/high/high | Deterministic helper reproduction | low/medium | Fail-closed classifier/gate, zero handler calls for malformed classes | P0 FIXED for explicit malformed declarations; omitted/valid caller metadata remains a limit |
| GAP-03 | Lightning persists nested/text synthetic credentials | high/medium/high | 14 failing regressions | low/low | Existing sanitizer + persisted-input assertion | P0 FIXED in tested path |
| GAP-04 | Container command references missing runtime | high/high/medium | Current Dockerfile/source inspection | medium/high | MCP transport and health contract; clean container smoke | P0 release blocker OPEN |
| GAP-05 | Baseline base wheel lacks required LangChain Core | high/high/low | Actual 49-package base install fails startup | medium/medium | Correct existing dependency ownership; fresh wheel lists tools without AI extras | P0 FIXED; actual base installed-wheel smoke passes |
| GAP-06 | Concurrent callers can execute same pending reservation | high/high/medium | 2 failing synthetic regressions | low/medium | Atomic reservation + pending reconciliation | P1 FIXED; payload-sensitive compatibility retained |
| GAP-07 | Flat runtime paths escape checkout; multiple stores exist | high/high/medium | 4 failing root regressions; metadata-only store detection | low/medium | Correct paths and require explicit choice before ambiguous switch | P1 FIXED; no data migrated |
| GAP-08 | Baseline graph worker ignores False acknowledgement and exhausted retries remain claimable | medium/high/low | Failing synthetic acknowledgement and real SQLite exhaustion regressions | medium/medium | Correct retry/outbox markers while SQLite remains available | P1 FIXED tested paths; live recovery/resync unverified |
| GAP-09 | No universal policy gate around public MCP tools | high/high/high | VERIFIED_CODE; per-domain checks incomplete | high/high | Trace representative final/write paths before common interception | P1 OPEN; not a blanket bypass finding |
| GAP-10 | Weak approval lifecycle and changed-payload idempotency semantics | high/high/high | Static service inspection and current contract tests | high/high | Explicit migration/recovery design, concurrency and restart tests | P1 OPEN |
| GAP-11 | 244 tools outside domain groups; output contracts largely untyped | medium/high/medium | Generated 571-tool inventory | medium/medium | Cover critical canonical schemas/ownership incrementally | P1 OPEN |
| GAP-12 | Indonesian research/recovery skill routing fails expected intent | high/medium/low | 8 actual diagnostic requests, not a golden benchmark | medium/medium | Held-out multilingual expected capability sets; no hardcoded answers | P1 OPEN |
| GAP-13 | Nested skills not discovered; metadata contracts conflict | medium/medium/medium | Direct/recursive catalog comparison | medium/high | Backward-compatible metadata/eligibility design; preserve existing names/resources | P1 OPEN |
| GAP-14 | Canonical instructions overclaim authority; validation protects old headings | medium/medium/high | Source/installed comparison | medium/low for repository candidate | Versioned policy contracts and static negative tests; host installation separate | P1 candidate FIXED; host drift OPEN |
| GAP-15 | Baseline noncritical failed workflow reports overall SUCCESS | high/high/low | Four failing executor regressions; persisted fixture | low/medium for status; high for recovery | Existing FAILED aggregate with retained successful steps | P1 status FIXED; complete replay/resume OPEN |
| GAP-16 | Research fetch buffers before cap; DNS validation/use separation | medium/medium/high | VERIFIED_CODE, not proven exploitation | medium/medium | Streaming size/redirect/resolution regression tests | P1 OPEN |
| GAP-17 | Full lint fails; historical docs/tool counts drift | medium/medium/low | 125 Ruff findings; current inventories | medium/low | Fix defined defects in scoped batches, regenerate counts | P2 OPEN |
| GAP-18 | RSS, full golden outcomes, retrieval quality, backup/restore unknown | medium/high/medium | Unexecuted acceptance boundaries | medium/medium | Reproducible fixtures, comparable measured baselines | P2 OPEN |
| GAP-19 | Optional cockpit/new providers/new agents | UNKNOWN | No demonstrated demand or benchmark advantage | high/high | Must show existing capability cannot meet measured need | P3 DEFERRED |

## Cost-benefit decisions

Reuse SQLite, current tool/skill registries, existing sanitizer, MCP adapter and provider factories. The accepted batches add no tool, LLM agent runtime, database or service. Concurrency correctness, truthful checks and data continuity have deterministic tests and small diffs. Prompt reductions are measured text changes only. Expanding orchestration, semantic routing, a dashboard, new vector database or new providers lacks a demonstrated gain relative to maintenance and migration cost, so none is introduced.

See [ADR](../architecture/ADR-001-INCREMENTAL-HARDENING.md) for alternatives, compatibility, test and rollback decisions. Next implementation order: approval authenticity/common execution boundaries; container deployment reliability; live graph reconciliation and workflow safe resume; held-out capability routing and retrieval quality. Minimal bootstrap, projection acknowledgement/retry and aggregate workflow status have verified local fixes. Review each batch against current evidence rather than treating this list as immutable.
