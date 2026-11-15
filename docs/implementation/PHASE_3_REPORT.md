# Phase 3: truthful workflow and projection outcomes

## FAISS snapshots and opt-in MCP worker, 2026-11-15

`VERIFIED_CODE` / `VERIFIED_TEST`: the existing FAISS store previously appended
duplicates on retry, could acknowledge failed saves, reused directory-unscoped
cache state and silently rebuilt damaged state. Initial storage regressions
reproduced10 failures. Embedding identity regressions reproduced3 failures;
lifespan regressions5; subsequent generation/freshness regressions3 failures/1 pass.

The existing store now clones the committed index, validates vectors, writes an
inactive checked index/map slot privately, fsyncs and atomically publishes one
manifest pointer last. Two bounded disk slots preserve the previous commit on
pre-publication failure. Same-key/same-text replay reuses the existing row across
threads/processes/restarts. Hashes, dimensions, actual provider/model/normalization
and generation are checked before use. Stale rows are excluded; hybrid fusion
also requires the vector text hash to match current canonical text. Stale semantic
data cannot suppress a fresh lexical fallback. Missing reads do not create dirs.

Legacy `graph.index`/`graph_map.json` and corrupted state are preserved and held
for a deliberate reviewed rebuild. No owner index was rebuilt. The embedding
model cache tracks configured provider/model and reports safe exception types;
a requested neural graph index cannot silently become a hash-vector index.
The preexisting general knowledge fallback remains a separate compatibility
boundary; this change does not prove every vector store uses the new format.

`GRAPH_SYNC_WORKER_ENABLED=false` is a new explicit opt-in. Both it and
`GRAPHRAG_V3_ENABLED` must be true for MCP lifespan activation. Startup is lazy;
shutdown stops later dispatch, releases only undispatched owned claims without
spending retry attempts, and retains live synchronous work until it finishes.
Runtime stats expose configured/running/inflight counts. Cancellation is
cooperative and cannot terminate an entered provider call. No owner flag changes.

Files: `xninetzy/core/config.py`, `interfaces/mcp_server.py`,
`os/knowledge/embeddings.py`, `os/graph/v3/{faiss_store,sqlite_store,projection_worker,
graph_service,graph_tools_v3,hybrid_retriever}.py`; regression coverage in
`tests/os/graph/{test_faiss_durability,test_hybrid_freshness}.py`,
`tests/os/knowledge/test_embedding_dimensions.py` and
`tests/interfaces/test_graph_lifespan.py`; `scripts/smoke_graph_worker.py` and CI.
No table migration, new framework or dependency is introduced.

Intermediate integrated lifecycle/worker/vector selection72 passes; subsequent
storage/freshness/lifespan/dimension selection42 passes in7.40s (overlapping).
The latter includes real FAISS, concurrent subprocess writers, failed publication,
corruption, provider mismatch, stale generations, shutdown and successor-lease
fencing. See the latest baseline report for the final expanded selection.

`VERIFIED_RUNTIME`: source and a fresh frozen non-editable embeddings installation
both pass real STDIO MCP handshake/discovery, disabled-worker isolation, automatic
outbox drain, graceful session shutdown, restart/resync and unchanged vector
count/generation. Each profile uses three synthetic canonical nodes and571 tools.
Explicit hash vectors are256-dimensional; the already cached offline
`sentence-transformers/all-MiniLM-L6-v2` is384-dimensional with no model download.
Exact-title top1 passes. This is not a labeled semantic-quality benchmark.
The installed runtime matches663 source files. Its temporary environment was
removed after completion to recover disk space.

Current minimal artifact: `xninetzy:validator-fix-20261115`,
`sha256:650658c1641d8ed3575c1f6db4e98554ec9435be40d9f0fbc3f5238a0672bff2`,
Python3.11/non-root1000:1000,663-file parity. Actual wire checks pass read/write,
idempotent restart, modified-payload denial and the validator repair described
in Phase1, using temporary data, read-only root and network none. No owner
deployment is performed. The earlier `vector-lifecycle` artifact also passed
the installed workflow and backup smokes before the three policy corrections.

The final `validator-fix` image additionally passes both actual installed MCP
workflow recovery and online snapshot/offline restore/restart/replay smokes.
Final graph/lifespan/embedding/validator/gateway/deployment/docs selection:
178 passed in192.49s with no warning/skips reported. Separate trust-outcome
fixture checks2 pass; counts must not be summed with overlapping earlier runs.
`yarn build` also builds34 documentation pages. The full2888-case attempt
did not complete after disk exhaustion; it is not replaced by these selections.

Rollback: preserve canonical SQLite, all snapshot slots/manifests and legacy
indexes. Disable the opt-in worker and stop cooperating readers/writers before
reviewing a runtime rollback; old FAISS code cannot read the new snapshot format.
Do not downgrade against the live projection or delete it as cleanup. Hashes
detect integrity errors, not malicious local-writer authenticity. Local POSIX
cooperating processes are assumed. Clone RAM/disk cost, full owner reconciliation,
all native clients, independently authenticated approval and full-suite readiness
remain open. See runbook for safe activation and evidence limitations.

