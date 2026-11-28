# Candidate verification and recovery runbook

## Installed global prompt v2.3, 2026-11-16

Owner-approved rollout is complete:9/9 installed hashes match the canonical
bundle. Five files changed under `~/.xninetzy` (L0, shared continuity, three
conditional references). L1 and Codex/Claude/OpenCode adapters were already
matching and were not rewritten. Permission/model/MCP configuration is untouched.
Validate with `python scripts/validate_prompt_contract.py --installed` or the
default read-only `scripts/verify_prompt_injection.sh`.

Backup and receipt:
`~/.xninetzy/backups/prompt-v2.3.0-20261115T191727Z-5753e6f8/` (timestamp UTC).
The0700 directory contains0600 originals, approved sources, receipt and private
installer. Source hashes, original modes, idempotent repeat and injected-failure
rollback were verified. Publication is atomic per file, not as one filesystem
transaction. Do not delete the backup or overwrite later owner additions.

For an owner-requested rollback, use the archived installer's `--rollback`
preview and add `--apply` only for actual recovery; exact commands are in Phase2.
It refuses changed targets and restores only this installation. Do not revert
unrelated application changes or user data. New sessions or a normal instruction
reload are needed where clients cached v2.2; no active process/job was restarted.
New optional MCP discovery parameters likewise require a normal schema reload.
File verification does not prove every native client has reloaded its context.

## Current validator repair and graph-worker candidate

The pure writing checks `skill_validate_anti_slop`, `skill_validate_output` and
`skill_validate_submission_readiness` are READ operations. After reviewing the
updated source/runtime, reconnect only the affected host's Xninetzy MCP session
so its cached catalog/callables reload. No host settings change is required.
Check them without an idempotency key under the default approval policy; a
negative validation is report data, not a failed approval. Explicit per-tool
owner restrictions still apply. Never change global approval mode to fix them.

```bash
.venv/bin/python scripts/smoke_container.py --image xninetzy:validator-fix-20261115 --validators-only
.venv/bin/python scripts/smoke_graph_worker.py
.venv/bin/python scripts/smoke_graph_worker.py --provider sentence_transformers
.venv/bin/ruff check .
```

The graph smoke uses disposable SQLite/vector state and disables downloads;
the neural variant needs the documented model already cached. Default worker
flags remain off. To opt in after a reviewed backup/configuration change, both
`GRAPHRAG_V3_ENABLED` and `GRAPH_SYNC_WORKER_ENABLED` must be true; stats expose
configured/running/inflight. Do not enable this on owner state as part of a smoke.
Neo4j remains independently optional. Shutdown stops future dispatch and retains
entered work; coordinate all clients before maintenance or restoration.

Preserve legacy `graph.index`/`graph_map.json`; new code deliberately holds
unversioned/corrupt projections. Do not delete them or auto-rebuild on a read.
New snapshots use two index/map slots plus `graph.current.json`. Preserve the
whole set for recovery; old runtime rollback cannot consume the new format.
Rebuild remains a separately reviewed consequential operation and is not granted
by a validator result. Snapshot hashes are integrity checks, not authentication.

The full regression attempt exhausted local disk; reserve adequate free space
before repeating full suites/rendering/installations. Only the task-created
temporary frozen environment was removed. Do not prune owner caches, databases,
containers or arbitrary Docker images to make a check pass. Inspect current
free space and retain actual failure evidence before recovery.

## Projection ownership and real Neo4j fixture — 2026-11-15

Current minimal image: `xninetzy:graph-hardening-20261115`, ID `sha256:ecbc8096b2fd9ec3f35cc0531fbdbc201b9742cf8b2e575165848e02e6bda3fb`. It remains STDIO/base-only; optional graph validation is a separate profile. Do not infer an owner deployment or always-running worker from a successful fixture.

