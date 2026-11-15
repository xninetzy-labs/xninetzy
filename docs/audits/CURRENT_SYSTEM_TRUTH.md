# Current system truth

Current2026-11-15 vector/validator continuation (`VERIFIED_CODE`, `VERIFIED_TEST`,
`VERIFIED_RUNTIME`): existing FAISS now uses checked atomic two-slot snapshots,
text/model fingerprints, replay deduplication and scoped caches. Hybrid retrieval
rejects stale text vectors before fusion. The existing projection loop is wired
to MCP lifespan only when both graph and explicit worker flags are enabled;
owner defaults remain unchanged. Source and frozen installed STDIO smokes pass
with real FAISS/hash256 and offline cached MiniLM384; three synthetic nodes do
not establish general retrieval quality. Legacy state is preserved and held.

Three pure `skill_validate_*` writing checks are corrected WRITE→READ. They
execute under default approval mode without mutation keys, preserve findings
and retain explicit restrictions.571 canonical tools now comprise136 READ/
6 DRAFT/406 WRITE/23 FINAL. Root Ruff is zero. Final relevant selection178 passes;
separate outcome-fixture/negative checks2 pass. Full regression remains incomplete
after disk exhaustion; independent approval and native all-client parity remain
unverified. No host configuration or owner database/index was modified. Older
counts/artifacts below are historical to their batches. See Phase1/3 and latest
baseline/results for exact source, tests, commands, image and rollback.

Graph continuation2026-11-15 (`VERIFIED_TEST` / `VERIFIED_RUNTIME`): existing outbox ownership is fenced to persisted attempts/unexpired leases; sync markers bind canonical version/hash/status. Current edge weight/properties and active endpoints are projected; unknown operations fail, local ticks serialize and provider error payloads are omitted from application logs/outbox.225 relevant cases pass. Real Neo4j5.26 tests pass from source and a fresh frozen non-editable graph-only installation (663-file parity) using an owned internal-network fixture. Neo4j outage retains SQLite/FTS and retries after restart; duplicate relationships/deletion are checked through actual Cypher. FAISS is explicitly stubbed/NOT_TESTED in that harness. Minimal image `xninetzy:graph-hardening-20261115` independently passes previous wire/recovery/backup smokes without optional services. [Phase3](../implementation/PHASE_3_REPORT.md) records exact evidence. No owner graph/configuration or background scheduler was changed; readiness remains NOT_READY.

Backup continuation2026-11-15 (`VERIFIED_TEST` / `VERIFIED_RUNTIME`): existing service now validates v1 file sets/hash/size/SQLite integrity, refuses symlinks/journals, derives retention targets from actual directories and preserves a pre-restore snapshot. The baseline service deleted an unrelated synthetic directory through manifest `path` in an isolated reproduction; current guards prevent that path.116 relevant tests pass, including36 backup cases. The final installed minimal image `xninetzy:backup-hardening-20261115` passes663-file parity and actual MCP online snapshot/offline restore/restart/local replay, plus prior workflow/general smokes. Exact artifact/evidence is in [Phase3](../implementation/PHASE_3_REPORT.md). Owner data/config/services remain unchanged; no independent positive approval or external/cross-file exactly-once guarantee.

Latest workflow continuation2026-11-15 (`VERIFIED_TEST` / `VERIFIED_RUNTIME`): exact-plan typed checkpoints, local concurrency exclusion, policy/cancellation/deadline checks and uncertain-mutation holds now operate in the existing engine. Controlled fixture-process SIGKILL recovery and installed-wheel MCP resume pass without repeating completed writes.211 combined tests preceded a final privacy correction;123 affected tests then pass, including59 workflow cases (overlapping counts). Current minimal image `xninetzy:workflow-recovery-20261115` passes663-file parity, recovery and general STDIO smoke. Nine fresh SDK source probes pass; no host configuration or owner store changed. See [Phase3](../implementation/PHASE_3_REPORT.md) for exact artifact/commands and [workflow contract](../architecture/AGENTIC_WORKFLOW.md) for POSIX/trusted-directory/cooperative-execution limits. Independent approval, live services, native all-client parity and production readiness remain open.

