# Baseline and candidate verification

## Latest vector/lifecycle/validator checkpoint, 2026-11-15

`VERIFIED_TEST`: final combined graph, embedding-dimension, MCP lifespan,
validator/gateway/action-policy, deployment and current documentation-risk
selection: **178 passed in192.49s**, no failed/skipped/warnings reported.
The repaired trusted-provider outcome fixture plus explicit unverified-provider
denial: **2 passed in24.34s**. The positive fixture now declares reviewed
read-only capability metadata; the new negative test fails if the unverified
handler executes. Runtime policy is unchanged. Earlier61/42/72 selections
overlap the178 cases and must not be added into a full-suite count.

```bash
.venv/bin/python -m pytest tests/os/graph tests/os/knowledge/test_embedding_dimensions.py tests/interfaces/test_graph_lifespan.py tests/interfaces/test_skill_validation_policy.py tests/interfaces/test_execution_boundary.py tests/interfaces/test_mcp_tool_adapter.py tests/tools/test_execution_policy.py tests/os/policy/test_action_policy.py tests/architecture/test_container_deployment.py tests/docs/test_docs_tool_count.py::test_audit_risk_matches_docs -q
.venv/bin/python -m pytest tests/evaluation/test_integration.py::test_invocation_outcome_mapping_pipeline tests/evaluation/test_integration.py::test_unverified_invocation_outcome_is_incomplete -q
.venv/bin/ruff check .
```

`VERIFIED_RUNTIME`: root Ruff23→0, nine edited skill scripts parse without
execution. Source and frozen installed MCP worker smokes pass for hash vectors
and cached offline MiniLM, with663-file installed parity. The minimal image
`xninetzy:validator-fix-20261115` passes general local read/write/restart/denial
and the separate default-approval validator smoke. Exact structured results
are retained in CLIENT_CONNECTION_RESULTS.json; Phase1/3 record artifact ID.

The full suite collected2888 cases before subsequent validator/negative tests
were added. Its execution did not finish after disk exhaustion; only1085
progress characters and a truncated failure traceback survive. This is not a
verified total pass count. Three recorded failures were risk-document drift,
unreviewed-provider success expectation and real Remotion rendering. The first
two are now covered by focused passing checks; rendering still needs enough
disk and reproduction. The earlier focused docs/evaluation run (25 passed/
2 failed) preceded those fixes. No skip/xfail was added to hide failures.

## Projection lease and real backend continuation — 2026-11-15

Final missing-store check reproduced1 failure in0.72s: projection tick created an empty SQLite file before its query failed. It now refuses missing canonical state before opening a connection. The final225-case run/rebuilt artifact includes this case; the earlier224/50.23s and44 focused selections precede it and are not summed.

Initial12 new regressions failed/19 passed in33.68s, reproducing pre-claim snapshots, stale finish/failure, dispatch after takeover, poison success, missing canonical edge weight/properties, deleted endpoint recreation, newer-version markers and private worker error logging. Additional9 backend query/auth/connectivity privacy cases failed in0.18s before type-only logging. Final focused worker/privacy selection passes44 in17.09s; final integrated graph/backup/workflow/DB/MCP-boundary/deployment/installed/internal-approval selection passes **225 in53.01s**, with no reported failure/skip/xfail/warning. Earlier58 graph cases in132.41s preceded the backend privacy correction. Counts overlap; no full-suite or throughput improvement is inferred.

Actual source and fresh frozen non-editable graph-only installed profile pass live Neo4j5.26 edge weight/properties, duplicate resync, backend stop, retained failed event/canonical SQLite+FTS, backend restart/retry and node/relationship deletion. Host Python3.14.5/driver6.2.0;663-file parity. FAISS is explicitly stubbed only in this live harness and reported NOT_TESTED. Two early harness attempts could not publish an internal-bridge port on this host and cleaned up; final script reaches only its exact owned private container address with no host port. Expected outage stderr is type-only ServiceUnavailable plus fixed safe ACK failure. No owner mount/auth/config or graph is used.