The worker now requires its exact persisted attempt/unexpired lease before dispatch/finalization. ACK and canonical version/hash/status markers commit together. Current canonical edge properties/active endpoints are used instead of old payload defaults. A local `.graph-projection.lock` next to the selected SQLite file serializes cooperating updated ticks without holding a SQL transaction during provider work. `lease_lost` means a worker did not own completion; `deferred` means another local tick held the lock. Neither means a completed projection. Unknown operations fail within existing retry limits; unexpected provider failures record type only.

Reproduce the enhanced fixture only in development, using an already reviewed official image and the existing graph extra:

```bash
docker pull neo4j:5.26-community
.venv/bin/python scripts/smoke_graph_projection.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest \
  tests/os/graph tests/os/backup tests/workflow tests/db \
  tests/interfaces/test_execution_boundary.py tests/architecture/test_container_deployment.py \
  tests/tools/test_installed_package.py tests/os/hitl/test_internal_approval_boundary.py -q
```

The script uses `.venv` only if it already has the graph extra; it does not install packages/pull images during a request. CI independently uses `uv sync --frozen --no-dev --no-editable --extra graph --reinstall-package xninetzy-mcp` in its disposable runner. For local installed-package checks use a fresh `UV_PROJECT_ENVIRONMENT`, not an active owner venv: changing extras in the owner's environment can remove unrelated packages. Current installed graph-only proof uses a temporary Python3.14.5 environment; remote Python3.11 enhanced CI is not claimed executed.

The harness resolves the already pulled image ID, creates its own labelled internal Docker network/container and synthetic0600 authentication file, and reaches only the exact container's private address. No host port/owner mount/Docker socket is exposed to the backend. Limits are1.5 CPU/1536MiB, UID7474, dropped capabilities/no privilege escalation. Cleanup removes only IDs it created, including their synthetic anonymous volumes; no owner service is stopped. If force-killed, inspect `docker ps -a --filter label=xninetzy.test=graph-projection` and the recorded invocation before separately removing only that test's exact IDs. Never clean resources by a broad owner-service name. Docker bridge reachability is a Linux-host assumption; early internal-port-publish attempts failed cleanly before the private-address correction.

Actual Cypher checks prove fixture edge properties/weight, no duplicate relationship on resync, canonical SQLite/FTS availability while the test backend is stopped, retry after restart and deletion. The failed pool is closed before a new failed connectivity probe; this is not a proof of a crash mid-write. FAISS is explicitly stubbed/NOT_TESTED, so no embedding/model download or semantic-durability claim follows. The loop still requires explicit host lifecycle activation. Configured-off Neo4j remains optional; enabling a previously disabled projection requires reviewed reconciliation, not assumed automatic resync.

Before owner activation, review every participating runtime and existing state, and reconnect deliberately; do not kill active owner sessions for a test. Mixed old/new ID-only code, NFS/multi-host and different canonical stores sharing a projection are not covered. Preserve failed/exhausted outbox rows and receipts for inspection; do not reset attempts, unlink active locks or wipe/rebuild projections to force success. Destructive rebuild remains subject to existing approval, whose independent positive issuer is still unavailable. Local lease fencing is not remote exactly-once execution or complete owner reconciliation. Rollback preserves canonical/outbox state and reviews only the batch hunks; reverting guards reinstates reproduced stale ownership/privacy defects. Exact evidence: [Phase3](../implementation/PHASE_3_REPORT.md).

## Backup/restore hardening — 2026-11-15

The existing `xninetzy.os.backup.service` now validates v1 manifests, exact file sets, hashes/sizes and SQLite integrity/foreign keys; snapshot and destination SQLite sidecars are held. Retention derives targets from real directories, not manifest `path`/`name`, and preserves the just-created snapshot. New snapshots have unknown `contains_secrets` (`null`); SQLite can itself contain private records. Legacy false claims are not proof of secret-free contents.

Only an owner-authorized offline restore may use `scripts/xninetzy_backup.py restore <name> --confirm` with explicitly reviewed SQLite/vector/backup settings. Stop all MCP hosts/workers that use the selected store through their own controls; do not stop owner processes as part of a test. The flag is local operator acknowledgement, not a new trusted MCP approval channel. A busy/sidecar check and advisory restore lock do not prove idle processes have closed old handles. No NFS/multi-host or hostile same-owner filesystem guarantee is made.

