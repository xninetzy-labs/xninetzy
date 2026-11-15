# Phase 1: foundational hardening batches

## Writing-validator policy repair, 2026-11-15

`VERIFIED_CODE`: `skill_validate_anti_slop`, `skill_validate_output`, and
`skill_validate_submission_readiness` only inspect supplied text through pure
in-memory functions in `skills/validators.py`. The execution catalog incorrectly
marked all three WRITE. The default `approval` policy therefore held ordinary
validation with `approval_channel_unverified`.

Only those three catalog entries change to READ. Public function parameters,
the existing result envelope and validator findings are preserved. They no
longer require mutation approval/idempotency or initiate optional write hooks.
Explicit per-tool manual/approval restrictions and the kill switch remain in
force. Submission readiness does not authorize submission; FINAL operations
remain held. No host configuration or owner store is changed.

Tests first reproduced7 failures/3 passes. Final validator/gateway/action-policy
selection: **61 passed in7.96s**. Actual SDK MCP calls in the fresh minimal image
under `ACTION_POLICY_DEFAULT_MODE=approval` pass for all three tools on initial
start and restart, with no approval/key. Expected negative findings survive,
READ annotations are present, and a consequential submission remains held.

Files: `xninetzy/tools/execution_policies.json`,
`tests/interfaces/test_skill_validation_policy.py`, `scripts/smoke_container.py`,
`.github/workflows/quality-gates.yml`, regenerated `docs/audits/tool_inventory.json`,
the inventory report and `apps/docs/src/pages/docs/mcp-system.md`.
The571-tool surface is now136 READ/6 DRAFT/406 WRITE/23 FINAL. No schema migration,
new tool/provider, global policy relaxation or positive approval channel is added.

Reproduction: `.venv/bin/python -m pytest tests/interfaces/test_skill_validation_policy.py
tests/interfaces/test_execution_boundary.py tests/interfaces/test_mcp_tool_adapter.py
tests/tools/test_execution_policy.py tests/os/policy/test_action_policy.py -q`;
`.venv/bin/python scripts/smoke_container.py --image xninetzy:validator-fix-20261115
--validators-only`. Exact image/evidence are in Phase3 and the existing JSON
checkpoint. Already-running MCP processes retain cached policy/callable metadata:
reload their MCP connection to activate the reviewed code. They were not killed.

Final expanded selection:178 passed in192.49s, including this repair, actual
FAISS/worker contracts, deployment contracts and the corrected docs risk table.
Separate trust-outcome checks2 passed in24.34s. Their existing success fixture
now uses a known provider with explicit reviewed read-only metadata; a new
unverified-provider case fails if the handler executes. This corrects the fixture
to current policy rather than permitting unreviewed execution. File:
`tests/evaluation/test_integration.py`. The earlier full run remains incomplete;
counts overlap and are not summed.

Rollback only the three reviewed catalog entries and associated test/docs hunks
if necessary, then reload that MCP connection; no data rollback is needed.
Restoring WRITE restores the reported false hold. Overall release remains
PARTIAL / NOT_READY for the independent gates recorded in RELEASE_READINESS.

## Whole-repository lint checkpoint

`VERIFIED_RUNTIME`: root `.venv/bin/ruff check .` now passes, down from23 findings.
Nine skill-bundled Python files received inspected import/print/dead-local/variable
name or statement-layout cleanup. Both preexisting untracked skill directories
were retained. Original files and hashes are backed up at
`/tmp/xn-skill-lint-backup-0yuaub13` with private permissions. All nine parse as
Python; no bundled script was executed for this cleanup. No rule ignore or lint
configuration reduction was introduced; CI now checks the root scope. This is
static verification, not artifact-generation behavior proof.

Exact skill-script paths relative to `.agents/skills/`:
`consulting-pptx-skill/scripts/check_deck.py`, `consulting-pptx-skill/scripts/new_deck.py`,
`pdf/scripts/extract_form_structure.py`, `pptx-skills/shared/scripts/extract_template.py`,
`skill-creator/eval-viewer/generate_review.py`, `skill-creator/scripts/aggregate_benchmark.py`,
`skill-creator/scripts/generate_report.py`, `skill-creator/scripts/quick_validate.py`,
and `skill-creator/scripts/run_loop.py`. Restore only these reviewed hunks from
their private backup if required; do not remove either untracked skill directory.

Graph continuation2026-11-15: [Phase3](PHASE_3_REPORT.md) hardens outbox ownership/current-version markers and prevents provider error payload logging.225 related cases and real isolated Neo4j plus fresh graph-only installed profile pass. Minimal installed MCP remains operational without the optional graph dependency. No approval/security boundary is weakened; independent positive approval remains unavailable, native-client activation and owner reconciliation remain open.

Backup continuation2026-11-15: [Phase3](PHASE_3_REPORT.md) adds manifest/path/SQLite integrity, offline cutover and safety-snapshot guards with116 relevant passing tests and installed-MCP restore evidence. Approval remains independently held; a local restore confirmation flag is not a human-authenticated MCP channel. A point-in-time restore rewinds approval/idempotency records and requires external reconciliation. No policy downgrade, owner restore or host mutation occurred.

Continuation2026-11-15: the remaining packaging/audit verification after interruption passed18 tests in2.24s. Subsequent [Phase3 recovery work](PHASE_3_REPORT.md) adds versioned workflow checkpoints, cooperative policy/deadline/cancellation boundaries, local concurrency protection and installed-MCP recovery without repeating completed writes. Current211 combined/123 scoped test evidence overlaps the earlier runs and does not clear the missing independent approval channel. Existing H1 fail-closed guards and owner configuration are preserved; release remains NOT_READY.