Final minimal Python3.11 image `xninetzy:graph-hardening-20261115` (`sha256:ecbc8096b2fd9ec3f35cc0531fbdbc201b9742cf8b2e575165848e02e6bda3fb`) verifies663 files and independently passes installed-MCP backup/restore, workflow and general571-tool restart/replay/denial smoke without optional services. CI adds a separate graph-only installed/live fixture job; remote Actions/Python3.11 enhanced execution remain unexecuted. Commands, resource/image identity, limitations and rollback: [Phase3](../implementation/PHASE_3_REPORT.md), [runbook](../release/OPERATIONS_RUNBOOK.md), `graph_projection_continuation` in CLIENT_CONNECTION_RESULTS.json.

## Backup/restore continuation — 2026-11-15

Initial selection reproduced17 failures/4 passes in1.06s: manifest/schema/SQLite validation, size checks, metadata-directed retention, unsafe journal acceptance, absent safety snapshot, symlink and unlisted/stale vector behavior. A separate HEAD-service runtime reproduction actually deletes a synthetic unrelated directory via forged manifest `path`, entirely inside a temporary directory. Further deterministic regressions reproduce same-second retention (1), offline WAL safety-capture sidecars (1, also found by the actual MCP drill), and ignored snapshot journals (3). Current36 backup cases pass within the final relevant selection: **116 passed in18.89s**, no reported failures/skips/xfails/warnings. Earlier21/31/112/113 runs overlap and are not summed.

Final image `xninetzy:backup-hardening-20261115`, ID `sha256:757420e8fd6108b50e948212eacd736600e9f41622427983af15dcba8426f38c`, verifies663 runtime files. Actual installed MCP from `/tmp` creates a local task, snapshots its live WAL database, changes state, closes all fixture sessions, restores offline with a verified safety snapshot, restarts and verifies saved task/local idempotent replay. Previous installed-workflow and general STDIO read/write/restart/denial smokes also pass on this image; all stderr empty, network disabled, no owner mounts. The first source smoke held safely due to self-created WAL sidecars; that failure was reproduced/corrected rather than suppressed. No live graph/FAISS/portal or owner recovery is inferred. Commands/rollback are in [Phase3](../implementation/PHASE_3_REPORT.md); machine evidence is under `backup_restore_continuation` in CLIENT_CONNECTION_RESULTS.json. CI includes the new cases/drill; remote CI not executed.

## Durable local workflow continuation — 2026-11-15

Docs validation found that CI's `yarn check` selected Yarn Classic's built-in dependency check, hiding the declared `astro check`. Replaced it with `yarn run check`; the actual checker reproduced one undefined dataset index error/two unused bindings in PageFeedback. The guarded-key/unused-binding correction now yields 0 errors/warnings/hints over 16 files (4.99s). `yarn run build` succeeds, 34 pages (2.22s command duration). This is checker/build evidence, not browser interaction or a speed comparison. No lockfile/dependency change; generated search-index churn restored to pre-build bytes. The initial unrelated built-in scan was interrupted deliberately, not counted as a passing Astro check.

`VERIFIED_TEST`: five initial recovery regressions failed before implementation. Further red cases reproduced cancellation races (2), dropped independent successful evidence (1), a valid1-second deadline (1), mutated owner/goal context (3), failed-run cancellation (1) and private handler errors (2). Current59 workflow cases include actual fixture-process SIGKILL during a read after a completed write and during an uncertain write; real SQLite state/rollback triggers, concurrent execution, typed/legacy/corrupt checkpoints, symlink refusal, budget/policy/cancellation and privacy checks. No real external mutation or owner process is used. A first unbounded concurrency fixture was interrupted and bounded; a fractional timeout fixture was invalid for the existing integer setting and corrected. Neither command issue is hidden as a skip or counted as a product defect.

Combined selection **211 passed in242.59s** (workflow/MCP/HITL/policy/privacy/packaging/graph). This preceded the last privacy fix; all affected workflow/core-privacy/MCP-boundary tests then passed **123 in18.14s**, including all59 workflow cases. Counts overlap, are not summed, and do not represent full-suite execution. Final commands and exact files are in [Phase3](../implementation/PHASE_3_REPORT.md). No final failures/skips/xfails/warnings reported. Canonical Ruff, strict571-tool inventory, prompt hashes and diff whitespace pass.