Restore stages/verifies snapshot files before effects and preserves a verified pre-restore snapshot without pruning. Individual file replacements are atomic; vectors plus SQLite are not one atomic operation. If `restore_interrupted` occurs, retain the named safety snapshot and keep services offline for reviewed recovery. A SQLite-only snapshot with existing target vector files is held for reconciliation rather than deleting those files. A corrupt current database may hold safety capture and needs a separate owner-controlled recovery. Do not remove journals/lock files, reset reservations or select a different database to bypass a hold.

A point-in-time restore rewinds checkpoints, approvals and idempotency records. Reconcile external effects since the snapshot before enabling consequential operations; an absent receipt/key does not prove an action never happened. No external exactly-once guarantee follows. FAISS is copied as an optional pair; cross-file live consistency and actual semantic retrieval remain unverified. See the canonical [backup guide](../../apps/docs/src/pages/docs/backup-restore.md).

Reproduce only against disposable state, from the repository root:

```bash
.venv/bin/python -m pytest tests/os/backup tests/workflow tests/db \
  tests/architecture/test_container_deployment.py tests/tools/test_installed_package.py -q
docker build --progress=plain -t xninetzy:backup-hardening-20261115 .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:backup-hardening-20261115 \
  -I /app/scripts/check_installed_package.py --source /app/xninetzy
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:backup-hardening-20261115 \
  -I /app/scripts/smoke_backup_restore.py
```

The smoke creates a task through actual MCP, snapshots the running fixture WAL database, changes its task state, exits every fixture MCP session, restores offline, restarts and verifies original task plus saved local replay result. It does not mount an owner store or use graph/embedding/network services. Source/installed artifact results and limitations belong to the latest [Phase3 checkpoint](../implementation/PHASE_3_REPORT.md), not to a production deployment claim.

## Durable workflow candidate — 2026-11-15

Current tested image: `xninetzy:workflow-recovery-20261115`, ID `sha256:ea96c0cc392970ef0dbc2db61326450dfa7e216868928ff5fb1acecbae23607f`. These commands verify a candidate using disposable state, without owner mounts, credentials, providers or network:

```bash
docker build --progress=plain -t xninetzy:workflow-recovery-20261115 .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:workflow-recovery-20261115 \
  -I /app/scripts/check_installed_package.py --source /app/xninetzy
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:workflow-recovery-20261115 \
  -I /app/scripts/smoke_workflow_recovery.py
.venv/bin/python scripts/smoke_container.py --image xninetzy:workflow-recovery-20261115
.venv/bin/python -m pytest tests/workflow -q
```

Parity checks663 installed runtime files. The recovery smoke uses the installed package from `/tmp` and actual MCP STDIO: two synthetic effects/two intended workflows remain, completed-write evidence is unchanged, exact failed-plan resume succeeds through canonical local reads/synthesis, completed output replays, and uncertain mutation is held. Process-kill recovery uses separate pytest fixture processes; no active owner client is terminated. The general container smoke separately proves orderly stop/start/local replay. No external-delivery or live graph guarantee follows.

Use the same workflow ID and exact saved checkpoint. Revalidate effective owner policy; never reconstruct from the old message or clear an action/result to force a retry. `workflow_uncertain_outcome_reconcile` requires inspection of authorized canonical state/receipts, not a new key or a new plan. Legacy/malformed/mismatched state remains held and preserved. Cancellation stops future unclaimed steps; a running operation may finish. Cached completed output is labelled stored and is not current artifact verification.

Updated runtimes coordinate through `.workflow-locks/` next to the selected SQLite database. Keep that directory on trusted local POSIX storage. Do not unlink active lock files, remove reservations, reset statuses or change database paths to bypass a hold. File-lock release on process exit is automatic. This does not protect against old executors that ignore the lock or arbitrary same-owner database writers. Review all participating runtimes and reconnect them deliberately before enabling recovery; do not kill active owner work merely for a test. Owner host configs and production state were not changed by this batch.

