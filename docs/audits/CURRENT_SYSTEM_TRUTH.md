# Current system truth

Recorded 2026-11-10 against `main`, initial HEAD `2d0f13f`. Status: **PARTIAL AUDIT; NOT_READY for a production release**. This is the entrypoint for the current evidence set. Historical reports remain available but are not current acceptance evidence.

The owner requested repository-wide audit and incremental enhancement, including the global instruction/skill workstream. Work performed here covers architecture reconstruction, registry inspection, instruction/skill discovery, isolated test baselines, a real STDIO smoke, a minimal installation attempt, and bounded implementation batches. It does not establish completion of all phases or all end-to-end owner journeys.

## Evidence vocabulary

| Label | Meaning |
|---|---|
| VERIFIED_CODE | Inspected current implementation, with source references |
| VERIFIED_TEST | Reproducible passing test; mocks establish fixture behavior only |
| VERIFIED_RUNTIME | Actual local execution with stated configuration |
| DOCUMENTED_ONLY | Intent described in a document without execution evidence |
| HISTORICAL | Previous snapshot, not current truth |
| INFERRED | Architectural interpretation needing validation |
| UNKNOWN | Insufficient evidence |

## Current facts

| Area | Current evidence | Implication |
|---|---|---|
| Layout | VERIFIED_CODE: Python package is `xninetzy/`; `pyproject.toml` at root | Old `services/ai/app/` instructions must not drive source discovery |
| Interfaces | VERIFIED_CODE: MCP STDIO plus loopback-only Streamable HTTP; supervisor and plan-runner entrypoints still declared | Preserve existing compatibility; no WhatsApp restoration justified |
| Tools | VERIFIED_RUNTIME: 571 unique registered tools; 34 groups; 244 tools have no group membership | Historical 339/343/544 counts are stale for this checkout |
| Policies | VERIFIED_CODE: manifest relies partly on name heuristics; public MCP adapter calls domain tools directly | Metadata alone does not prove independent authorization/idempotency |
| MCP protocol | VERIFIED_RUNTIME: installed MCP 1.30.0 negotiates `2025-11-25`, lists 571 tools and completes ten datetime reads | This does not establish 2026-07-28 compatibility or native client parity |
| State | VERIFIED_CODE: SQLite is canonical; graph/indexes are projections; graph services optional | No new database is justified by this audit |
| Skills | VERIFIED_RUNTIME: 125 direct built-in definitions, 123 eligible, 2 rejected historical underscore mirrors; 166 recursive files | Recursive file count and runtime availability are different quantities |
| Agent behavior | VERIFIED_CODE: host performs conversation/planning; workflow, harness, routing and feedback modules exist | Existence is not demonstrated autonomous task completion or multi-agent improvement |
| Instructions | VERIFIED_CODE: installed L0/L1 authority and override conflicts; corrected repository candidate with hashes | Host configuration remains unchanged; candidate requires reviewed installation |
| Minimal install | VERIFIED_RUNTIME: initial wheel failed on missing mandatory dependency; corrected frozen base wheel lists 571 tools and runs datetime with optional packages absent | Existing dependency moved to base; optional processing imports deferred; 49→64 minimal distributions, locked versions unchanged |
| Deployment | VERIFIED_CODE: Dockerfile points to absent `xninetzy.main:app`; Compose checks old REST `/health` | Container release is blocked; do not infer deployability from STDIO success |

## Audit coverage and artifacts

- [Architecture and ownership map](ARCHITECTURE_MAP.md): 18+ responsibilities, actual dependencies, wiring and state.
- [Capability matrix](CAPABILITY_MATRIX.md): logical agents mapped to existing services, with acceptance gaps.
- [Tool inventory](TOOL_INVENTORY.md) and [machine-readable schemas](tool_inventory.json): generated from current registry without handler execution.
- [Instruction inventory and client matrix](GLOBAL_INSTRUCTION_INVENTORY.md), [prompt conflicts](PROMPT_CONFLICT_REPORT.md), [skill validation](SKILL_VALIDATION_REPORT.md).
- [Test evidence](BASELINE_TEST_RESULTS.md), [local performance](../evaluation/PERFORMANCE_BASELINE.md), [context/routing baseline](../evaluation/GLOBAL_AGENTIC_BASELINE.md).
- [Security register](SECURITY_RISK_REGISTER.md), [prioritized backlog](GAP_ANALYSIS.md), [implementation checkpoint](../implementation/PHASE_0_REPORT.md).
- [Workflow/projection batches](../implementation/PHASE_3_REPORT.md): truthful persisted aggregate status and acknowledged, bounded projection retries; complete durable orchestration remains unverified.

## Documentation drift

`tests/baseline/REPORT.md` is HISTORICAL (September), including its claims of 339/343 tools, 29 failures and production status. `docs/prompt-injection-core/SUB-A-COMPLETE.md` and `SMOKE-TEST.md` describe the previous prompt design; the current contract is `manifest.json` plus the actual canonical files and new validator. `docs/SKILLS_INDEX.md` count claims predate the current inventory. Deleted `CHANGELOG.md`, `PROVIDERS.md`, `KNOWN_ISSUES.md` and other initially deleted files are owner workspace changes, not this audit's cleanup.

## Boundaries

No commits/pushes, messages, submissions, deployment, host instruction installation, credential changes, production data migration, portal authentication, or live external security tests were performed. Existing deletions and untracked skill folders were preserved. New tests use temporary SQLite/files and synthetic secrets. No historical telemetry or personal memory contents were copied into reports.

Full-suite execution, backup/restore, all output schemas, all approval paths, held-out retrieval quality, 50 golden task outcomes, HTTP authentication/origin checks and cross-client workflows remain unverified. The next eligible work is governed by the backlog, not the order of features in historical roadmaps.