`VERIFIED_RUNTIME`: final Python3.11 image `xninetzy:workflow-recovery-20261115` is separately rebuilt after the privacy fix. Installed runtime parity passes663 files. From outside checkout, actual MCP resumes the same failed fixture plan using canonical reads/synthesis; completed-write ledger remains unchanged, completed output replays, and uncertain mutation is held. Exactly2 synthetic effects/2 intended workflows remain. The general container smoke separately passes read/write/restart/replay/denial; nine fresh SDK source probes pass without host changes. See structured results in `docs/evaluation/CLIENT_CONNECTION_RESULTS.json`. This does not verify live providers, owner host activation, positive authenticated approval or external exactly-once delivery. CI adds installed-MCP recovery; remote Actions remains unexecuted.

## Internal/domain and packaging continuation — 2026-11-14

From the previous836/98 checkpoint:5 initial internal approval regressions failed;6 notification/message regressions failed;3 direct HEBAT cases and1 failed-token case reached synthetic upload/removal before correction. After implementation, the command recorded at the top of Phase1 passes **361 tests in225.86s** across HITL/policy/academic/notifications/MCP/privacy/workflow/graph. Separate packaging/deployment selection passes **12 in0.29s**. No final failure/skip/xfail/warning reported. Earlier32/151/29 runs overlap and are not summed with these or the historical836/98 runs. Positive effect/race/rollback tests are preserved as private transition-kernel tests; public authentication is independently tested as denied. QA/KRS fixtures use real legacy-record validation and zero-effect assertions. No live institutional mutation occurs.

Container build initially succeeded but installed-wheel approval checks from `/tmp` failed. File hashes confirmed current copied source/stale installed module. The corrected Dockerfile forces own-project reinstall and checks runtime file parity before accepting the image. The first parity build flagged the manifest-excluded empty `os/mcp_external/tests/__init__.py`; a source-only exclusion aligned with the existing manifest was regression-tested while unexpected installed files still fail. Final build and runtime check pass663 Python/JSON/SQL files. Installed-package raw approval/legacy status checks then pass; MCP smoke passes571 tools, read, synthetic local write, denial/mismatch, restart and replay. Exact image and structured evidence are in CLIENT_CONNECTION_RESULTS.json. CI configuration is updated; remote Actions execution remains unverified.

## Phase1 boundary continuation — 2026-11-14

Final expanded selection below: **836 passed in646.51s**, no failures/skips/xfails/warnings reported. Subsequent scoped privacy/performance/hook corrections were verified by **98 passed in24.56s** in `tests/core/test_output_sanitization.py tests/core/test_secret_redaction.py tests/core/test_identity_redaction.py tests/interfaces/test_execution_boundary.py tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py tests/interfaces/test_mcp_server.py tests/os/lightning/test_input_redaction.py`. These are overlapping selections, not934 distinct tests, and the full repository suite was not run. Redaction's40041-character subprocess fixture failed its2s budget before and passes after;2000 seeded compatibility comparisons pass. Two new auto-hook regressions failed before and now verify read/replay mutation boundaries. The final image is rebuilt after these changes and runtime-smoked separately.

The canonical isolated selection is reproduced below. `tests/conftest.py` now installs temporary writable paths before collection, disables deployment `.env` loading in the parent test process and optional auto/services; MCP subprocess fixtures explicitly forward this environment and use the current interpreter. No production/portal mutation, model download or owner service rollout is part of these checks.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q --durations=10 \
  tests/tools tests/cli tests/db tests/policy tests/invocation tests/orchestrator \
  tests/workflow tests/os/hitl tests/os/graph tests/os/knowledge tests/os/memory \
  tests/os/lightning tests/architecture tests/governance tests/core \
  tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py \
  tests/interfaces/test_execution_boundary.py tests/interfaces/test_transport_authority.py \
  tests/interfaces/test_mcp_runtime.py tests/interfaces/test_mcp_server.py \
  tests/media/video/test_storage_roundtrip.py tests/os/skills tests/reasoning \
  tests/test_routing*.py tests/learning tests/evaluation/test_replay_poison.py