## Graph projection ownership and live recovery — 2026-11-15

**Controlled local Neo4j recovery verified; release remains PARTIAL / NOT_READY.** Continued from the backup checkpoint, preserving the existing SQLite/outbox/Neo4j architecture, owner data/configuration and earlier patches. No new database, application agent, provider, tool, schema or runtime dependency. The already declared optional graph extra and existing official Neo4j5.26 deployment profile supply the isolated backend test.

| Finding | Evidence | Implemented behavior / limit |
|---|---|---|
| Claims return pre-claim fields; old worker can finish/fail a reclaimed event by ID | VERIFIED_TEST: initial12 failures/19 passes include actual SQLite takeover during provider callback | Return persisted attempt/lease; validate before dispatch; conditional finalization requires matching current unexpired processing lease |
| Synced markers can describe a newer canonical revision than the acknowledged write | VERIFIED_TEST: update during callback and marker invalidation regressions | Commit outbox ACK plus exact version/hash/status markers in one short transaction; canonical changes/deletions clear stale markers |
| Edge projection loses weight/properties and can recreate a deleted endpoint | VERIFIED_TEST: canonical edge/endpoint cases; VERIFIED_RUNTIME: actual Cypher verifies2.75 weight and fixture properties | Read current canonical edge with active endpoints; old event payload no longer overrides domain state |
| Unknown operations silently complete; overlapping local ticks can run providers | VERIFIED_TEST: poison operations, ownership loss, concurrent threads and lock symlink fixtures | Unknown operations fail with bounded retries; nonblocking POSIX lock serializes cooperating updated ticks; no SQL transaction spans provider work |
| Provider messages/auth-file paths leak into logs/outbox | VERIFIED_TEST: worker regression plus9 failing backend privacy cases | Known safe ACK failures or exception types only; historical logs untouched; provider data is not an instruction/permission source |
| Worker silently creates an empty file when canonical SQLite is missing | VERIFIED_TEST:1 failing regression in0.72s creates an unexpected temporary database | Reject unavailable canonical database before locking/connection; no new state initialized by a projection tick |

Exact implementation files: `xninetzy/os/graph/v3/sqlite_store.py`, `projection_worker.py`, `neo4j_store.py`, `tests/os/graph/test_projection_worker.py`, new `tests/os/graph/test_neo4j_privacy.py`, new `scripts/smoke_graph_projection.py`, `.github/workflows/quality-gates.yml`. Existing audit/architecture/evaluation/release/runbook checkpoints and structured evidence are updated. Existing outbox attempt/lease/version/hash fields are reused; no migration or row reset. Internal finalizers without a valid claim return false; public MCP names/parameters remain unchanged. Tick stats add `lease_lost`/`deferred` only when applicable, without falsely counting completion. Old direct Python helpers remain for compatibility; mixed old/new workers are not certified.

Final relevant selection: **225 passed in53.01s**, covering graph, backup, workflow, DB, MCP boundary, installed/deployment checks and internal-approval regression. Final focused worker/privacy selection also passed44 in17.09s before the combined run. Earlier58 graph cases in132.41s preceded the backend privacy patch; all counts overlap and are not summed. No final failure/skip/xfail/warning reported. Initial12 regressions failed in33.68s;9 backend privacy regressions failed in0.18s, then passed after type-only logging changes. These are fixture checks, not universal production security certification.

The preceding224-case run passed in50.23s before the final missing-database guard/regression. The final225-case run and rebuilt/rechecked artifact include it. Counts are not summed. The earlier focused44-case run likewise predates that added case; the final integrated selection covers all36 worker and9 backend privacy cases. The intermediate minimal image6bd6a79e is retained as historical evidence in structured results, not the final candidate.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest \
  tests/os/graph tests/os/backup tests/workflow tests/db \
  tests/interfaces/test_execution_boundary.py tests/architecture/test_container_deployment.py \
  tests/tools/test_installed_package.py tests/os/hitl/test_internal_approval_boundary.py -q