Rollback preserves checkpoint JSON and action ledgers; no schema rollback is required. The older resume code can repeat completed work and may not understand additive checkpoint/cancelled states. Hold resume while reviewing a compatible runtime instead of downgrading against active state. See [workflow contract](../architecture/AGENTIC_WORKFLOW.md) and [Phase3 evidence](../implementation/PHASE_3_REPORT.md).

## Internal approval / installed-package checkpoint

Public approval calls now hold even with a configured owner ID/name. Legacy approved records are preserved but do not authorize new effects. Rejection remains a reversible configured-owner operation. HEBAT owner shortcuts and confirm-only deletion are unavailable; dry-run inspection does not authorize deletion. An inbox note is not an approval channel, and removed `/approve` commands must not be used as an authorization workaround. Positive authenticated approval remains unimplemented.

Reproduce the latest candidate with disposable state:

```bash
docker build --progress=plain -t xninetzy:approval-hardening-20261114 .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:mode=1777 --workdir /tmp \
  --entrypoint python xninetzy:approval-hardening-20261114 \
  -I /app/scripts/check_installed_package.py --source /app/xninetzy
.venv/bin/python scripts/smoke_container.py --image xninetzy:approval-hardening-20261114
.venv/bin/python -m pytest tests/os/hitl/test_internal_approval_boundary.py \
  tests/os/academic/hebat/test_hebat_direct_admin_approval.py \
  tests/os/academic/test_qa_portal_tools.py tests/os/academic/test_krs_war_tools.py -q
```

Docker/CI now use `--reinstall-package xninetzy-mcp` for frozen non-editable installation. Do not infer installed freshness from source copies, successful import or571-tool discovery. Parity checks compare runtime `.py/.json/.sql` files and preserve the manifest's intentional source-test exclusion; they do not read owner state or certify dependency provenance. Latest tested image: `sha256:2866147d6cb006a2fce10703accf46bc7589b314436eae966c0fd75cfe2fc90a`.

The recorded installed-service denial probe creates/mutates synthetic approval rows only in container tmpfs, from `/tmp`, without network or owner mounts. The general MCP smoke uses its own temporary state and explicit synthetic local-write permission. Neither starts an owner service, replaces a host config, uses a portal session or verifies native host approval UX. Reconnect existing clients deliberately to load revised source; do not kill in-progress owner work for a test.

Rollback review covers this batch's service/domain/notifier/build/test hunks only; keep preexisting work and historical approval rows. No schema rollback or reservation cleanup is needed. An older cached image is not a safe rollback merely because its tag exists; rebuild/review it and run parity, negative authorization and local replay checks first.

## Phase1 hardened profile — 2026-11-14

Supported profile is local single-owner STDIO. HTTP now fails before initialization because independently authenticated owner HTTP access is unavailable. Do not restore loopback HTTP to bypass this gate. All23 FINAL tools are held; a boolean/approval ID/tool description cannot authorize execution. Preserve the global default `approval` or stricter owner policy. Local fixture writes explicitly select auto without changing host configuration.

After reviewing the diff, rebuild and exercise disposable state:

```bash
docker build --progress=plain -t xninetzy:phase1-20261114 .
.venv/bin/python scripts/smoke_container.py --image xninetzy:phase1-20261114
.venv/bin/python scripts/connect_mcp_clients.py --smoke
.venv/bin/python -m ruff check xninetzy tests scripts
.venv/bin/python scripts/validate_prompt_contract.py
```

The smoke performs no production rollout and mounts no owner data. It explicitly permits automatic synthetic local task writes; production policy remains separate. It proves orderly local restart/replay and wire denials, not live portal/graph or interrupted external workflow recovery. Installed client entries load revised source on reconnection and must rediscover additive idempotency schemas; do not kill active owner sessions merely to force activation. OpenCode native activation remains unverified even when SDK transport passes.