## Internal approval and installed-wheel continuation — 2026-11-14

Status: **verified bounded containment; Phase1/H1 and release remain PARTIAL / NOT_READY**. This continuation starts from the previous836/98 checkpoint below and preserves its working tree. It adds no tool, provider, agent, database or approval bypass flag.

| Finding | Evidence before | Implemented result | Limit |
|---|---|---|---|
| Internal approval service accepted configured display names/IDs as consent; matching legacy approved rows remained reusable | VERIFIED_TEST:5 failing isolated cases | Public approve always holds; legacy validation rejects unverified issuance; owner rejection uses exact configured principal IDs, including STDIO fallback | Genuine positive approval issuance and single-use consumption still unavailable |
| HEBAT direct/token upload skipped approval for owner; deletion accepted confirm=true | VERIFIED_TEST:3 direct cases and1 failed-token case reached synthetic providers before patch | Owner no longer skips validator/request; confirm=true is held before reads/effects; deletion tool retains inspection and has no boolean-authorized mutation branch | No institutional live action attempted; lower-level trusted Python/provider routines are not a sandbox |
| Requests/inbox still advertised removed WhatsApp buttons/commands; inbox failures logged private summaries/exceptions | VERIFIED_TEST:6 failures before correction | Shared truthful inbox/channel status; no obsolete `/approve` promise; failure logs contain type only | Inbox delivery is local storage, not human approval |
| Container checkout was current but installed wheel came from stale cache | VERIFIED_RUNTIME:outside-checkout service assertion failed; source/installed hashes differed | Force reinstall own locked project and fail build on mismatched/missing/extra runtime files; current663-file parity passes | Earlier source-STDIO smoke remains scoped evidence; import counts alone did not prove installed revision |

Exact source/build files: `xninetzy/os/hitl/approval_service.py`, `approval_tools.py`, `xninetzy/os/notifications/admin_notifier.py`, `xninetzy/os/academic/hebat/tools.py`, `qa_portal/tools.py`, `mahasiswa_portal/tools.py`, `Dockerfile`, `scripts/check_installed_package.py`, `.github/workflows/quality-gates.yml`. Exact regression files: `tests/os/hitl/test_internal_approval_boundary.py`, `test_approval_concurrency.py`, `test_hitl.py`, `tests/os/policy/test_action_policy.py`, `tests/os/notifications/test_admin_notifier.py`, `tests/os/academic/hebat/test_hebat_direct_admin_approval.py`, `test_hebat_upload_flow.py`, `tests/os/academic/test_qa_portal_tools.py`, `test_krs_war_tools.py`, `tests/architecture/test_container_deployment.py`, `tests/tools/test_installed_package.py`. Inventory JSON and the existing audit/architecture/release/runbook documents are refreshed.

Verification: **361 passed in225.86s** in the combined HITL/policy/academic/notifications/MCP/privacy/workflow/graph selection, and **12 packaging/deployment checks passed in0.29s**. Earlier32/151/29 selections overlap and are not summed. No failure/skip/xfail/warning reported in these final selections. Existing positive approval transition/concurrency/rollback and roadmap effect tests still exercise the same atomic kernel as explicit private unit tests; they do not authenticate a person. Public-service negative tests run without mocking away the authorization guard. QA and KRS integration fixtures use the real validator with a matching legacy approved row and confirm zero submit/arm effects. Canonical Ruff, strict571-tool inventory, prompt integrity and diff checks pass. CI now includes these regressions and non-editable installed-package parity.

Executed combined command:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q \
  tests/os/hitl tests/os/policy tests/os/academic/hebat \
  tests/os/academic/test_qa_portal_tools.py tests/os/academic/test_krs_war_tools.py \
  tests/os/notifications tests/interfaces/test_execution_boundary.py \
  tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py \
  tests/interfaces/test_mcp_server.py tests/interfaces/test_transport_authority.py \
  tests/policy tests/tools/test_execution_policy.py tests/tools/test_mcp_audit.py \
  tests/tools/test_release_check.py tests/core/test_output_sanitization.py \
  tests/core/test_secret_redaction.py tests/workflow tests/os/graph