docker pull neo4j:5.26-community
.venv/bin/python scripts/smoke_graph_projection.py
docker build --progress=plain -t xninetzy:graph-hardening-20261115 .
```

Live runtime: official backend `neo4j:5.26-community`, resolved image `sha256:577eb43120e8688e62e753e962c47d30044ecaa95147ee5386c29f226b878008`, on a temporary internal Docker bridge with no published host port or owner mount. The Linux host reaches only the exact owned container's private address. Synthetic authentication stays in a0600 temporary env file. Container UID7474, capabilities dropped, privilege escalation disabled, CPU1.5 and memory1536MiB caps; its synthetic anonymous volumes/network/container are removed by owned IDs. Two early harness attempts found internal-bridge port publishing unavailable on this host; they failed and cleaned up, not counted as graph passes. The final harness uses the private fixture address instead.

The source live trial passes before the last missing-database guard; a fresh frozen non-editable graph-only installation is then rebuilt/rechecked against final source (host Python3.14.5, Neo4j driver6.2.0,663-file parity). It passes actual node/edge Cypher, exact weight/properties, duplicate resync without duplicate relationship, backend stop, retained failed event/canonical SQLite+FTS reads, backend restart/retry and node/relationship deletion. The broken pool is explicitly closed before the failed connectivity probe; this is a real backend outage, not proof of mid-transaction crash recovery. FAISS is explicitly stubbed only in this Neo4j harness and reported NOT_TESTED; no model or embedding is downloaded. Expected outage stderr contains ServiceUnavailable type and a safe ACK failure only.

Final minimal Python3.11 image `xninetzy:graph-hardening-20261115`, ID `sha256:ecbc8096b2fd9ec3f35cc0531fbdbc201b9742cf8b2e575165848e02e6bda3fb`, passes663-file installed parity, actual MCP backup/restore, workflow recovery and general571-tool read/write/restart/replay/denial smoke without optional graph services/network/owner mounts. This separately proves the graph extra remains optional. CI adds an independent graph-only installed profile/live fixture job; remote Actions and that Python3.11 enhanced job remain unexecuted here. Canonical Ruff/diff/prompt-integrity checks pass. Machine evidence: `graph_projection_continuation` in `docs/evaluation/CLIENT_CONNECTION_RESULTS.json`.

Impact: stale ACKs/failures no longer alter a successor lease; stale canonical markers are not advertised as current; real relation properties and bounded outage recovery pass. Startup/request latency, CPU/RSS usage, throughput, context/token delta and retrieval-quality gains are NOT_MEASURED. Additional short SQLite checks, serialization lock and marker commits have unprofiled cost; configured container limits are not resource measurements.

Limits/rollback: the loop still needs explicit lifecycle activation; no new always-on MCP scheduler is installed. Fencing protects local ledger/markers, not arbitrary remote side effects. The local lock coordinates cooperating updated workers using one trusted local database/filesystem; no NFS/multi-host, mixed-version, hostile same-owner process or foreign canonical store sharing one Neo4j guarantee. Long/expired work can require repeat delivery and is not exactly once. Full graph reconciliation, poison-event operator recovery, live semantic FAISS durability/duplicates, owner deployment and native-client parity remain open. Independent positive approval remains unavailable and all consequential guards are preserved. Revert only reviewed batch hunks while preserving canonical/outbox rows; never reset attempts, delete locks or rebuild/wipe owner projections to bypass failure. Review all runtimes before deliberate activation; do not kill owner sessions. Next priorities: authenticated approval/consumption, FAISS persistence/replay and held-out retrieval validation, then native host diagnosis and full release acceptance.

## Backup/restore continuation — 2026-11-15

**Controlled local recovery improved; release remains PARTIAL / NOT_READY.** Continued from the workflow checkpoint below, using existing backup service/v1 manifests and disposable files. No audit restart or new agent, tool, database, provider, dependency, schema migration or owner rollout.

| Finding | Evidence | Implemented behavior / status |
|---|---|---|
| Retention trusts manifest `path`/`name` | VERIFIED_TEST: initial negative fixture; VERIFIED_RUNTIME: HEAD service deletes a synthetic unrelated directory in a temporary-only reproduction | List/retention derive authoritative directory identity; no manifest-directed deletion |
| Missing/incomplete manifests or checksum-matching corrupt SQLite can verify | VERIFIED_TEST: part of17 failing regressions /4 passes before correction | Strict v1 allowed file set/metadata, hash+size, SQLite integrity+FK checks; symlinks/unlisted projections and snapshot journals held |
| Restore lacks staging revalidation, offline guards and a pre-restore snapshot | VERIFIED_TEST: sidecar/malformed/source mutation/failure fixtures | Verify private staged bytes; hold destination sidecars/busy/overlap/symlink paths; preserve current state without pruning; serialize cooperating POSIX restores |
| Same-second retention can prune the newly returned snapshot | VERIFIED_TEST: deterministic UUID/timestamp case fails before fix | Explicitly protect newly published snapshot |
| Safety snapshot opens an offline WAL-format target read-only, leaving new sidecars | VERIFIED_RUNTIME: first actual MCP drill holds after safety capture; isolated regression reproduces1 failure | Privately capture the already offline standalone file, then validate/snapshot the capture; original sidecar guard remains strict |
| Snapshot-side journal files are silently ignored | VERIFIED_TEST:3 failing sidecar cases | Reject sidecars rather than pairing/ignoring them |

Exact implementation files: `xninetzy/os/backup/service.py`, `tests/os/backup/test_backup_service.py`, new `scripts/smoke_backup_restore.py`, `.github/workflows/quality-gates.yml`, `apps/docs/src/pages/docs/backup-restore.md`, and that guide's generated entry in `apps/docs/public/search-index.json`. Existing phase/audit/security/evaluation/release/runbook/ADR documents and structured results are updated. The script `xninetzy_backup.py` and MCP tool contracts are preserved. Backup manifest version remains1; incomplete/unsafe historical snapshots now fail verification without rewriting them. `contains_secrets` is unknown (`null`) because canonical SQLite may contain private data; separate secret/browser/vault files are excluded, but that does not make SQLite secret-free. Restore returns additive `pre_restore_backup`; retention supports an internal no-prune capture.

Verification: **116 passed in18.89s**, including all36 backup cases plus workflow/database/deployment/installed-package checks. Earlier21/31/112/113 runs overlap and are intermediate evidence, not additive outcomes. Final selection reports no failure/skip/xfail/warning. Actual source MCP snapshot/restore succeeded after the WAL correction. Final Python3.11 image `xninetzy:backup-hardening-20261115`, ID `sha256:757420e8fd6108b50e948212eacd736600e9f41622427983af15dcba8426f38c`, verifies663 installed runtime files. From `/tmp`, installed MCP creates a local task, snapshots the live fixture WAL database, changes state, closes every fixture session, restores offline, restarts, and verifies the original task plus saved local idempotency replay. Its separate workflow recovery smoke and general571-tool read/write/restart/replay/denial smoke pass. No network or owner mount; stderr is empty. CI adds backup regression and installed-MCP drill, but remote Actions remains unexecuted.

```bash
.venv/bin/python -m pytest tests/os/backup tests/workflow tests/db \
  tests/architecture/test_container_deployment.py tests/tools/test_installed_package.py -q
