# Current release decision

Updated: 2026-11-15. Decision: **PARTIAL / NOT_READY**. Scope: repository audit, local candidate patches and isolated container operation, not production deployment certification. Historical V1 checklists do not override this evidence.

Newest checkpoint: the three `skill_validate_*` writing checks were incorrectly
WRITE. They are verified pure in-memory READ operations;61 related tests and
actual MCP in default approval mode pass on first start/restart, retaining
negative findings and consequential-action holds. Catalog:136 READ/6 DRAFT/
406 WRITE/23 FINAL. Active native MCP connections were not restarted; reload
their connection to adopt the new policy.

Real FAISS durability and opt-in MCP worker activation now pass from source and
a fresh frozen installation, with explicit256-dimensional hash vectors and
cached offline384-dimensional MiniLM. The three-node exact-title check does
not establish retrieval quality. Current minimal image is
`xninetzy:validator-fix-20261115`
(`sha256:650658c1641d8ed3575c1f6db4e98554ec9435be40d9f0fbc3f5238a0672bff2`),
with663-file parity and real local read/write/restart/denial checks. Root Ruff
is now zero; the earlier23 findings were repaired without suppressions.

The complete2888-case suite was attempted but did not finish after filesystem
exhaustion (1085 progress characters captured, final report truncated). Recorded
failures include obsolete documentation risk counts, an unreviewed-provider
success fixture and Remotion rendering. The first two are corrected and pass
focused checks; rendering still needs reproduction. Final178 relevant cases,
2 trust-outcome checks,34-page docs build and final-image workflow/backup smokes
pass. Only the task-created temporary installed environment was explicitly
removed; later `df` reports41G available after runtime completion, without owner
cache/image/data pruning. Peak scratch use remains unprofiled. Independent positive
approval, all native-host activation, labeled golden/retrieval outcomes and a
completed full regression remain release gates. Detailed evidence/rollback:
Phase1/3 and CLIENT_CONNECTION_RESULTS.json.

Latest graph continuation:225 related tests pass after fixing stale outbox ownership/current-version markers, canonical edge data and private error logging. Actual official Neo4j5.26 tests pass from source and a fresh frozen non-editable graph-only environment (663-file parity): relationship properties, duplicate resync, backend stop/restart/retry, SQLite+FTS availability and deletion. The backend uses only an owned internal-network fixture, no published host port or owner data. FAISS is explicitly stubbed and NOT_TESTED there. Final minimal image `xninetzy:graph-hardening-20261115` (`sha256:ecbc8096b2fd9ec3f35cc0531fbdbc201b9742cf8b2e575165848e02e6bda3fb`) separately passes parity and previous wire/backup/workflow smokes without graph extras. This clears a controlled live-backend boundary, not full owner reconciliation, all-client scheduler activation, semantic retrieval durability, native host parity or independently authenticated positive approval. [Phase3](../implementation/PHASE_3_REPORT.md) records evidence/rollback; readiness remains unchanged.

Latest backup continuation (`VERIFIED_TEST` / `VERIFIED_RUNTIME`): existing v1 snapshot verification/retention/offline restore is hardened after reproduced failures, including baseline manifest-directed deletion of a synthetic unrelated directory.116 relevant tests pass, including36 backup cases. Final minimal image `xninetzy:backup-hardening-20261115` (`sha256:757420e8fd6108b50e948212eacd736600e9f41622427983af15dcba8426f38c`) passes663-file parity and installed-MCP online snapshot/offline restore/restart/local replay, previous workflow recovery and general read/write/restart/denial smoke. No owner store/config/process changes. This closes a controlled local backup drill gap; owner restore, offline coordination of every client, live cross-file vectors/graph and external effect reconciliation remain open. Restore confirmation is a local operator acknowledgement, not an independent positive approval channel. See [Phase3](../implementation/PHASE_3_REPORT.md) and [runbook](OPERATIONS_RUNBOOK.md).

Latest workflow continuation: `VERIFIED_TEST` / `VERIFIED_RUNTIME` for bounded local recovery. Resume restores the original typed checkpoint/plan; successful steps are retained, uncertain mutations are held, and policy/cancellation/checkpoint failures stop further effects. Real fixture-process interruption and new-executor recovery pass. Final installed-wheel image `xninetzy:workflow-recovery-20261115` (`sha256:ea96c0cc392970ef0dbc2db61326450dfa7e216868928ff5fb1acecbae23607f`) passes663-file parity and actual MCP same-plan recovery/completed replay/uncertain-write denial from outside checkout. The combined211-test selection preceded the last scoped privacy fix;123 affected tests then pass on final source, including all59 workflow cases. Counts overlap. Nine fresh SDK source probes pass without host changes. [Phase3](../implementation/PHASE_3_REPORT.md) and the [workflow contract](../architecture/AGENTIC_WORKFLOW.md) record exact evidence and rollback. This closes the controlled local recovery gap, not independent approval, live provider reconciliation, full native-client parity or a production rollout.

Latest internal/domain continuation:361 relevant tests and12 packaging checks pass (separate scopes). Public service approval no longer accepts configured names/IDs as consent; legacy approved rows do not authorize subsequent effects. HEBAT owner/token upload bypass and confirm-only deletion are contained below MCP. Inbox notifications now report the unavailable channel truthfully and omit private failure content from logs. The first outside-checkout image check exposed a stale installed wheel despite current copied source; own-project reinstall plus a663-file build/runtime parity gate now passes on image `sha256:2866147d6cb006a2fce10703accf46bc7589b314436eae966c0fd75cfe2fc90a`. Actual installed-service denial and STDIO local write/restart/replay smoke pass with disposable state. Earlier import-count/source smoke did not establish installed revision identity. These are containment and packaging improvements, not independent approval issuance, external single-use consumption, a live portal submission or production deployment.