Latest internal/domain continuation2026-11-14: service-level identity-only approval and legacy-approved reuse are held; HEBAT owner upload and confirm-only removal no longer bypass domain policy. Notifications no longer promise obsolete WhatsApp approval and do not log private failure payloads.361 relevant tests and12 packaging checks pass. Outside-checkout execution exposed stale wheel code in an intermediate candidate; the rebuilt `xninetzy:approval-hardening-20261114` image now verifies663 runtime files and actual installed-service denial plus STDIO local read/write/restart/replay. The earlier copied-source profile was verified, but tool counts/import success did not establish installed-code freshness. Approval issuance/consumption, native host parity and live service recovery remain open; production is NOT_READY.

Latest source/runtime update2026-11-14: [Phase1](../implementation/PHASE_1_REPORT.md) adds the canonical571-policy catalog and enforced STDIO gateway. Current risk distribution is133 READ/6 DRAFT/409 WRITE/23 FINAL; all23 consequential operations and unknown policies are held. Write calls preserve owner mode and require scoped payload-bound idempotency. HTTP, including loopback, is unavailable without independent authentication and fails before DB initialization. Learned configuration cannot override data selection, identity or permissions. The rebuilt minimal image passes isolated local write/restart/replay and wire denial checks. These supersede earlier descriptions of metadata-only MCP policy and available loopback HTTP; they do not establish independent human approval, all-domain semantics or production readiness. Canonical CI Ruff scope is clean; root lint also finds23 preserved skill/vendor issues outside that scope.

Initial audit 2026-11-10 against `main`, HEAD `2d0f13f`; continuation updated 2026-11-11 from `74ff58b` plus local patches. Status: **PARTIAL AUDIT; NOT_READY for a production release**. This is the entrypoint for the current evidence set. Historical reports remain available but are not current acceptance evidence.

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
| Interfaces | VERIFIED_CODE / VERIFIED_TEST: MCP STDIO; all HTTP rejected before initialization pending independent authentication; supervisor/plan-runner entrypoints still declared | No WhatsApp/REST restoration justified |
| Tools | VERIFIED_RUNTIME: 571 unique registered tools; 34 groups; 244 tools have no group membership | Historical 339/343/544 counts are stale for this checkout |
| Policies | VERIFIED_CODE / VERIFIED_TEST: canonical571-name catalog plus MCP principal/owner-mode/risk/idempotency gateway; unknown and all23 FINAL held | Domain semantics/internal/background paths still need complete coverage; denial does not implement authentic approval |
| Approval containment | VERIFIED_TEST: model-facing approval leaves requests pending; irreversible context execution rejects unverified approval channels | Independent owner approval, atomic consumption and universal domain coverage remain release blockers |
| Approval concurrency | VERIFIED_TEST: service decision update is conditional on pending; stale decisions cannot overwrite winner, interrupted outcome is unverified without rerun | Covers decision claim/auto-action fixtures, not genuine owner authentication or external single-use consumption |
| MCP protocol | VERIFIED_RUNTIME: installed MCP 1.30.0 negotiates `2025-11-25`, lists 571 tools and completes ten datetime reads | This does not establish 2026-07-28 compatibility or native client parity |
| State | VERIFIED_CODE: SQLite is canonical; graph/indexes are projections; graph services optional | No new database is justified by this audit |
| Graph projection | VERIFIED_TEST / VERIFIED_RUNTIME: local claim/marker fencing and actual isolated Neo4j outage/retry/duplicate/delete pass | Requires cooperating updated local workers; lifecycle activation, owner-wide reconciliation, multi-host safety and live FAISS durability remain unverified |
| Backup/restore | VERIFIED_TEST / VERIFIED_RUNTIME: online committed-WAL snapshot, offline verified staging/safety capture, installed-MCP restore/restart and saved local replay pass | Owner must stop every client/worker; optional vector files are not atomic with SQLite; production restore and subsequent external effect reconciliation remain unverified |
| Skills | VERIFIED_RUNTIME: 125 direct built-in definitions, 123 eligible, 2 rejected historical underscore mirrors; 166 recursive files | Recursive file count and runtime availability are different quantities |
| Agent behavior | VERIFIED_CODE: host performs conversation/planning; existing workflow/harness/routing/feedback modules remain | Controlled workflow recovery is now tested; general autonomous outcome quality/multi-agent advantage remains unknown |
| Workflow recovery | VERIFIED_TEST / VERIFIED_RUNTIME: original plan/state resumed, completed writes reused, ambiguous write held; real fixture-process interruption and installed MCP checks pass | Cooperating updated local POSIX runtimes only; no universal domain verification, mixed-version or external exactly-once claim |
| Instructions | VERIFIED_CODE: installed L0/L1 authority and override conflicts; corrected repository candidate with hashes | Shared global prompt files remain unchanged; prompt installation is separate from authorized MCP connection repairs |
| Minimal install | VERIFIED_RUNTIME: initial wheel failed on missing mandatory dependency; corrected frozen base wheel lists 571 tools and runs datetime with optional packages absent | Existing dependency moved to base; optional processing imports deferred; 49→64 minimal distributions, locked versions unchanged |
| Deployment | VERIFIED_RUNTIME: Python3.11 installed wheel passes parity, STDIO read/write/restart/replay and exact-plan recovery with disposable state | Owner deployment, backup/restore, live providers and external reconciliation unverified |
| Local clients | VERIFIED_RUNTIME: A installed in nine entries/eight host profiles;9/9 latest isolated SDK probes pass; active Codex executes MCP safe reads, earlier native Claude isolated health passed | OpenCode2 schema/disabled migration installed with backups; native isolated list still reports no servers (UNKNOWN cause). Other GUI/parity and owner-state mutation/recovery remain unverified |
| Quality | VERIFIED_TEST: current211 combined/123 scoped selections pass with overlap; canonical Ruff is clean | Full collected suite not executed;23 preserved root skill/vendor findings outside canonical CI scope; no user-completion percentage inferred |
| Release checks | VERIFIED_TEST: supervisor uses shared validators;13 regressions prohibit hardcoded successful results | Guard checks cannot certify independent approval or production readiness |