```

Earlier expanded result: **5 failed /828 passed in545.18s**. Failures were one stale inventory-provenance expectation, one real missing declared-return validator, one SDK subprocess missing fixture environment (wrong-store guard refused startup), one synthetic write fixture retaining default approval mode, and one mock external provider missing trusted read-only metadata. They were corrected without hiding cases. Wire/audit retest: **10 passed in16.43s**. Latest combined acceptance subset: **64 passed in182.53s**. Subsequent optional hook error-trace regressions reproduced three leaks, then all boundary cases passed: **28 passed in53.78s**. Counts overlap; they are not added into a fabricated full-suite result. Final expanded outcome is recorded in the final verification section of Phase1.

`tests/governance/test_no_comments.py` contained two preexisting xfails tied to an absent historical policy. It was retired and replaced with two tested authority invariants; no current functional test was skipped/xfail-ed to improve a score. Controlled provider metadata updates preserve successful invocation/replay/audit assertions. A prior command attempted an invalid wire payload for the HEBAT denial fixture; the valid synthetic payload is now schema-correct and cannot reach its external handler.

Other current checks: strict non-executing inventory passes571 tools (133 READ/6 DRAFT/409 WRITE/23 FINAL); canonical `ruff check xninetzy tests scripts` passes; `git diff --check` passes; prompt manifest hashes pass; actual supervisor validators pass6/6. Root `ruff check .` reports23 additional skill/vendor findings outside canonical CI scope, with no new ignores. Candidate prompt remains1861 cl100k_base tokens. Current image and9-client SDK results are preserved in CLIENT_CONNECTION_RESULTS.json. These are bounded contract/runtime checks, not a whole-repository/full-live or production-readiness claim.

Date: 2026-11-10. Existing environment: Python 3.14.5, pytest 9.1.1, MCP 1.30.0, Pydantic 2.13.4, LangChain Core 1.6.3. Repository HEAD at start: `2d0f13f`. Hardware/configuration: [performance baseline](../evaluation/PERFORMANCE_BASELINE.md).

## Isolation and reproducibility

Tests were executed in-process after setting `MCP_RUNTIME_MODE=container`, pointing SQLite/data/output/vault/index paths at fresh `/tmp/xn-*` directories, disabling automatic memory/graph/improvement and optional services, and setting `Settings.model_config['env_file']=None` before clearing the settings cache. This prevents deployment `.env` settings from controlling test paths. Root-layout tests pass explicit fixture mappings; secret tests contain synthetic sentinels only. The existing `.venv` was not reinstalled.

Representative in-process invocation (set all writable paths for tests that exercise those paths):

```python
import os, tempfile
from pathlib import Path
root = Path(tempfile.mkdtemp(prefix="xn-check-"))
os.environ.update(MCP_RUNTIME_MODE="container", SQLITE_PATH=str(root / "tests.sqlite3"),
                  DATA_DIR=str(root), AUTO_MEMORY_ENABLED="false",
                  AUTO_GRAPH_ENABLED="false", AUTO_IMPROVE_ENABLED="false")
