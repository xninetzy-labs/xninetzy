# Local runtime performance baseline

## November15 worker/validator measurement

`VERIFIED_RUNTIME`: same local x86_64 host,8 logical CPUs, Python3.14.5,
explicit CPU/offline embeddings and three synthetic nodes. Each session records
one MCP handshake/discovery and10 warm `datetime_now` reads. The p95 uses nearest
rank (the maximum at n=10), not a reliable population tail estimate. Tests and
builds also ran on this host; these are descriptive samples, not comparable
before/after speedups or SLO acceptance. Projection/model-ready latency is not
included in the handshake metric.

| First opted-in session | Handshake s | Discovery ms | Warm read p50 ms | Warm read sample p95 ms |
|---|---:|---:|---:|---:|
| source/hash | 5.463007 | 253.274 | 6.469 | 12.774 |
| source/cached MiniLM | 4.515969 | 102.051 | 3.829 | 5.08 |
| installed/hash | 5.271832 | 97.18 | 4.557 | 5.241 |
| installed/cached MiniLM | 6.590143 | 203.12 | 4.027 | 7.619 |

Source and frozen installed profiles both retain exactly3 vector rows and an
unchanged snapshot generation after restart/resync. Exact-title top1 passes;
retrieval Recall@k/MRR, citation quality, CPU/RSS, SQLite contention and full
workflow token/latency deltas remain NOT_MEASURED. Model identities are explicit
hash-bow-v1/256 and cached all-MiniLM-L6-v2/384; no semantic-quality comparison
between them is claimed. Global prompt candidates remain1861 cl100k_base tokens,
not reoptimized or installed in this batch.

Root Ruff falls23→0. Pure validator calls change from approval-held to successful
report data under default approval policy, demonstrated by real minimal-container
MCP and61 related tests. Final expanded178 tests overlap that selection; passing
test counts/durations are not performance gains. Full-suite execution exhausted
local disk and did not yield a trustworthy final pass total. Current image and
JSON evidence are in Phase1/3 and CLIENT_CONNECTION_RESULTS.json.

Graph continuation2026-11-15:225 integrated cases pass in53.01s and44 focused worker/privacy cases pass in17.09s (overlapping scopes; not a before/after performance comparison). Correctness gains are fenced stale ACK/failure, exact-revision markers and actual Neo4j weight/properties/outage/retry/duplicate/delete. A fresh frozen non-editable graph-only environment also verifies the live fixture; minimal Python3.11 image remains independent of graph extras. Neo4j fixture limits are1.5 CPUs,1536MiB container memory,256MiB heap/128MiB page cache, with no published host ports. These are configured limits, not measured usage. Request/startup latency, CPU/RSS, lock contention, throughput, context/token changes and semantic retrieval quality remain NOT_MEASURED. Short ownership/version checks and local serialization have an unprofiled cost; no throughput gain is asserted. Live FAISS is NOT_TESTED in the Neo4j harness. Existing machine/runtime details below remain applicable; backend image and exact boundaries are in Phase3.

Backup continuation2026-11-15:116 relevant tests pass in18.89s, including36 backup cases; these overlap earlier selections and are not comparative runtime measurements. The meaningful correctness changes are invalid/corrupt snapshot rejection, containment of manifest-directed retention, preservation of the new same-second snapshot, and actual installed-MCP offline restoration of a captured local task/replay record. Snapshot/restore latency, CPU, RSS, contention and context/token deltas remain NOT_MEASURED. Additional hashing/integrity scans/copies have unprofiled cost on explicit operations; no performance gain is inferred. Same host/minimal Python3.11 profile as the prior workflow checkpoint;663 runtime files match the final artifact. Live FAISS quality/cross-file consistency, external reconciliation and owner restore remain unverified.

Workflow continuation2026-11-15: this batch measures correctness, not a comparative speedup. On the existing host/Python3.14.5 and minimal Python3.11 image,211 combined tests pass in242.59s; after the last scoped privacy fix,123 affected cases pass in18.14s (overlapping/different scopes). These durations are not before/after request latency. Tools remain571; no prompt/skill/model/provider or dependency change is introduced.