For `idempotency_pending`, timeout, cancellation or invalid output after a write: preserve the reservation and inspect canonical state plus any provider receipt before retrying. Changed payload requires a new independently authorized operation, not reuse of the prior key. Never delete reservations/approvals or pick a fresh database to make an error disappear. Gateway-v1 rows coexist with legacy rows; reconcile pre-upgrade in-flight work explicitly.

Learned overrides accept bounded tuning only. Protected legacy rows are ignored without deletion; correcting one is a separate owner-authorized data action. Missing/unavailable configured data must be investigated using the explicit A selection and saved receipts, not silently switched to B. Rollback reviews source/catalog/test hunks or a previously verified image while preserving all state, backups and unrelated owner changes.

This runbook covers current local checks, not a certified production deployment. Do not apply the stale REST/WhatsApp commands in the historical V1 checklist. Start with [current truth](../audits/CURRENT_SYSTEM_TRUTH.md) and [release decision](RELEASE_READINESS.md).

## Inspect before running

Check Git and preserve user changes. Review explicit data/vault/index paths; never use a real owner database for mutation tests. Disable deployment `.env` in in-process checks and use fresh temporary SQLite/files. Base installation tests must use a separate environment and non-editable wheel so source imports do not hide packaging omissions.

```bash
git status --short
python3 scripts/validate_prompt_contract.py
bash scripts/verify_prompt_injection.sh --canonical
```

`bash scripts/verify_prompt_injection.sh` compares installed instructions read-only and reports drift; this is expected until reviewed rollout. It does not install files or change native permissions.

For scoped tests, use the isolation method in [baseline results](../audits/BASELINE_TEST_RESULTS.md). Run strict tool audit in an environment with temporary paths and `.env` disabled. `--inventory` inspects declarations and never invokes providers. A successful strict audit is not authorization proof.

## Ambiguous store recovery

If corrected runtime refuses startup because legacy sibling state exists, stop before opening a database. Review intended paths without dumping personal contents; preserve a backup through the established owner-controlled process. Set `MCP_HOST_DATA_DIR`, `MCP_HOST_SQLITE_PATH` or non-container `SQLITE_PATH` explicitly in process configuration to select the intended existing store. Do not silently merge, rename, delete or choose a store by file size. Host configuration changes require reviewed owner authorization where applicable.

## Pending idempotency recovery

A pending reservation may be active or have an uncertain external outcome. Do not retry with a new key or delete the reservation automatically. Inspect the workflow/action receipt and provider current state through authorized read paths. Reconcile whether the effect occurred, then use a separately reviewed domain recovery path. The generic helper has no automatic crash takeover or external exactly-once guarantee.

## Approval execution uncertainty

The approval service now claims a pending decision conditionally before committing and invoking its auto-action. A stale approver/expiry check cannot overwrite another decision. If approval_execution_unverified is returned, the approval was accepted earlier but execution_at is missing: work may still be running or may have been interrupted before/after its effect. Inspect authorized action state and durable receipts before a separately reviewed reconciliation. Do not create a new approval, reset the row or repeat the effect automatically. Completed duplicate acknowledgements do not prove external exactly-once execution. Independent owner authentication and external approval consumption remain open gates.

## Optional dependencies and protocol

Core metadata and datetime should not require graph/model/browser/image/document extras. Missing selected providers should return an actionable extra-install message. Install only the required project extra; never install arbitrary scripts or third-party skills during discovery.

Keep current SDK below v2 until the [compatibility plan](../architecture/MCP_PROTOCOL_CONTRACT.md) is executed. Streamable HTTP, including loopback, is disabled before initialization until independently authenticated owner access is verified. The corrected Docker contract is STDIO, not a detached REST server.

## Minimal container verification