docker build --progress=plain -t xninetzy:backup-hardening-20261115 .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:backup-hardening-20261115 \
  -I /app/scripts/smoke_backup_restore.py
```

Parity/workflow/general smoke commands, owner procedure and recovery are in the [runbook](../release/OPERATIONS_RUNBOOK.md). Structured evidence is under `backup_restore_continuation` in `docs/evaluation/CLIENT_CONNECTION_RESULTS.json`. Canonical Ruff/diff checks pass. Actual `yarn run check` passes16 files with0 errors/warnings/hints (4.77s); `yarn run build` succeeds34 pages. Only the changed backup guide's generated search entry is retained from build output; unrelated preexisting index entries are preserved. No browser interaction test claimed. The guide removes obsolete REST health/supervisor assumptions and includes actual `--confirm` semantics. Host/global prompts, credentials, owner stores and active client processes were not changed; this batch does not reverify native-client activation.

Measured improvement is deterministic correctness, not speed: invalid snapshot acceptance, manifest-directed retention and same-second snapshot loss now fail the unsafe path; controlled MCP restore/replay passes. Latency/RSS/CPU/context/token deltas are NOT_MEASURED. Additional copies/hashes/integrity scans run only during explicit backup/restore; the30-second cooperative backup-copy budget does not bound all filesystem/validation work.

Limits/rollback: restore assumes the owner stops all readers/writers; probes cannot prove idle handles are closed. File replacements are atomic individually, not across SQLite/FAISS; live FAISS semantics and cross-file snapshot consistency remain unverified. On interruption keep services offline and preserve the named safety snapshot; never delete journals/locks to force success. Corrupt current state can hold automatic safety capture and needs separately reviewed recovery. A point-in-time restore rewinds approval/idempotency/checkpoint records, so reconcile subsequent external effects before enabling consequential actions. `confirmed=True` is a trusted local-operator acknowledgement, not independent MCP approval. No owner restore, external exactly-once or production readiness claim. Rollback reviews only these source/test/CI/doc hunks while preserving snapshots, current stores and preexisting work; no schema rollback. Reverting guards restores reproduced defects. Next priorities: independent authenticated approval/consumption, live graph/provider reconciliation and native client parity, then held-out routing/retrieval and full acceptance.

## Durable local recovery checkpoint — 2026-11-15

**Verified controlled local recovery; phase/release remain PARTIAL / NOT_READY.** This continues the preceding approval/packaging work without rebuilding the OS. Earlier sections below describe their dated historical checkpoints.

| Finding | Evidence before | Change / result |
|---|---|---|
| Resume regenerates a new plan from the old message and can repeat writes |5 initial regressions failed in3.52s | Same workflow/plan ID and typed checkpoint now restored; completed handlers are skipped |
| Checkpoint writes occur after effects and failures are swallowed | Real SQLite trigger fixture previously permits handlers to continue | RUNNING is committed before execution; post-effect checkpoint failure stops and holds uncertain mutation |
| Cancellation races can execute a new step or return SUCCESS over a cancelled row |2 failing regressions in0.78s; failed-run cancellation also reproduced | Short serialized step/final commits preserve cancellation; failed checkpoints can be cancelled to prevent resume |
| An interrupted retry can discard evidence of another completed independent step |1 failing regression in0.39s | All prior successful evidence retained and ordered by immutable plan IDs |
| Deadline/context invariants not enforced between steps | Valid1-second budget regression fails in2.56s;3 owner/goal mutation cases fail | Cooperative budget, current effective policy and immutable owner/plan/objective checked before further effects |
| Private handler errors reach logs/progress before persistence filtering |2 failing regressions in0.53s | Unexpected errors expose type only; all typed handler results sanitized before notifications |

Implementation files: `xninetzy/workflow/models.py`, `store.py`, `executor.py`, `tools.py`, `actions.py`, `tests/workflow/test_workflow_recovery.py`, the authorized-policy fixture in `tests/workflow/test_workflow_executor.py`, `scripts/smoke_workflow_recovery.py`, `.github/workflows/quality-gates.yml`. Inventory JSON and existing architecture/audit/evaluation/release/runbook checkpoints are updated; [AGENTIC_WORKFLOW.md](../architecture/AGENTIC_WORKFLOW.md) fills the missing runtime contract documentation.

Documentation gate follow-up: actual `yarn check` ran Yarn Classic's built-in dependency check rather than the declared Astro script. The official [Yarn run contract](https://classic.yarnpkg.com/lang/en/docs/cli/run/) confirms built-in commands take precedence. CI now explicitly uses `yarn run check`. That real checker first failed with one undefined dataset-key error and two unused-variable hints in `apps/docs/src/components/PageFeedback.astro`. The narrow fix validates `up`/`down` before indexing local feedback and removes unused bindings while retaining the optional prop contract. On final source, `yarn run check` reports 0 errors/warnings/hints across 16 checked files (4.99s), and `yarn run build` builds 34 pages (2.22s total command). No browser click/visual behavior is claimed; existing markup/styles and storage format remain. The mistakenly invoked built-in scan was interrupted on its own known process; its Node deprecation warning is not a vulnerability finding. Build-regenerated search-index changes were restored from exact pre-build bytes to avoid unrelated generated diffs. No dependency/lockfile or runtime package change is needed; the tested container runtime digest remains applicable. Remote CI is unexecuted.

The existing SQLite workflow tables retain canonical state. Version1 checkpoint metadata (typed working state, plan hash, action results) uses existing JSON columns; no new table/column or destructive migration. One local advisory file lock coordinates cooperating updated POSIX runtimes. No SQLite write transaction spans a domain/network call. Owner IDs and objective cannot change through working state, missing/changed/legacy checkpoints are held, and mutating failed/interrupted steps require reconciliation. Successful reads can be retried only through an explicit server-owned whitelist. The owner mode/kill switch remains authoritative; tests explicitly allow safe local fixture writes. No new agent, framework, database, tool, external approval path or global instruction installation.

Verification: **211 passed in242.59s** across workflow/MCP/policy/HITL/privacy/packaging/graph. That run preceded the final scoped handler-error privacy correction; the complete affected workflow/core-privacy/MCP-boundary selection then passed **123 in18.14s**, including all59 current workflow cases. Counts overlap and are not summed. Earlier54/56/208 selections are intermediate evidence, not additional outcomes. No final failure/skip/xfail/warning reported. The recovery suite includes actual fixture-process SIGKILL during a completed-write/read transition and during an uncertain write; the first resumes with one persisted effect, the second refuses replay. Other fixtures cover concurrent executors, real checkpoint rollback failures, legacy/corrupt state, owner policy/context, notification failure, budget, symlinks and cancellation.

```bash
.venv/bin/python -m pytest -q tests/workflow tests/interfaces/test_execution_boundary.py \
  tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py \
  tests/interfaces/test_transport_authority.py tests/interfaces/test_mcp_server.py \
  tests/os/hitl tests/os/policy tests/tools/test_execution_policy.py \
  tests/tools/test_mcp_audit.py tests/tools/test_release_check.py \
  tests/architecture/test_container_deployment.py tests/tools/test_installed_package.py \
  tests/core/test_output_sanitization.py tests/os/graph