| Measure | Before | Verified current result | Interpretation |
|---|---|---|---|
| Completed-plan handler invocations in fixture | Two on repeated execution | One, followed by stored-result replay | Deterministic duplicate-effect correction, not throughput |
| Original resume identity | New plan rebuilt from old message | Same workflow ID/typed checkpoint | No regenerated workflow in installed-MCP smoke |
| Interrupted controlled write/read flow | Safe restart unverified | Actual fixture-process kill/resume retains single completed effect | Local POSIX/SQLite only |
| Installed-MCP recovery fixture | NOT_MEASURED |2 intended workflows/2 synthetic effects; successful-write ledger unchanged | Synthetic writes and canonical local reads; not live external delivery |
| Request p50/p95, startup delta, CPU, RSS, lock contention, context/token cost | NOT_MEASURED | NOT_MEASURED | No performance gain/SLO or agent-quality percentage claimed |

State serialization and additional short commits/one local lock descriptor have a cost that remains unprofiled. Final artifact663-file parity and nine SDK source probes establish packaging/transport scope only. Exact evidence and rollback are in [Phase3](../implementation/PHASE_3_REPORT.md) and CLIENT_CONNECTION_RESULTS.json.

Internal/domain continuation:361 relevant regression cases pass in225.86s;12 packaging checks pass in0.29s. These selections differ from earlier836/98 and are not performance comparisons or summed task outcomes. Artifact freshness changes from a verified stale installed module to663 matching runtime files; numeric request latency/RSS/CPU/build-time deltas are NOT_MEASURED. Own-project reinstall/parity adds build/verification work only and retains dependency caching. Tools remain571 with unchanged policy counts and no prompt/skill/model change. No native client task-quality or approval-UX improvement percentage is inferred.

## Measured Phase1 redaction correction

An actual expanded-test duration identified27.03s in the input/output budget test. A separate one-sample-per-size experiment isolated repeated greedy local-identifier matching in `redact_chat_ids_in_text`: an unrelated long token followed by `@example.com`, then a legitimate synthetic `@chat.local` identifier. Runtime redaction now scans fixed domain markers and walks adjacent tokens once. The same synthetic shape on the same host/interpreter produced:

| Fixture characters | Before seconds | After seconds |
|---:|---:|---:|
|1041|0.007325|0.000029|
|2041|0.034527|0.000011|
|4041|0.131522|0.000010|
|8041|0.552502|0.000010|
|40041|NOT_MEASURED in direct experiment|0.000026|

Each row is n=1 with uncontrolled background load; microsecond values are noisy and are not p95, confidence intervals, production latency or whole-system speedup. Before the correction, a subprocess processing40041 characters exceeded its2s regression budget; after, all affected redaction/boundary tests passed.2000 seeded short compatibility cases match previous behavior. The final affected runtime selection passes98 tests in24.56s, including two real subprocess MCP tests; do not compare this different selection to the836-test total. Other runtime performance/cost metrics remain NOT_MEASURED.

Phase1 continuation2026-11-14: hardware remains x86_64 AMD Ryzen3 5300U,4 cores/8 threads (8 logical CPUs available); host Python3.14.5, minimal image Python3.11, SDK1.30.0, STDIO protocol2025-11-25. The machine also runs unrelated owner workloads; test durations are not controlled performance comparisons. New validation/reservation/typing boundaries have no measured before/after latency, RSS, CPU or contention gain: NOT_MEASURED. Prompt text remains1861 cl100k_base tokens (353+1035+275+198), re-encoded locally, with host instructions unchanged. Current client probes and isolated container checks are in CLIENT_CONNECTION_RESULTS.json; SDK probe duration includes startup/discovery/read and is not a comparable p95/SLO. Higher regression counts are broader correctness coverage, not an agent task-completion rate.

Recorded 2026-11-10. Evidence: VERIFIED_RUNTIME for measurements below. Existing environment, no paid provider calls; automatic memory/graph/improvement, Lightning and optional background services disabled for smoke. SQLite and writable paths point to `/tmp/xn-stdio-audit-*`; deployment `.env` disabled before resolving Settings. No Neo4j or embedding model required.

