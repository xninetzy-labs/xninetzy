# Local runtime performance baseline

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