from xninetzy.core.config import Settings, get_settings
Settings.model_config["env_file"] = None
get_settings.cache_clear()
import pytest
raise SystemExit(pytest.main(["-q", "tests/db/test_idempotency_store.py"]))
```

## Executed checks

| Check | Before | Candidate / interpretation |
|---|---|---|
| Initial selected suite: tools, idempotency, policy, MCP mapping/adapter, skill frontmatter | 146 passed, 1 xfailed in 22.63s | Xfail masked two invalid legacy names, not damaged YAML |
| Idempotency new concurrency/interruption regressions | 2 failed | 9 total idempotency tests passed after fix |
| Runtime root regression | 4 failed, 5 passed | 17 passed after root correction and ambiguity guard |
| Synthetic Lightning credential tests | 14 failed, 1 passed | 39 combined Lightning/core-redaction tests passed |
| Audit tooling regression | 6 failed | 25 audit/manifest/registry tests passed |
| Canonical prompt integrity entrypoint | Failed: validator missing | 10 prompt contract tests added, including unsafe edits, missing files, traversal, symlink, hash drift and read-only installed comparison |
| Skill governance/health | Broad xfail attribution | 14 passed, 0 xfail; 2 historical rejected mirrors explicitly identified |
| Combined candidate suite A | NOT_MEASURED as identical pre-change suite | 222 passed in 19.65s; see selection below |
| Broader suite B | NOT_MEASURED as identical pre-change suite | 124 passed in 62.65s; see selection below |
| Full collection at intermediate candidate snapshot | Historical collection failures not assumed current | 2538 tests collected, exit 0, 10.06s; collection is not execution |
| Full repository Ruff | No claimed clean baseline | 125 findings outside the focused passing change set; no mass formatting/fix applied |
| STDIO smoke | NOT_MEASURED before | Actual initialize/list and ten safe read calls succeeded |
| Minimal base wheel | Frozen install: 49 packages | Initial startup failed `ModuleNotFoundError: langchain_core`; follow-up recorded in implementation report |

Suite A: `tests/tools tests/db tests/policy tests/interfaces/test_mcp_runtime.py tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py tests/governance/test_skill_frontmatter.py tests/governance/test_prompt_contract.py tests/os/skills/test_skills.py tests/os/lightning/test_input_redaction.py tests/os/lightning/test_lightning_rl.py tests/core/test_secret_redaction.py`.

Suite B: `tests/invocation tests/orchestrator tests/workflow tests/os/policy tests/os/hitl tests/security tests/os/knowledge/test_evaluation.py tests/os/knowledge/test_retrieval.py tests/os/memory tests/architecture tests/cli`.

These selections are disjoint: 346 executed candidate tests at that checkpoint, not 346 end-to-end user scenarios. Later additions and final combined results are recorded in the phase report. No failures were skipped to obtain those results. Existing tests can still encode weak guarantees (for example approval presence); passing them does not prove secure approval consumption.

One attempted combined command referenced nonexistent `test_rl.py` / `test_security_redaction.py`; pytest exited 4 with no tests run. Paths were corrected to the existing files above and the actual successful run is reported. This command error is not a product failure.

## Remaining verification

## Final regression checkpoint

After the additional workflow/projection changes, the final combined run yielded **476 passed, 1 warning in 162.36s**, with no failed/skipped/xfail reported. It includes suite A and B plus `tests/reasoning/test_reasoning_depth.py`, `tests/core/test_llm_providers.py`, `tests/core/test_flaz_llm.py`, `tests/os/graph`, `tests/ecosystem/test_vision_tools.py`, `tests/data_analysis/test_profiling.py` and `tests/data_analysis/test_table_artifact.py`. All checks ran with the temporary-state isolation described above.

The warning is `FutureWarning` in `knowledge/embeddings.py:106`: `get_sentence_embedding_dimension` renamed to `get_embedding_dimension`. It was reported, not suppressed. This result supersedes earlier candidate execution totals; do not add overlapping runs. It remains a selected regression suite, not the entire collected repository suite or 476 end-to-end user tasks.

Final focused Ruff on every changed Python file passes; `git diff --check`, shell syntax, CI YAML parsing and relative documentation links pass. Full repository Ruff still reports **125 findings**. The exact CI minimal-wheel smoke body was executed locally with the isolated installed interpreter from `/tmp`: **571 tools; safe read passed**. Remote CI execution is not verified.

## Outstanding verification

Full execution of all collected tests, clean Python 3.11 installation, container build, backup/restore, advisory scan, real network/provider failure tests, academic portal actions, native Codex/Claude/OpenCode parity, and 50 curated outcome tasks were not completed. No historic 811/29 or 828/29 result is reused as today's baseline. Release readiness remains NOT_READY.

## Continuation regression from `74ff58b`

Current expanded offline-model regression: **781 passed in283.29s**, no failures/skips/xfails/warnings reported. Settings `.env` loading was disabled in the parent test process; all mutable paths were temporary, auto hooks/Neo4j disabled and `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. The selection includes tools/db/policy/invocation/orchestrator/workflow/HITL, knowledge/memory/graph, architecture/CLI, client config, prompt/skill contracts, provider factories, vision/spreadsheet, video, Lightning and every `tests/test_routing*.py`, plus registry extraction/capability registry. It is still not the whole repository or781 end-to-end user tasks.