Latest Phase1 evidence:836 combined isolated tests pass; after final scoped privacy/performance/auto-hook corrections,98 affected tests pass on final source (overlapping counts). Canonical CI lint and six actual release diagnostics pass; root lint retains23 skill/vendor findings outside that scope. Explicit571-tool policy, owner-mode enforcement, strict scoped replay, typed/bounded outputs, transport-before-state and protected learned settings are implemented. Read-only responses and successful replay no longer generate canonical auto-hook mutations. The rebuilt final container passes wire read/write/denial/restart/replay with synthetic state. These close bounded foundation defects, while **Phase1/H1 acceptance remains partial**: independent authenticated approval issuance/consumption, complete consequential/internal path coverage and the operational gates below are still open. No production rollout or host prompt replacement occurred.

## Verified improvements

The docs CI command is now explicit `yarn run check`, avoiding Yarn Classic's built-in-command collision. Its newly exposed feedback dataset-key type error and unused bindings are corrected. Actual Astro check passes 16 files with 0 errors/warnings/hints; build succeeds 34 pages. Remote Actions and browser interaction remain unexecuted. These checks do not change the production decision.

Pending duplicate calls now fail closed; malformed explicit side-effect classes cannot reach handlers; synthetic credentials are redacted before Lightning event persistence; runtime path layout is corrected with explicit selection for ambiguous existing stores; audit invariants accept the current FINAL surface; skill tests expose actual eligibility without broad xfail; canonical prompt guidance has versioned integrity checks. Minimal packaging is verified separately in the final implementation checkpoint.

## Release blockers and limits

Previous checkpoint evidence: **476 passed, 1 warning**. In the continuation, full Ruff is **zero** without configuration changes; the embedding API is corrected and current client candidates pass isolated transport checks. These successes do not override the blockers below. Latest test/runtime counts are in the existing phase reports.

1. The reproduced arbitrary-ID context path and model self-approval are contained. Service-level concurrent decisions now use an atomic pending claim; stale approval/expiry cannot overwrite another decision, and interrupted outcomes are reported unverified without rerun. Independently authenticated owner approval, exact principal/payload binding, single-use external consumption and complete domain coverage remain release gates; an atomic decision claim does not clear them.
2. The STDIO gateway now enforces explicit canonical risk for571 tools; unknown tools and all23 FINAL operations fail closed. Context execution raises caller risk to canonical and selected-provider policy. Individual domain semantics, direct internal dispatch and complete provider metadata coverage still require audit; this is not universal proof across every possible Python entrypoint.
3. The obsolete Docker application/REST contract is repaired. A minimal Python3.11 image passes real MCP discovery/read/write/restart/replay and controlled workflow recovery. Installed-MCP online snapshot/offline restore is also now verified with disposable state/network disabled. Owner database recovery, live graph/providers, cross-file projection consistency and production deployment remain unverified; see the runbook and Phase3.
4. Full collected suite was attempted and did not finish after local disk exhaustion. Root `ruff check .` now has zero findings after nine inspected skill-script cleanups; no ignores/exclusions were added. Final relevant178 tests and separate2 trust-outcome cases pass. No full-suite pass total is claimed.
5. Local graph/workflow/backup recovery now has controlled SQLite/process/MCP, real isolated Neo4j and real CPU FAISS snapshot/replay evidence. Local POSIX/trusted-filesystem, cooperating updated worker and offline-operator boundaries still apply. Mixed runtimes, NFS/multi-host, domain outcome verification, ambiguous external delivery, full owner graph reconciliation, owner backup/restore and all provider degraded modes remain open. Cancellation/deadlines are cooperative and do not terminate an in-flight effect.
6. Installed SDK advertises through2025-11-25. A is selected in nine installed entries/eight host profiles; latest isolated SDK probes pass9/9. The active Codex session now executes real MCP safe reads; native Claude health passed with isolated configuration. OpenCode2.x schema/disabled semantics are corrected with backups, but isolated native list still says No MCP servers configured (cause UNKNOWN). Other GUI parity, owner-state mutation/recovery and2026-07-28 conformance remain unverified.
7. Fifty curated golden task outcomes, labeled retrieval metrics and live citation validity targets are unmeasured.

Source links, executed commands, counts, before/after failures and rollback: [Phase 0](../implementation/PHASE_0_REPORT.md), [Phase 1](../implementation/PHASE_1_REPORT.md), [Phase 2/G1](../implementation/PHASE_2_REPORT.md), [risk register](../audits/SECURITY_RISK_REGISTER.md), [known limits](KNOWN_LIMITATIONS.md).

No production service was deployed, and no intentional owner-data mutation/migration or host-instruction replacement was performed. Historical active MCP reads can emit application telemetry under existing configuration; no byte-for-byte owner-store immutability claim is inferred from a successful read. Current tests/container/client probes use disposable state. No claim of zero possible policy bypass, production safety, scientific learning benefit or complete master-roadmap execution is made.

The supervisor's `release-check` now executes the shared validators rather than hardcoding successful redaction, SSRF, transport and SDK checks. Its PASS remains a bounded structural/guard result, not this production readiness decision. Thirteen new regressions reproduce the prior defect; the related43-test regression passes after correction. Current selected781-test evidence precedes this additional batch; overlapping runs are not added into a fabricated whole-suite count.

Historical bounded batches: approval/domain/adapter/CLI regression125 passed; approval/client tests21 passed. Those image results describe their recorded artifacts; the current November15 final image is separately rebuilt and verified above. The earlier23 root lint findings are resolved; root Ruff is zero. No full-suite, all-host native success or exactly-once external approval claim follows.