The current Dockerfile installs only frozen base dependencies, uses Python 3.11 and UID/GID1000, starts `xninetzy.interfaces.mcp_server` and exposes no network listener. Compose keeps graph in an optional profile, uses a read-only root with writable `/tmp`, drops capabilities and forbids privilege escalation. The chosen data directory must already exist; no owner vault is mounted by default. Build contexts exclude tracked/untracked data stores, deployment `.env`, `.secrets` and Git state.

```bash
docker build --progress=plain -t xninetzy:deployment-audit-20261111 .
.venv/bin/python scripts/smoke_container.py --image xninetzy:deployment-audit-20261111
```

The smoke creates and removes only its uniquely named container, uses a temporary data bind, disables automatic hooks/Neo4j and has `--network none`. It verifies actual MCP handshake/catalog/read, synthetic task persistence and one-record idempotent replay after restarting that same container. It does not load owner `.env` or test live providers, abrupt workflow interruption or external reconciliation. Result provenance is in [Phase 3](../implementation/PHASE_3_REPORT.md).

For an owner-reviewed deployment, an MCP host launches the Compose service per STDIO session, using an absolute Compose path and an explicitly selected existing data directory:

```bash
XNINETZY_DATA_DIR=/absolute/selected/data-directory \
docker compose -f /home/misbahul45/code/xninetzy/docker-compose.yml \
  run --rm --no-deps -T xninetzy
```

This command is a deployment recipe, not an executed owner rollout. Review optional `.env` provider credentials and permissions before that rollout; never include them in logs or tracked examples. Compose's `create_host_path: false` rejects a missing directory, but an existing empty directory still allows initialization of new SQLite state. Do not treat it as protection against selecting the wrong existing directory or a missing expected database file. No production restart is authorized by a successful synthetic smoke alone. Optional browser/model processing requires explicitly selected extras; the minimal image never installs them during requests. A missing writable home may affect providers that require caches outside `/app/data` or `/tmp`.

## Local MCP host connections

Use [the connection report](../implementation/CLIENT_CONNECTIONS.md) for nine installed entries/eight hosts and exact plan/apply/smoke commands. The owner selected A (`/home/misbahul45/code/xninetzy/services/ai/data/xninetzy.sqlite3`); all entries now select that store, with protected backups/private receipt and unrelated configuration/approval flags preserved. No global prompt installation occurred. Restart/reconnect MCP in existing clients to load their saved settings. Post-install SDK checks override mutable paths temporarily; they do not prove a native GUI session has reloaded or that an owner-database startup/migration is verified.

OpenCode2.x requires mcp.servers/disabled; the helper migrates only Xninetzy and preserves Kilo's separate flat format. Native isolated OpenCode list remains unverified despite correct native add output; do not count exit0 or SDK success as native activation. The active Codex session now completes real MCP datetime/discovery reads. Avoid restarting another active owner client/service just to improve a test report. Native client metadata may change independently; preserve it when considering rollback and check the correct installation receipt for the later OpenCode migration.

## Bounded release diagnostics

For the documentation application, run `yarn run check` and `yarn run build` from `apps/docs`. The explicit `run` is required: Yarn Classic's built-in `yarn check` checks dependencies rather than invoking the Astro script. Current check/build pass; browser interaction and remote Actions are separate verification boundaries. Build regenerates the public search index, so review any generated diff before retaining it.

`python -m xninetzy.cli.supervisor release-check` runs existing registry, redaction-sample, SSRF-guard, transport, installed-SDK and canonical-FINAL checks. WARN/BLOCKED results cause nonzero exit; unexpected validator failure reports only its exception type. Use temporary state and explicit process paths for candidate runs. A PASS is a bounded diagnostic result; the independent owner approval, live service and recovery gates in RELEASE_READINESS.md still apply.

## Rollback

Review/reverse only the relevant candidate hunks, preserving initial workspace deletions/untracked files. Keep pyproject and lock together. No schema migration needs rollback. Reverting security patches restores known regressions; review that tradeoff explicitly. Host instructions and historical telemetry did not change and require no automatic rollback.