| Environment | Value |
|---|---|
| CPU | AMD Ryzen 3 5300U with Radeon Graphics |
| Logical CPUs | 8 |
| Host physical memory | 18,695,122,944 bytes |
| Kernel | Linux 6.8.0-149-generic |
| Python / MCP SDK | 3.14.5 / 1.30.0 |
| Workload | One fresh STDIO subprocess; initialize; list all tools; ten sequential `datetime_now` calls |
| Negotiated protocol | 2025-11-25 |

| Metric | Before candidate | Observed candidate checkpoint | Change |
|---|---|---|---|
| Process launch through initialize | NOT_MEASURED | 4.960 s, n=1 | NOT_MEASURED |
| Full 571-tool discovery | NOT_MEASURED | 45 ms, n=1 | NOT_MEASURED |
| First safe read | NOT_MEASURED | 15.015 ms | NOT_MEASURED |
| Subsequent 9 safe reads | NOT_MEASURED | 3.044–4.338 ms, median 3.514 ms | NOT_MEASURED |
| External network latency | NOT_MEASURED | No external request in workload | NOT_MEASURED |
| RSS / CPU usage / SQLite contention | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| Retrieval Recall@5 / citation validity | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| Full context/model token use | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |

Individual read samples in milliseconds: `15.014514, 4.337826, 3.294666, 3.088968, 3.044266, 3.413475, 3.751604, 3.514125, 3.516290, 3.571888`.

The RSS probe returned zero while the child was still alive, so it is invalid and excluded. These tiny samples do not support a p95, confidence interval, throughput claim or improvement percentage. The under-500ms metadata target is not accepted as a production SLO from this sample. Background hooks, real owner data, concurrent clients, graph/model initialization and external requests would change costs.

[Global baseline](GLOBAL_AGENTIC_BASELINE.md) records actual cl100k_base prompt text counts and eight skill-selector probes separately. Text-token reductions do not establish lower model billing or higher task success. No architectural complexity or caching optimization was introduced based on these sparse measurements.

## Hardening continuation comparison

| Metric | Previous reported baseline | Current evidence | Interpretation |
|---|---|---|---|
| Selected passing tests | 476 | 781 in283.29s | Broader scope; not a comparable success-rate metric |
| Canonical full Ruff findings | 125 | 0 | Same rules/config; no suppressions added |
| Embedding API warning | 1 visible warning | No warning reported in expanded run | Current dimension API used; no warning filter added |
| Codex referenced candidate text | 1861 cl100k tokens | 1861, re-tokenized locally | No further text-size change; model billing/quality unmeasured |
| Candidate client transport | Previously unverified | 9 entries/8 hosts: handshake,571 tools, safe read | Temporary state, SDK probes; not native GUI/owner rollout |
| Shared-store configuration | Awaited explicit selection | Owner selected A;9 entries installed; post-install transport9/9 and zero-change replan | Protected backups; owner data/global prompts unchanged; GUI reload/owner-state runtime unverified |
| Approval authenticity | Unverified | Known self-approval/forged-ID path contained | Independent trusted owner channel still absent; not H1 completion |
| Container operation | No current runtime verification | Python3.11 minimal image:571 tools, read/write/restart/persist/replay pass | Disposable state/network disabled; live providers and interrupted external workflows unverified |
| Release diagnostics | Four checks hardcoded PASS/stale SDK version | Shared validators executed;13 regressions pass, actual image shows1.30.0 | Correctness gain; latency difference NOT_MEASURED |
| Retrieval quality / RSS / CPU / SQLite contention | NOT_MEASURED | NOT_MEASURED | No invented comparison |

[Client probe evidence](CLIENT_CONNECTION_RESULTS.json) records per-entry5–11s-like cold-session totals. Those include process startup, registration, discovery and a read, and are not directly comparable to the older initialize-only4.960s value. No speedup or p95 is inferred from one run per configuration. Container results are recorded independently with their image/runtime provenance.

November14 correctness observations: synchronized duplicate approval fixture invoked its synthetic effect twice before, once after the conditional decision claim. This is a deterministic safety regression, not a throughput gain or external exactly-once proof. Five focused approval and125 related tests pass; current client/approval selection21 passes. OpenCode2 schema/disabled migration has16 client cases; latest SDK9/9 passes, while native isolated OpenCode still reports no servers. Active Codex safe reads now work. Native task success rate, comparative latency/RSS, external recovery and context-quality improvements remain NOT_MEASURED.