## Audit coverage and artifacts

- [Architecture and ownership map](ARCHITECTURE_MAP.md): 18+ responsibilities, actual dependencies, wiring and state.
- [Capability matrix](CAPABILITY_MATRIX.md): logical agents mapped to existing services, with acceptance gaps.
- [Tool inventory](TOOL_INVENTORY.md) and [machine-readable schemas](tool_inventory.json): generated from current registry without handler execution.
- [Instruction inventory and client matrix](GLOBAL_INSTRUCTION_INVENTORY.md), [prompt conflicts](PROMPT_CONFLICT_REPORT.md), [skill validation](SKILL_VALIDATION_REPORT.md).
- [Test evidence](BASELINE_TEST_RESULTS.md), [local performance](../evaluation/PERFORMANCE_BASELINE.md), [context/routing baseline](../evaluation/GLOBAL_AGENTIC_BASELINE.md).
- [Security register](SECURITY_RISK_REGISTER.md), [prioritized backlog](GAP_ANALYSIS.md), [implementation checkpoint](../implementation/PHASE_0_REPORT.md).
- [Workflow/projection batches](../implementation/PHASE_3_REPORT.md): truthful aggregate status, controlled durable local recovery and bounded projection retries; live graph/external recovery and complete domain verification remain unverified.

## Documentation drift

`tests/baseline/REPORT.md` is HISTORICAL (September), including its claims of 339/343 tools, 29 failures and production status. `docs/prompt-injection-core/SUB-A-COMPLETE.md` and `SMOKE-TEST.md` describe the previous prompt design; the current contract is `manifest.json` plus the actual canonical files and new validator. `docs/SKILLS_INDEX.md` count claims predate the current inventory. Deleted `CHANGELOG.md`, `PROVIDERS.md`, `KNOWN_ISSUES.md` and other initially deleted files are owner workspace changes, not this audit's cleanup.

## Boundaries

No commits/pushes, messages, submissions, production deployment, host instruction installation, credential changes, production data migration, portal authentication, or live external security tests were performed. Container operation uses a disposable fixture. Existing deletions and untracked skill folders were preserved. New tests use temporary SQLite/files and synthetic secrets. No historical telemetry or personal memory contents were copied into reports.

Full-suite execution, owner backup/restore, live projection/external recovery, all output schemas, all approval paths, held-out retrieval quality,50 golden task outcomes, HTTP authentication/origin checks and native cross-client workflows remain unverified. Controlled local backup/restore has the scoped evidence above. The next eligible work is governed by the backlog, not the order of features in historical roadmaps.