The first expanded run yielded744 passed/2 failed; performance-group taxonomy and historical33-group count caused both. Three focused red assertions confirmed the missing mapping; a corrected routing/registry/client selection then passed139 tests. The final781 result supersedes those runs; do not add overlapping counts. A supplemental latest helper run passed9 tests after permission-preservation and snapshot consistency refinements. A command using nonexistent routing registry test filenames exited4 with no tests run; it was corrected to existing registry-extractor/capability files and is not counted as product validation.

Full canonical Ruff now passes: `.venv/bin/ruff check xninetzy tests scripts`, **125→0 findings**, no config/ignore weakening. Shell/diff whitespace and CI YAML checks pass. Native Claude reports Connected under temporary paths; native Codex accepts candidate configuration through `mcp get --json`; nine candidate SDK transports each initialize/list571 tools/read datetime. Host GUI sessions, owner database rollout and unsupported ArkCLI/standalone Copilot are explicitly not inferred. Container verification is recorded separately after the actual image/runtime checks.

## 2026-11-11 runtime and diagnostic continuation

Actual minimal Python3.11 image build and two-session MCP restart smoke succeed:571 tools, safe read, synthetic local write, persisted task after restart and one-record idempotent replay. Network disabled; no owner state mounted. The final image also executes all six bounded release validators successfully with actual MCP1.30.0. Exact commands, digest, limitations and rollback: [Phase 3](../implementation/PHASE_3_REPORT.md).

The supervisor's previous hardcoded diagnostic results were reproduced by13 failing regressions and corrected to shared validators. Focused red/green command: `.venv/bin/python -m pytest tests/cli/test_supervisor.py -q -k 'actual_validator or validator_exception'`. Related isolated selection `tests/cli tests/tools/test_release_check.py tests/tools/test_mcp_audit.py tests/architecture/test_container_deployment.py tests/tools/test_client_connection_config.py`: **43 passed in12.51s**. The earlier781-test run predates this extra diagnostic batch; these overlapping counts are not summed. No test was skipped/xfail-ed to obtain the new result. Full Ruff remains zero; canonical prompt hashes pass; no host prompt rollout occurred.

After owner selection A, nine configuration files were installed and post-install `--smoke` initially failed before invocation because quoted TOML headers were not recognized on replan. Three regression cases reproduce this failure; all12 connection tests pass after parsing equivalent table paths. `.venv/bin/python -m pytest tests/tools/test_client_connection_config.py tests/cli/test_supervisor.py tests/interfaces/test_mcp_runtime.py -q`: **49 passed in12.95s**. This run overlaps previous selections and is not added to781/43. All9 post-install transport probes pass with temporary mutable paths; native Codex parses installed A configuration; replan reports no changes. Both owner database file hashes and global instruction hashes remain unchanged. Backups/receipt are private, outside Git. Actual native GUI reload and owner-state MCP startup remain unverified.

## November14 continuation

Approval race/outcome regressions first returned4 failed/1 passed, then5 passed after a conditional pending claim and truthful interrupted-outcome response. Related isolated selection `tests/os/hitl tests/os/policy tests/policy tests/orchestrator tests/db/test_idempotency_store.py tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py tests/cli/test_supervisor.py`: **125 passed in203.02s**. Identity and effects are controlled; SQLite is real temporary storage. No live portal/submission or real process-crash proof is claimed.

OpenCode2.x migration and disabled-flag tests failed before corrections; all16 client cases pass. Current `.venv/bin/python -m pytest tests/os/hitl/test_approval_concurrency.py tests/tools/test_client_connection_config.py -q`: **21 passed in2.46s**. Full Ruff and diff checks pass. Latest SDK smoke passes9/9; active Codex session performs real Xninetzy datetime and skill discovery/body reads. Native Claude isolated health passed, but native isolated OpenCode list returns No MCP servers configured despite its own add writing the documented nested shape. That native attempt is NOT_VERIFIED, not counted as a pass from exit0. Namespace sandbox attempts failed on system permissions; no sandbox guarantee. These counts overlap prior selections and are not summed.