.venv/bin/python -m pytest tests/workflow tests/core/test_output_sanitization.py \
  tests/core/test_secret_redaction.py tests/interfaces/test_execution_boundary.py -q
```

The first red concurrency fixture lacked a bounded wait and its own runner was interrupted; the corrected bounded fixture supplies the5-failure baseline. An initial fractional deadline fixture failed configuration validation because the existing timeout setting is integer; the corrected1-second fixture reproduced missing deadline enforcement. Neither command issue is counted as a product failure or a skipped scenario.

Runtime: final minimal image `xninetzy:workflow-recovery-20261115`, ID `sha256:ea96c0cc392970ef0dbc2db61326450dfa7e216868928ff5fb1acecbae23607f`. Installed-source parity passes663 runtime files. From `/tmp`, actual MCP resumes the original failed fixture plan using canonical local reminder reads/final synthesis, preserves the completed-write ledger byte-for-byte, replays completed output, and holds a separate uncertain write. Exactly2 synthetic effects/2 intended workflows remain; no regenerated plan. Separate STDIO smoke passes571-tool discovery, read/local write/denial/restart/idempotent replay. All use disposable state, no network/owner mounts. Nine fresh client-template SDK probes also pass; native host activation/OpenCode/UI parity remain unverified. CI adds the installed-wheel MCP recovery smoke; remote Actions not executed here.

| Measure | Before | Current evidence |
|---|---|---|
| Repeating an existing completed plan in fixture | Write/read handlers execute twice | One execution; stored result returned |
| Resume plan identity | Rebuild path invoked from old message | Original ID/checkpoint reused |
| Recovery of controlled write then interrupted read | No checkpoint/state recovery | SIGKILL/new executor and actual MCP fixture pass without repeating write |
| Ambiguous write | Replay safety not established | Held; fixture effect remains single |
| Startup/latency/RSS/CPU/token delta | NOT_MEASURED | NOT_MEASURED; no speedup/accuracy percentage claimed |

Limits: existing handlers' SUCCESS is checkpoint evidence, not universal independent outcome verification. Cached completion is labelled stored and does not verify current files/sources. No external exactly-once delivery, general DAG scheduling, multi-host/NFS locking, non-POSIX recovery, live graph reconciliation, owner backup/restore or positive authenticated approval is certified. Budget/cancellation is cooperative; an in-flight operation may finish. The data directory and cooperating updated runtimes are trusted; arbitrary privileged Python/DB writers are outside this lock's security boundary. Mixed old/new executors do not share the new contract. Old records are preserved and held where state is insufficient.

Rollback: preserve JSON checkpoint/ledger evidence and owner stores, and never reset statuses/reservations or unlink active lock files to force success. No schema rollback is required. Older resume code can regenerate and duplicate work and older readers may not understand checkpoint/cancelled results: hold resume while reviewing a compatible runtime rather than running an old image against active state. No production rollout or active owner-client restart occurred. Next priorities remain independently authenticated approval/consumption/reconciliation, domain outcome/freshness verifiers, backup/restore and live graph/native-client acceptance.

Latest internal-boundary continuation2026-11-14: candidate image `xninetzy:approval-hardening-20261114` (`sha256:2866147d6cb006a2fce10703accf46bc7589b314436eae966c0fd75cfe2fc90a`) passes installed-package parity663 files, raw service/legacy-approval denial outside checkout, and actual STDIO local read/write/restart/replay/denial smoke. A stale cached wheel was discovered in an intermediate build despite successful source-STDIO smoke; Docker/CI now force own-project rebuild and verify installed runtime files. Prior source smoke remains scoped evidence; its installed-code revision was not established by import counts alone.361 combined tests cover current workflow/graph regressions; this remains neither interrupted external workflow recovery nor live graph verification. Full evidence/rollback is in Phase1; production readiness remains NOT_READY.

Latest Phase1 continuation2026-11-14: the current rebuilt minimal Python3.11 image `xninetzy:phase1-20261114` (`sha256:4cfa64c0ebbce8fd006a95dadd8955f8c006d8941969957b448217907e843765`) passes real STDIO initialization,571-tool discovery, read, explicitly permitted synthetic local write, missing-key/payload-change/unauthenticated-confirmation denials, orderly restart and single-result replay. A read-only root, no network and disposable mounts isolate this from owner data. This supersedes statements below that no November14 source image was rebuilt. It is not an owner deployment, interrupted multi-step workflow, abrupt crash or external-provider reconciliation drill.

The context executor now preserves canonical/provider risk, binds replay to capability/context/payload and refuses to report successful execution when no invocable ran. Gateway timeouts retain bounded workers and uncertain reservations. Existing graph projection fixes remain covered by the combined regression; live graph acknowledgement/reconciliation remains NOT_VERIFIED_IN_LIVE_ENVIRONMENT. The global default approval/manual write policy is enforced; only the synthetic smoke explicitly selects auto. See [Phase1](PHASE_1_REPORT.md) for current contracts/evidence and [runbook](../release/OPERATIONS_RUNBOOK.md) for recovery. No graph data, schema, owner service or historical workflow was reset.

Final gateway auto-hooks now execute only within an actual permitted WRITE reservation, so READ/DRAFT responses and successful replay cannot independently create automatic memory/graph/improvement artifacts. This closes duplicate optional projection initiation at that boundary; it is not a transactional outbox or live graph reconciliation implementation. Current affected runtime/serialization tests98 pass after this correction; the earlier expanded836-test run is distinct, not summed.

Date: 2026-11-10. Status: **PARTIAL phase**. These batches improve existing execution/persistence behavior. They do not create a new orchestrator or establish complete restart/resume safety.

## Workflow outcome correction

VERIFIED_CODE: `WorkflowExecutor` previously assigned overall SUCCESS whenever execution did not stop on a critical failure, even if noncritical actions failed or skipped. Its text already said the workflow completed partially, so persisted status and visible evidence disagreed.

Tests were updated/added before implementation: **4 failed, 3 passed** in the executor suite. Aggregate status now uses existing FAILED whenever any executed result is not SUCCESS. Successful actions still run/are retained, noncritical continuation is preserved, and existing partial response text remains. No new enum value or schema migration is introduced.

The new regression writes a real temporary SQLite workflow and checks both stored status/result JSON and retained successful steps. A preexisting reminder fixture omitted academic detail/download handlers yet expected aggregate SUCCESS. It was corrected to explicitly assert those two SKIPPED outcomes, aggregate FAILED, successful REMINDER_INFER and a genuinely persisted pending reminder. This strengthens the original reminder assertions rather than removing the case or masking a product failure.

Files: `xninetzy/workflow/executor.py`, `tests/workflow/test_workflow_executor.py`, `tests/workflow/test_workflow_reminder.py`. Compatibility: consumers that previously interpreted partial execution as SUCCESS now receive the existing FAILED value; partial completion details remain in per-step results/text. This intentional behavior correction must not be mistaken for durable recovery or policy enforcement.

Remaining workflow limits: dependency skipping is not a general validated DAG scheduler; generated placeholder academic steps and continuation semantics need a separate product decision; persistence errors, pending approvals and restart replay still require acceptance tests. No external academic operation ran in these fixtures.

## Projection acknowledgement batch

VERIFIED_CODE: the worker ignored False acknowledgement and marked SQLite projection sync/outbox completion despite Neo4j failure. Tests first reproduced **10 failures / 2 passes**. Enabled projection writes/deletes now require acknowledgement before reporting success; failures enter the existing outbox failed/backoff path. FAISS is still attempted independently for node upserts. Disabled Neo4j remains optional, is not invoked, and does not get a synchronized timestamp.

A prerequisite retry defect was also reproduced: exhausted rows had `next_retry_at=NULL`, which the claim query interpreted as ready immediately. A dedicated real temporary SQLite test failed before the correction. Claiming now filters `attempts < GRAPH_SYNC_MAX_ATTEMPTS` across pending, failed and expired-processing branches. Exhausted rows remain inspectable; no rows are reset/deleted and no rebuild is automatic.

Final expanded projection suite: **19 passed in 21.35s**. The earlier existing graph suite with the initial projection cases: **36 passed in 40.06s**, with one preexisting embedding FutureWarning; counts overlap and must not be added. Workflow suite: **30 passed in 1.73s**. Scoped Ruff and diff whitespace checks pass.

Files: `xninetzy/os/graph/v3/projection_worker.py`, `xninetzy/os/graph/v3/sqlite_store.py`, `tests/os/graph/test_projection_worker.py`. CI now includes graph and workflow regression directories in the critical execution step. No live Neo4j, destructive projection rebuild, schema migration, new dependency or owner database change occurred.

Limits: disabled Neo4j work is drained for configured projections and leaves its sync timestamp unset; enabling it later requires an explicit resync. Exhausted rows need deliberate reconciliation; simply restoring connectivity does not reset attempts. FAISS may append duplicate vectors during bounded retries under its existing API. General projection consistency, edge-deletion semantics and whole-index reconciliation are not established by these tests. None of this proves live graph availability or exact-once external projection effects.

## Rollback

Reverse only the reviewed workflow/projection hunks and tests if required; no data migration is needed. Restoring the old status behavior restores false success. Existing stored historical workflow statuses are not rewritten. No failed graph rows are deleted/reset automatically; recovery must preserve canonical SQLite and existing approvals.

## Final integrated verification

**476 passed, 1 warning in 162.36s** in the final combined foundation, policy, workflow, graph, knowledge/memory, minimal-import, provider, vision and spreadsheet regression run. No failed/skipped/xfail reported. This is a selected local suite, not all collected tests or live provider acceptance. One preexisting embedding-method FutureWarning remains visible. Every changed Python file passes scoped Ruff; global Ruff remains 125 findings. Diff whitespace, shell syntax, CI YAML and report links pass. The CI installed-wheel smoke was also executed locally and lists 571 tools plus a successful safe read.

Measured production task success, runtime CPU/RSS improvement, citation quality and cross-client parity remain NOT_MEASURED/NOT_VERIFIED. Highest next work: exact approval authenticity/atomic consumption and canonical risk binding, then corrected container deployment and safe durable resume. Current release decision stays NOT_READY.

## Continuation verification

The476 result above is historical to the preceding checkpoint, now committed in `74ff58b`. Current approval containment prevents treating a model-supplied identifier or injected installation identity as independent owner consent. No new workflow resume/approval-consumption state machine is claimed. Nine candidate connection entries for eight local hosts each completed a real temporary STDIO handshake/catalog/safe read; the client report distinguishes these from native sessions. Full repo Ruff is now zero and the old embedding API call is corrected without suppressing warnings. Current final regression/deployment results are appended after execution; production readiness remains NOT_READY until the outstanding gates are proven.

Final expanded continuation run: **781 passed in283.29s, no warnings reported**, using temporary state and offline-model flags. This includes existing workflow/graph tests and new approval, embedding, decoder, taxonomy, client configuration and deployment contracts. Full repo Ruff remains zero; current API/token metadata and JSON inventory are validated. It does not demonstrate arbitrary external side-effect recovery, full-suite success, live graph quality or owner-state deployment. The selected-scope expansion explains the changed count versus476.

## H2 actual container operation, 2026-11-11

VERIFIED_RUNTIME: Docker Engine29.9.3 builds the corrected base-only image successfully using CPython3.11.14 and64 frozen base distributions. Tested tag: `xninetzy:deployment-audit-20261111`; final inspected image ID: `sha256:06471256d9d0a5b6359e265c8f95598ffd86ac79ec48f73370fe278d65002bc1`. Resolved base reference: `ghcr.io/astral-sh/uv:python3.11-bookworm-slim@sha256:4f5d923c9dcea037f57bda425dd209f3ec643da2f0b74227f68d09dab0b3bb36`. The tag itself remains mutable; these identifiers describe the tested artifact rather than a pinned production rollout. The earlier intermediate image was rebuilt after the supervisor fix; results below apply to the final tag/ID.

Executed commands:

```bash
docker build --progress=plain -t xninetzy:deployment-audit-20261111 .
.venv/bin/python scripts/smoke_container.py --image xninetzy:deployment-audit-20261111
docker image inspect xninetzy:deployment-audit-20261111 --format '{{.Id}} {{.Config.User}}'
docker run --rm --network none --read-only --tmpfs /tmp:mode=1777 \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --env AUTO_MEMORY_ENABLED=false --env AUTO_GRAPH_ENABLED=false \
  --env AUTO_IMPROVE_ENABLED=false --env NEO4J_ENABLED=false \
  --env LIGHTNING_ENABLED=false xninetzy:deployment-audit-20261111 \
  python -m xninetzy.cli.supervisor release-check