.venv/bin/python -m pytest tests/architecture/test_container_deployment.py tests/tools/test_installed_package.py -q
```

Runtime: corrected image `xninetzy:approval-hardening-20261114`, ID `sha256:2866147d6cb006a2fce10703accf46bc7589b314436eae966c0fd75cfe2fc90a`. From `/tmp`, the installed wheel denies raw service approval and matching legacy-approved authorization using disposable SQLite. Isolated MCP smoke passes571-tool discovery, safe read, explicitly allowed synthetic write, denial/mismatch, restart persistence and replay. Network disabled, unprivileged user, read-only root; no owner mount or deployment. Build and an isolated runtime check confirm663 `.py/.json/.sql` runtime files match the checkout, respecting the explicit source-test exclusion while still rejecting unexpected installed files. One intermediate build correctly failed on an intentionally excluded empty test package; the comparator was aligned with the existing manifest and that exception has its own regression. No package/version/lock upgrade occurred.

Compatibility/data: public tool names and argument shapes remain; unsafe identity-only approval, owner submission bypass and confirm-only deletion intentionally stop working. Pending/legacy-approved rows remain untouched, but their stored status cannot authorize new effects. No schema migration or owner data/configuration change. `_apply_status_decision` is an internal transition primitive, not a supported authorization entrypoint; only authorized rejection reaches it from public code. Positive approval is held until an independently authenticated issuer and exact-operation single-use consumer are implemented. Runtime/client principals are not human consent.

Performance: runtime latency/RSS/CPU deltas NOT_MEASURED. Package parity adds build/verification work, not per-request work; only the own project is rebuilt while dependency cache is retained. Tool count571, risk counts133/6/409/23 and candidate prompt1861 tokens are unchanged. Native client connections/configuration were not modified; previous9 SDK probes remain historical transport evidence, not new native activation certification.

Rollback: review only this batch's source/build/test hunks and preserve the preexisting working tree, owner stores, legacy approval rows and config receipts. No database rollback is needed. Do not deploy/reuse a prior cached image on the strength of import/tool counts; rebuild it with parity checks and review the restored security behavior first. Next P0: independently authenticated owner review/issuance plus principal/payload/scope/expiry-bound consumption and reconciliation. Next P1: interrupted workflow/live graph recovery and native OpenCode diagnosis. Do not convert a tool argument, configured identity, private unit-test kernel or inbox note into approval evidence.

## Earlier Phase1 execution boundary checkpoint — 2026-11-14

Final verification: **836 passed in646.51s**, no failures/skips/xfails/warnings reported in the expanded isolated selection documented in BASELINE_TEST_RESULTS.md. That run preceded the final scoped trace-privacy, redaction-performance and auto-hook replay corrections. The complete affected privacy/adapter/MCP/Lightning selection then passed **98 tests in24.56s** on final source; these overlapping counts are not summed. Earlier wire/audit10 and acceptance64 also passed. Strict inventory, six actual release validators, canonical prompt integrity, canonical Ruff and diff checks pass. Fresh9/9 SDK connection probes pass; native-client activation is a separate limitation. Container verification uses the exact final artifact recorded below and in CLIENT_CONNECTION_RESULTS.json, with no production deployment.

This section supersedes earlier statements that the MCP adapter has no common execution gate, idempotency is only payload-sensitive, or loopback HTTP is usable. Safe repository-local implementation is delivered; **Phase1/H1 acceptance remains PARTIAL and the release remains NOT_READY** because independently authenticated owner approval and complete consequential domain coverage are not demonstrated. Denying consequential execution contains the reproduced paths; it does not implement usable authentic approval.

| ID | Finding / implemented behavior | Evidence | State |
|---|---|---|---|
| P1-01 | Canonical571-name risk catalog; unknown names fail closed; current distribution133 READ/6 DRAFT/409 WRITE/23 FINAL | VERIFIED_CODE catalog/manifest/action classifier; VERIFIED_RUNTIME regenerated strict inventory | Implemented; conservative WRITE classifications still need semantic audit |
| P1-02 | MCP handlers previously bypassed common policy; adapter now enforces principal, risk, global/explicit owner restrictions and kill switch before effects | VERIFIED_TEST forged IDs, confirmation/description poisoning, manual/approval mode and all23 FINAL denial matrix | Contained; independent human approval channel unavailable |
| P1-03 | Payload-sensitive keys allowed changed-payload reuse; strict gateway reservations bind owner/tool/key to normalized payload and retain uncertain/pending outcomes | VERIFIED_TEST replay/mismatch/concurrency/cross-client owner scope; VERIFIED_RUNTIME container restart/replay | Implemented at MCP/context boundaries; legacy domain helper remains compatible |
| P1-04 | Caller read-only declarations could downgrade canonical/context-provider operations | VERIFIED_TEST canonical risk raise, selected-provider metadata and replay argument mismatch; missing external classification held | Fixed tested boundaries, not every direct Python/domain entrypoint |
| P1-05 | Transport validation occurred after state access, and Settings inspection created a database | VERIFIED_TEST invalid/unauthenticated HTTP cannot create DB; read-only optional overrides | Fixed; HTTP intentionally unavailable |
| P1-06 | Learned patches could overwrite any setting, including database path/permission controls | Seven failing regressions before; bounded shared tuning allowlist, protected legacy rows preserved, cache updated after persistence | Fixed tested load/apply/rollback boundary |
| P1-07 | Generic LangChain output schema lost callable return contract; worker timeouts released effective concurrency too soon | Failing output-contract regression before; resolved return validation, bounded input/output, retained worker slots, privacy/telemetry tests | Fixed tested paths; Any and semantic outcome verification remain limited |
| P1-08 | A read-only audit-skippable operation with no invocable reported success | VERIFIED_TEST now reports error/not executed while preserving documented no-audit behavior | Corrected completion claim |
| P1-09 | Redaction repeatedly scanned long unrelated tokens; a40041-character fixture exceeded2s | VERIFIED_TEST regression plus measured size scaling; fixed domain-first scan and2000 seeded compatibility comparisons | Corrected measured resource cost; no production latency/SLO claim |
| P1-10 | Canonical automatic hooks ran on reads and replayed writes | Two failing regressions before; final tests verify zero read hooks and a single write hook set inside reservation | READ/DRAFT no longer auto-persist canonical memory/graph/improvement state; telemetry remains separate |

Exact current batch source files: `xninetzy/core/config.py`, `core/security.py`, `db/idempotency.py`, `interfaces/mcp_tool_adapter.py`, `interfaces/mcp_server.py`, `context/invocation/classify.py`, `context/policy/gate.py`, `context/routing/policy.py`, `context/orchestrator/pipeline.py`, `os/policy/action_policy.py`, `os/lightning/patch_executor.py`, `tools/manifest.py`, `tools/execution_policies.json`, `tools/tool_meta.py`, `tools/release_check.py`, `cli/supervisor.py`, `scripts/mcp_audit.py`, `scripts/smoke_container.py`. Earlier continuation files remain separately documented below; the full workspace diff contains preexisting work.

Regression/CI files: `tests/conftest.py`, `tests/interfaces/test_execution_boundary.py`, `test_transport_authority.py`, `test_mcp_server.py`, `test_mcp_tool_adapter.py`, `test_trust_injection.py`, `tests/tools/test_execution_policy.py`, `test_mcp_audit.py`, `tests/policy/test_policy_gate.py`, `tests/orchestrator/test_orchestrator_pipeline.py`, `test_pipeline_reasoning_hook.py`, `tests/core/test_output_sanitization.py`, `tests/os/lightning/test_patch_executor.py`, `tests/evaluation/test_replay_poison.py`, `tests/governance/test_execution_authority.py`, `test_mcp_surface.py`, `.github/workflows/quality-gates.yml`. Historical `tests/governance/test_no_comments.py` was retired: it xfailed on a nonexistent AGENTS section prohibiting comments/docstrings, incompatible with required MCP descriptions. Two current authority regressions replace that obsolete governance rule; no functional scenario was skipped/xfail-ed to hide a defect.

Test isolation now selects temporary mutable paths before collection and disables deployment `.env` loading in the test process. MCP subprocess tests use the installed interpreter and explicitly inherit fixture environment; they do not invoke dependency installation. An omitted SDK subprocess env initially hit the existing wrong-store guard and closed before starting; the fixture was corrected rather than weakening that guard. Controlled external-provider fixtures explicitly declare trusted read-only metadata, retaining their effect/audit assertions.

Verification known at this checkpoint: focused policy/startup/boundary tests115 passed; a later expanded run828 passed/5 failed in545.18s found output and fixture/metadata drift; these were corrected. Current wire MCP/audit retest10 passed in16.43s. The final combined result is recorded in the final verification section below, not inferred by summing overlapping runs. Canonical Ruff (`xninetzy tests scripts`), diff checks, prompt integrity and six bounded release validators pass. Root `ruff check .` additionally reports23 skill/vendor findings outside the CI scope; owner copies were preserved.

Actual rebuilt minimal Python3.11 image `xninetzy:phase1-20261114`, ID `sha256:4cfa64c0ebbce8fd006a95dadd8955f8c006d8941969957b448217907e843765`, passes initialization,571-tool discovery, safe read, explicitly permitted synthetic local write, missing-key/changed-payload/unauthorized-confirmation denial, orderly restart and single-result replay. Network disabled, nonroot, read-only root, disposable state; no owner mounts. Installed wheel was also inspected from `/tmp`:571 packaged policies, Torch and Sentence Transformers absent. Source tests after the build only refine fixture isolation; application/runtime policy source matches the tested image. No production rollout occurred.

Compatibility: no tool names removed/renamed, no new database/framework/agent. MCP hides trusted owner/context parameters and adds `idempotency_key` where mutation handlers lack one; nonblank key is enforced at execution. Writes still respect global default approval/manual policy; only isolated fixtures select automatic local writes. FINAL remains unavailable even with auto mode or forged IDs. Clients must rediscover schemas after reconnecting. Gateway-v1 reservations reuse the existing table without migration, while legacy domain rows remain unchanged; reconcile pre-upgrade work rather than assuming its old keys are gateway records. All ambiguous outcomes remain quarantined; no automatic pending reset or external exactly-once claim.

Performance: Codex candidate remains1861 cl100k_base tokens (353+1035+275+198), no host prompt installation. Latency/RSS/CPU before/after impact is NOT_MEASURED. Higher selected test counts and lower prompt text size are not task-success metrics. Host connection candidates are SDK-tested separately; OpenCode native activation and full cross-client model parity remain unverified.

Rollback: review individual source/test/catalog hunks or a verified image. Preserve unrelated workspace changes, owner stores A/B, config backups, protected override rows and all legacy/gateway reservations. No schema reset is needed. Reconnecting/reverting an active owner service is an operational action, not implied by an image build. Next priorities: independent owner approval issuance plus exact-payload atomic consumption/reconciliation, interrupted workflow recovery and live optional-service acceptance. See [governance](../architecture/TOOL_GOVERNANCE.md), [release gates](../release/RELEASE_READINESS.md) and [test evidence](../audits/BASELINE_TEST_RESULTS.md).

Date: 2026-11-10. Status: **PARTIAL phase, verified local batches; release NOT_READY**. Scope: existing runtime and contracts, no architectural replacement. [Phase 0](PHASE_0_REPORT.md) records the baseline; [test results](../audits/BASELINE_TEST_RESULTS.md) distinguish individual runs.

## Findings, implementation and verification

| ID | Current behavior change | Evidence | Status / remaining boundary |
|---|---|---|---|
| SEC-01 | Invalid explicit side-effect names now raise ValueError; pure policy returns BLOCK with invalid_side_effect | 28 new/updated regressions failed before; 90 invocation/policy/orchestrator + 16 reasoning-depth tests passed after | Fixed explicit malformed declaration path; omitted None and valid caller-declared read-only remain compatible and require canonical risk binding |
| SEC-04 | Redact nested credential-key values/text assignments and shared token patterns before telemetry truncation | Synthetic baseline 14 failures/1 pass; 39 combined redaction/Lightning tests pass, including persisted SQLite assertions | Fixed tested future event path; prior traces and other persistence hooks unchanged |
| SEC-05 | Reject existing pending idempotency reservation instead of executing again | Two failing deterministic tests before; 9 idempotency tests pass after | Stored results replay; crashes require reconciliation; no exactly-once external promise |
| SEC-06 | Resolve flat package root correctly; preserve legacy services/ai fixtures and explicit paths; refuse ambiguous existing store selection | Four original regressions fail before; 17 mapping tests pass after guard | No data moved; process environment must explicitly select store if sibling legacy DB exists, including when corrected env lookup discovers a different .env choice |
| AUD-01 | Strict audit checks required FINAL policies, approval/idempotency declarations and duplicate names; optional full inventory | Six regression tests fail before; 25 audit/manifest/registry tests pass after | Runtime enforcement and provider availability remain UNKNOWN |
| SKL-01 | Replace broad skill xfails with strict YAML, eligible runtime validation and explicit two legacy rejections | 14 focused tests pass; no xfail | No skills deleted, renamed or installed; nested metadata/routing issues remain |
| PKG-01 | Correct mandatory/optional dependency boundaries for minimal MCP bootstrap | Initial base wheel failed; 34 import/provider/vision/spreadsheet regressions pass; actual base wheel exposes/lists 571 tools and calls datetime with optional packages absent | Fixed minimal bootstrap; 49→64 distributions from existing dependency transitives; all 168 lock package identities/versions unchanged |

## Exact implementation files

Idempotency: `xninetzy/db/idempotency.py`, `tests/db/test_idempotency_store.py`.

Runtime mapping: `xninetzy/interfaces/mcp_runtime.py`, `tests/interfaces/test_mcp_runtime.py`.

Telemetry: `xninetzy/os/lightning/rl.py`, `tests/os/lightning/test_input_redaction.py`.

Policy: `xninetzy/context/invocation/classify.py`, `xninetzy/context/policy/gate.py`, `tests/invocation/test_invocation_contract.py`, `tests/policy/test_policy_gate.py`, `tests/orchestrator/test_orchestrator_pipeline.py`.

Audit: `scripts/mcp_audit.py`, `tests/tools/test_mcp_audit.py`, `docs/audits/TOOL_INVENTORY.md`, `docs/audits/tool_inventory.json`.

Skill evidence: `tests/governance/test_skill_frontmatter.py`, `tests/os/skills/test_skills.py`, the instruction/skill/context reports linked from Phase 0.

Minimal dependencies: `pyproject.toml`, `uv.lock`, `xninetzy/core/llm.py`, `xninetzy/tools/ecosystem/vision_tools.py`, `xninetzy/context/data_analysis/profiling.py`, `xninetzy/context/data_analysis/table_artifact.py`, `tests/architecture/test_minimal_dependencies.py`.

CI: `.github/workflows/quality-gates.yml` now runs critical execution regressions and canonical prompt validation, plus a separate frozen base-only installed-wheel smoke outside the checkout. YAML parses; the exact smoke step was executed locally with the isolated installed interpreter and passed (571 tools + safe read). Remote Actions and Python 3.11 execution remain unverified in this environment.

## Contracts, compatibility and state

No public tool was added, deleted or renamed. No database schema migration, owner configuration installation or production data change occurred. Invalid explicit side-effect declarations intentionally stop being accepted; valid normalized classes and omitted legacy classification retain behavior. Idempotency keeps its existing `(scope,key,payload)` identity; changed payloads remain separate executions until a separately designed compatibility change. Ordinary callable exceptions still release reservations, so callers must reconcile external uncertain delivery rather than blindly retry.

Path correction intentionally refuses an ambiguous host restart rather than selecting a different existing database. This can require an explicit process setting before restart. It never chooses a database by size/mtime or copies/migrates data. Installed package path behavior and legacy paths have separate tests.

The dependency correction reuses an already-supported library; provider/embedding/browser/document extras stay optional. Installed package versions in the lock are preserved; only dependency ownership changes. CPU/RSS/latency improvements from lazy imports are NOT_MEASURED.

## Performance and limitations

The verified benefits are prevented duplicate execution in concurrency fixtures, blocked malformed-class invocation, removed synthetic secret persistence and successful invariant checks. Before/after runtime throughput, production incidence and end-user completion gains are NOT_MEASURED. [Performance baseline](../evaluation/PERFORMANCE_BASELINE.md) contains a single-process smoke, not a speedup comparison.

Open release blockers include approval authenticity and single-use consumption, caller-controlled valid risk declarations, obsolete container entrypoint/health contract, graph false acknowledgements, and unexecuted full release acceptance. Full repository Ruff reports 125 findings outside this focused batch. No failures were hidden through new skips or xfails.

## Rollback and next priorities

Review/reverse only these source/test hunks; preserve initial user deletions/untracked directories. No database rollback is needed. Reverting security fixes restores the reproduced failures and should require deliberate review. Never remove pending reservations without reconciling their effects. Restore dependency manifest and lock together if reverting packaging changes.

Next: independent exact approval verification and atomic consumption; canonical risk at execution; then deployment and truthful workflow/graph recovery. Keep release NOT_READY until those boundaries have sufficient acceptance evidence.

## Final foundation checkpoint

Combined foundation/domain/contract run: **411 passed in 108.92s**, no failed/skipped/xfail reported. This includes the earlier suite selections plus all new malformed-class, reasoning and minimal-import tests and existing provider factory tests. Separate image/spreadsheet/optional import run: **34 passed in 10.21s** (overlaps the combined run; do not add counts). Subsequent workflow/graph batches are recorded separately in Phase 3 and require their own final regression.

Strict audit and regenerated-schema comparison confirm all **571** saved inventory rows match current registry declarations. All six installed shared/client instruction hashes still equal the initial snapshot. Focused Ruff, shell syntax and diff whitespace checks pass; full Ruff remains **125 findings**. No full-suite or release-green claim follows from this checkpoint.

## H1/H5/H6 continuation

The paragraph above is the previous checkpoint. Current changes start from committed `74ff58b`.

H1 containment reproduced **14 failed /42 passed** before the correction. The context policy previously accepted an arbitrary approval integer, and a model-facing `hitl_approve` call received the trusted installation principal and could approve its own isolated request and invoke a synthetic effect. The context gate now always returns REQUIRE_APPROVAL with `approval_channel_unverified` for irreversible execution until independent authorization is integrated. The model-facing approval tool leaves the row pending and does not call the approval service. Names/arguments stay compatible; formerly accepted self-approval and unverified irreversible execution deliberately stop working. Related isolated policy/HITL/MCP identity regression: **91 passed**.

Exact H1 files: `xninetzy/context/policy/gate.py`, `xninetzy/os/hitl/approval_tools.py`, `tests/policy/test_policy_gate.py`, `tests/orchestrator/test_orchestrator_pipeline.py`, `tests/os/hitl/test_model_approval_boundary.py`. Tool description changes are reflected in regenerated `docs/audits/tool_inventory.json`. This is containment, **not completed approval authenticity**: the underlying service still needs an independent owner channel, identity binding and atomic consumption; valid caller-declared READ_ONLY and per-domain execution paths remain separate release questions.

H5 revalidated125 Ruff findings: F40192, F5416, F84110, F6011, F8113, F8216, E7416 and E4021. The final whole-repository command `.venv/bin/ruff check xninetzy tests scripts` passes with **zero findings**, no rule-ignore/config changes. Safe unused imports/placeholders were removed, unused assignments retained required expression side effects, shadowed duplicate implementations were removed without replacing the effective implementation, and ambiguous locals were renamed. Correctness repairs add missing Keyframe/VideoTrack decoder imports, missing taxonomy Any and pytest imports. The video public export remains available. A real synthetic project decoder roundtrip now covers tracks and keyframes.

H6 changes only `xninetzy/os/knowledge/embeddings.py` plus `tests/os/knowledge/test_embedding_dimensions.py`: prefer current `get_embedding_dimension`, retain the older method for supported older models, reject missing/nonpositive/nonintegral/bool dimensions before index allocation. The existing fallback remains explicitly numpy_tfidf/256; no index is deleted/rebuilt and no semantic quality improvement is claimed. Current-API tests fail if the deprecated method is called; warnings are not suppressed. The new decoder/embedding delegated red run was7 failed/2 passed.

Further routing regression found performance group unmapped. `xninetzy/context/registry/taxonomy.py` now maps it into software; `tests/test_routing_taxonomy.py` requires no unmapped current groups and uses actual registry cardinality instead of historical33. No domain, tool, database, agent runtime or provider was added.

Rollback: selectively restore the reviewed hunks, preserving unrelated owner changes. Reverting H1 containment reopens the reproduced self-approval path; it requires deliberate review. No owner database/schema rollback is needed. Revert neither lint configuration nor tests to hide failures. Client connection changes remain a repository candidate until explicit store selection; see CLIENT_CONNECTIONS.md.

## Truthful release diagnostics, 2026-11-11

VERIFIED_CODE: `xninetzy/cli/supervisor.py::_cmd_release_check` hardcoded PASS for redaction, SSRF, transport and SDK, including a stale1.28.1 version. The shared `xninetzy.tools.release_check.run_release_checks` already implements actual deterministic checks. The supervisor now invokes those validators, reports their actual details/statuses, fails on WARN/BLOCKED, retains audit-failure rejection and catches unexpected validator errors without printing potentially sensitive exception messages. No public tool, schema, dependency, identity or permission changed.

Tests first: `.venv/bin/python -m pytest tests/cli/test_supervisor.py -q -k 'actual_validator or validator_exception'` returned **13 failed**; after correction the same selection returned **13 passed**. Each shared validator is independently replaced with a failing result for BLOCKED and WARN, and invocation/results are asserted. A synthetic private exception sentinel must not appear in CLI output.

Related isolated regression: **43 passed in12.51s** for `tests/cli`, `tests/tools/test_release_check.py`, `tests/tools/test_mcp_audit.py`, `tests/architecture/test_container_deployment.py`, `tests/tools/test_client_connection_config.py`. Mutable paths were temporary; settings `.env` disabled in the parent; automatic hooks/Neo4j disabled. This is a supplemental run, not43 new end-to-end tasks or a total to add to the earlier781 overlapping selection. Full Ruff remains zero. Real execution of release-check inside the network-isolated minimal image reports measured SDK1.30.0 and all six bounded checks PASS; Phase 3 records exact commands/provenance.

Files: `xninetzy/cli/supervisor.py`, `tests/cli/test_supervisor.py`, `.github/workflows/quality-gates.yml` (critical step now includes CLI regressions), and current truth/security/backlog/release/runbook/checkpoint documents. Container source/tests are enumerated in Phase 3; client helper source/tests in CLIENT_CONNECTIONS.md. No database migration or host config installation occurred. Roll back reviewed source/test hunks if necessary; reverting this diagnostic fix restores misleading evidence. PASS from this command does not replace RELEASE_READINESS.md's independent owner-authorization and operational gates.

## Authorized MCP connection installation after owner selection A

2026-11-11: owner explicitly chose A, resolving the two-store ambiguity. The existing plan/apply helper installed nine MCP entries for eight compatible hosts, all selecting `/home/misbahul45/code/xninetzy/services/ai/data/xninetzy.sqlite3`. Every saved candidate/hash and original0600 backup was verified; native Codex parses the installed command/A path; repeat plan reports zero changes. Permission settings and unrelated configuration are preserved. The private receipt/backup locations are documented in CLIENT_CONNECTIONS.md, not copied as credential-bearing artifacts into the repository.

Post-install smoke exposed an installer-only defect before server invocation: rendered quoted TOML table headers were not recognized on replan. Three new fixture cases failed before correction. `scripts/connect_mcp_clients.py` now parses header paths with tomllib instead of comparing only bare strings, while retaining whole-document equivalence validation. `tests/tools/test_client_connection_config.py` covers bare/double/single-quoted header roundtrips; all12 tests pass. Already-correct host files needed no second write.

Verification commands: plan/`--apply --store <A>`, read-only same-store replan, `--smoke`, native `codex mcp get xninetzy --json`, `.venv/bin/python -m pytest tests/tools/test_client_connection_config.py tests/cli/test_supervisor.py tests/interfaces/test_mcp_runtime.py -q` (**49 passed in12.95s**), full Ruff and `git diff --check` (pass). The initial post-install smoke failed during TOML parsing; rerun after correction passes **9/9** with571 tools/protocol2025-11-25 and verified datetime output. All SDK runtime probes override mutable paths to temporary stores, not A. Raw file hashes confirm both owner databases and three shared global prompt files remain unchanged; no owner-state migration or global prompt installation occurred.

Limits: installed config is not native GUI reload, every agent's permission eligibility or live owner-database verification. Existing sessions need reconnect/restart to load saved settings. ArkCLI generic MCP-host support and the missing standalone Copilot executable remain unverified/unsupported, with VS Code Copilot configured through its installed host. No before/after speedup is inferred from single-run timings. Rollback restores the matching protected backup only after checking the receipt/current hashes and preserving later owner edits. No database rollback is necessary. Trusted approval, canonical risk and external recovery remain the next security/operational priorities; release remains PARTIAL / NOT_READY.

## Continuation file ledger

Additional continuation files after the original ledger: `xninetzy/os/hitl/approval_service.py`, `tests/os/hitl/test_approval_concurrency.py`. The existing client helper/test and reports also receive the OpenCode2.x follow-up below. No schema migration or new tool/agent/service is introduced.

Exact changed/new repository files in this continuation from `74ff58b` (preexisting untracked skill directories excluded and preserved). Review by hunk; this list does not authorize commits, host installation or production deployment. No schema migrations. Performance improvements beyond the measured correctness/context/lint results remain NOT_MEASURED.

- `.dockerignore`
- `.github/workflows/quality-gates.yml`
- `Dockerfile`
- `docker-compose.yml`
- `docs/architecture/ADR-001-INCREMENTAL-HARDENING.md`
- `docs/architecture/MCP_PROTOCOL_CONTRACT.md`
- `docs/audits/BASELINE_TEST_RESULTS.md`
- `docs/audits/CURRENT_SYSTEM_TRUTH.md`
- `docs/audits/GAP_ANALYSIS.md`
- `docs/audits/SECURITY_RISK_REGISTER.md`
- `docs/audits/tool_inventory.json`
- `docs/evaluation/CLIENT_CONNECTION_RESULTS.json`
- `docs/evaluation/GLOBAL_AGENTIC_BASELINE.md`
- `docs/evaluation/PERFORMANCE_BASELINE.md`
- `docs/implementation/CLIENT_CONNECTIONS.md`
- `docs/implementation/PHASE_0_REPORT.md`
- `docs/implementation/PHASE_1_REPORT.md`
- `docs/implementation/PHASE_3_REPORT.md`
- `docs/release/KNOWN_LIMITATIONS.md`
- `docs/release/OPERATIONS_RUNBOOK.md`
- `docs/release/RELEASE_READINESS.md`
- `scripts/build_olist_workbook.py`
- `scripts/career/oauth_workflow.py`
- `scripts/connect_mcp_clients.py`
- `scripts/extract_routing_registry.py`
- `scripts/repair_skill_yaml_v2.py`
- `scripts/smoke_container.py`
- `tests/architecture/test_container_deployment.py`
- `tests/cli/test_supervisor.py`
- `tests/interfaces/video_backends/test_remotion.py`
- `tests/media/video/test_capability_seed.py`
- `tests/media/video/test_models.py`
- `tests/media/video/test_storage_roundtrip.py`
- `tests/media/video/test_video_validators.py`
- `tests/orchestrator/test_orchestrator_pipeline.py`
- `tests/os/hitl/test_model_approval_boundary.py`
- `tests/os/knowledge/test_embedding_dimensions.py`
- `tests/policy/test_policy_gate.py`
- `tests/test_routing_abstention.py`
- `tests/test_routing_benchmark.py`
- `tests/test_routing_capability_graph.py`
- `tests/test_routing_dataset_expansion.py`
- `tests/test_routing_fine_tune.py`
- `tests/test_routing_laya.py`
- `tests/test_routing_lazy_schema.py`
- `tests/test_routing_pipeline.py`
- `tests/test_routing_production.py`
- `tests/test_routing_regression.py`
- `tests/test_routing_routers.py`
- `tests/test_routing_shadow.py`
- `tests/test_routing_taxonomy.py`
- `tests/test_routing_warmup.py`
- `tests/tools/ecosystem/test_media_video_tools.py`
- `tests/tools/test_client_connection_config.py`
- `xninetzy/cli/supervisor.py`
- `xninetzy/context/capability_graph/builder.py`
- `xninetzy/context/media/video/__init__.py`
- `xninetzy/context/media/video/project_engine.py`
- `xninetzy/context/media/video/renderers/router.py`
- `xninetzy/context/media/video/storage.py`
- `xninetzy/context/media/video/validators.py`
- `xninetzy/context/policy/gate.py`
- `xninetzy/context/registry/taxonomy.py`
- `xninetzy/context/registry_extractor/extract.py`
- `xninetzy/context/routing/abstention.py`
- `xninetzy/context/routing/baselines.py`
- `xninetzy/context/routing/benchmark.py`
- `xninetzy/context/routing/calibration.py`
- `xninetzy/context/routing/dataset.py`
- `xninetzy/context/routing/embeddings_index.py`
- `xninetzy/context/routing/fine_tune.py`
- `xninetzy/context/routing/hard_negatives.py`
- `xninetzy/context/routing/lazy_schema.py`
- `xninetzy/context/routing/pipeline.py`
- `xninetzy/context/routing/policy.py`
- `xninetzy/context/routing/production.py`
- `xninetzy/context/routing/regression.py`
- `xninetzy/context/routing/routers.py`
- `xninetzy/context/routing/shadow.py`
- `xninetzy/os/auth/browser/gateway.py`
- `xninetzy/os/hitl/approval_tools.py`
- `xninetzy/os/knowledge/embeddings.py`
- `xninetzy/os/research/sources/browser_session.py`
- `xninetzy/tools/ecosystem/routing_pipeline_tools.py`
- `xninetzy/tools/ecosystem/routing_taxonomy_tools.py`

## Atomic approval decisions and native-client follow-up, 2026-11-14

VERIFIED_TEST: two concurrent service-level approvals could both read pending, both overwrite status and both invoke the synthetic action. A stale approver could overwrite rejection; a stale expiry decision could overwrite a completed approval. An interrupted action left an approved row with no recorded outcome but a subsequent approve incorrectly reported success. These are service-level fixture findings, not evidence of a live portal attack or genuine human approval.

Tests first: `pytest tests/os/hitl/test_approval_concurrency.py -q --tb=short` returned **4 failed,1 passed**. `set_approval_status` now uses `UPDATE ... WHERE id=? AND status='pending'` and requires rowcount1 before committing the winning decision and invoking an effect. Stale decision/expiry updates cannot overwrite another winner. An already-approved row without execution_at returns False with `approval_execution_unverified` and reconciliation guidance; it is never automatically rerun. Completed duplicate approvals retain their existing acknowledgement behavior. No SQL transaction spans the effect, and no table/migration is added.

Five focused cases pass: simultaneous approval, approve/reject race, stale expiry race, rollback before effect and synthetic SystemExit after effect. The identity predicate and action implementation are controlled fixtures; SQLite and migrations are real temporary data. This demonstrates an atomic **decision claim**, not complete single-use external approval consumption. `validate_approval` remains a validation-only reader, owner-name fallback/trusted-channel limitations remain, and exactly-once external delivery is not claimed.

Related isolated regression selection: `tests/os/hitl tests/os/policy tests/policy tests/orchestrator tests/db/test_idempotency_store.py tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py tests/cli/test_supervisor.py`: **125 passed in203.02s**, with temporary writable paths, parent `.env` disabled and background hooks/optional services off. Current focused approval/client selection: **21 passed in2.46s** (5 approval +16 client cases); full Ruff and diff checks pass. These overlap earlier781/49/43 counts and must not be added as a whole-suite total. Critical CI already includes tests/os/hitl and tests/tools.

Native probing exposed a separate actual compatibility gap: installed OpenCode2.2.6 writes servers under mcp.servers and uses disabled, whereas the previous helper emitted flat entries/enabled. Three initial migration regressions failed; enabled-flag regressions then failed3 cases before their correction. The helper now moves only Xninetzy into the verified2.x schema, converts enabled to disabled without changing effective permission and rejects conflicting old/new settings. Kilo retains its separate flat format. All16 client tests pass. OpenCode1.x native compatibility is not claimed by the2.x profile.

Only the two existing OpenCode host files were updated, with protected0600 backups and private receipt `/home/misbahul45/.xninetzy/mcp-opencode-v2-install-20261114T102613327525Z.json`. Before/after parsed comparisons verify every unrelated setting/server value is unchanged; A remains selected; replan is unchanged for both files. SDK smoke passes9/9 after the change. Native Claude health passed with a temporary configuration/registered alias, but native OpenCode list still reports No MCP servers configured even after its own add command writes the documented nested schema in isolated XDG paths. This is NOT_VERIFIED with root cause UNKNOWN, not a passing native test or proof of an upstream defect. Namespace-based extra isolation could not run (bwrap namespace/UID permissions); no sandbox guarantee is claimed. No real background client service was restarted.

The active Codex session now exposes Xninetzy MCP tools and actually returns datetime/skill discovery/body results. This is bounded live session evidence, separate from the SDK probes and from all-host parity. No explicit owner-data mutation, credential change or global-prompt deployment was performed; normal client counters/application telemetry are not claimed absent. Native Claude may update its own promptQueueUseCount; its MCP entries were verified unchanged, so blind whole-file rollback would overwrite newer client state.

Rollback: reverse reviewed service/test hunks only; reverting the decision claim restores a reproduced duplicate-execution race. Restore only matching OpenCode config backups after comparing current/receipt hashes and preserving subsequent owner edits. Do not reset databases, approvals, reservations or graph state. Next priorities: independent principal/payload-bound approval issuance/consumption, native OpenCode configuration-loading diagnostics and controlled external workflow reconciliation. Release remains PARTIAL / NOT_READY.

Decision references: [SQLite conditional UPDATE](https://www.sqlite.org/lang_update.html), [SQLite transaction concurrency](https://www.sqlite.org/lang_transaction.html), [OpenCode2 MCP schema](https://opencode.ai/docs/mcp-servers/), [Claude configuration scope](https://code.claude.com/docs/en/settings). These guide the bounded implementation; tests establish local behavior, not compliance certification.