```

All exit0. Actual SDK STDIO result, with no owner `.env`, database or vault mounted:

| Stage | Evidence | Result |
|---|---|---|
| Initialization/catalog |571 tools; protocol2025-11-25 | PASS |
| Safe read | datetime_now contains ISO result | PASS |
| Safe local write | Synthetic task_capture and task_list | PASS |
| Same-container restart | Reinitialize/list/read and retrieve persisted task | PASS |
| Idempotent replay | Same task payload/key after restart; exactly one listed synthetic task | PASS |
| Isolated runtime | Non-root1000:1000; read-only root; network none; temporary writable data; container removed afterward | PASS |
| Bounded release checks inside image | Registry,3 redaction samples,3 SSRF scenarios, STDIO transport, actual SDK1.30.0,4 canonical FINAL declarations | PASS; not production certification |

Exact files: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `scripts/smoke_container.py`, `tests/architecture/test_container_deployment.py`; supervisor/test/CI follow-up is recorded in Phase 1. Compose uses per-session STDIO with no public port or REST healthcheck; optional Neo4j retains existing volumes/profile. The .dockerignore allowlist prevents owner `.env`, secrets, Git state and databases from entering the build context. Five deployment contract tests pass; the related43-test run also includes them. Compose syntax was checked separately without loading owner `.env`; this is not an actual owner Compose rollout.

Measured startup latency, RSS/CPU and speedup for this container: NOT_MEASURED. The smoke proves orderly restart of a local mutation, not crash recovery for a multi-step or external workflow. Live Neo4j, embeddings/model providers, provider timeouts, full disk, backup/restore and database-unavailable recovery remain NOT_VERIFIED_IN_LIVE_ENVIRONMENT. Existing empty data directories can initialize fresh SQLite state; no wrong-store recovery guarantee is claimed. Optional browser/model features require extras and provider-specific cache/mount review.

Rollback: reverse only reviewed deployment/source/test hunks or choose a separately reviewed prior image. Do not delete/reset data directories, graph volumes, reservations or approvals. No production container was replaced. Next P0 work remains trusted approval issuance/atomic consumption, canonical risk enforcement and controlled interrupted-workflow/reconciliation tests. Release stays PARTIAL / NOT_READY.

## Owner-selected client connection checkpoint

The owner subsequently selected database A. Nine host MCP entries for eight compatible clients are now installed with explicit A paths, protected backups and unchanged permission flags. Isolated post-install SDK probes pass9/9; native Codex parses the saved configuration. Neither production database was opened through SQLite or a migration-capable server during verification; raw file hashes and global prompt hashes are unchanged. Native GUI reload/owner-state runtime remain NOT_VERIFIED. The quoted-TOML installer replan regression is fixed and49 related config/CLI/runtime tests pass. See CLIENT_CONNECTIONS.md for exact receipt/rollback and Phase 1 for source/test changes. This does not change workflow/approval readiness gates.

November14 follow-up: service decision races and uncertain-outcome acknowledgement are corrected, with125 related/21 latest focused tests passing (overlapping selections). This is not a workflow durable resume implementation. OpenCode2 adapter migration is installed and SDK checks pass9/9, but its native isolated connection remains unverified; active Codex read/discovery works. The earlier container image/digest remains evidence for its recorded artifact only; no fresh container rollout of this approval patch is claimed. Phase 1 records exact changes and recovery limits. External single-use approval consumption and reconciliation remain open.
