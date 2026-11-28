# Phase 2 / G1: canonical instruction and discovery foundation

## Owner-approved global installation, 2026-11-16

Status: **VERIFIED installed prompt bundle v2.3.0**. The owner explicitly
approved the reviewed candidate with “iya pasang”. This authorizes the native
instruction-file rollout only; no MCP consequential-action approval was created.
The broader system release remains PARTIAL / NOT_READY.

Preflight confirmed the installed six shared/client files still matched the
reviewed v2.2 baseline and none contained extra local changes. The approved nine
source hashes matched CONTEXT_COST_RESULTS.json. Five targets changed:

- `~/.xninetzy/CORE_PROMPT.md`
- `~/.xninetzy/CLI_SHARED_INSTRUCTIONS.md`
- `~/.xninetzy/references/artifacts-and-design.md` (new)
- `~/.xninetzy/references/reverse-engineering.md` (new)
- `~/.xninetzy/references/product-videos.md` (new)

`CORE_RULES.md`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md` and
`~/.config/opencode/instructions/xninetzy-paksa.md` already matched and were not
rewritten. L1 and adapter components retain their2.2 versions inside bundle2.3.
Model settings, permissions, MCP configuration, owner databases/credentials and
running agent processes were not changed by installation.

The private fixed-destination installer takes a cooperative local lock, refuses
symlinks/unreviewed local changes, backs up existing files and the approved source,
preserves file modes and records intent before each atomic replacement. Domain
references publish first, shared guidance next and L0 last. Rollback follows the
reverse dependency order. These are per-file atomic replacements, not a filesystem
transaction across all nine paths or an arbitrary concurrent-writer guarantee.

Backup: `~/.xninetzy/backups/prompt-v2.3.0-20261115T191727Z-5753e6f8/`.
The UTC timestamp corresponds to November16 WIB. Directory mode0700; saved files,
installer and receipt0600. `receipt.json` records original/installed hashes,
publication order and native owner authorization. It is not an MCP approval token.
The backup contains the original six files plus the approved source bundle.

`VERIFIED_TEST/RUNTIME`: five isolated fixture groups pass installation/repeat/
explicit rollback, custom-file refusal, post-replacement failure recovery for a
reference and shared file, and symlink refusal. The owner installation reports
five changes/nine verified files. An immediate repeat reports zero changes.
Installed comparison exits0 with **9/9 matches**, backup hashes/modes verify, and
the11 prompt-governance tests pass in1.58s. No full162-case rerun was needed:
runtime code and the nine approved instruction payloads were unchanged.

Installed referenced compositions independently measure2109 Codex,2213 Claude,
2111 OpenCode cl100k_base tokens. Host model usage, billed tokens and live native
cross-client behavior remain unmeasured. Existing client adapters reference the
same shared location; open a new session or reload instructions for conversations
that cached the old prompt. Active MCP schema caches also need their normal reload
for the previously implemented optional compact-discovery arguments. No process
was force-restarted and no job was interrupted.

Verification: `python scripts/validate_prompt_contract.py --installed`;
`python -m pytest tests/governance/test_prompt_contract.py -q`.
The default read-only `scripts/verify_prompt_injection.sh` also now checks installed
state. An actual rollback was tested only against disposable fixture homes.
Preview or deliberately apply owner-requested recovery with the archived helper:

```bash
prompt_backup=/home/misbahul45/.xninetzy/backups/prompt-v2.3.0-20261115T191727Z-5753e6f8
/home/misbahul45/code/xninetzy/.venv/bin/python "$prompt_backup/installer.py" --rollback "$prompt_backup/receipt.json"
# Only when an owner actually requests rollback:
/home/misbahul45/code/xninetzy/.venv/bin/python "$prompt_backup/installer.py" --rollback "$prompt_backup/receipt.json" --apply
```

Rollback verifies installed hashes and refuses later local modifications. It
restores original bytes/modes and removes only unchanged new reference files;
it never prunes owner data or unrelated configurations. Repository changes in
this installation stage are deployment annotations/evidence in the manifest,
this report, architecture/audit/release/runbook documents and
CONTEXT_COST_RESULTS.json. No new runtime feature, migration or provider is added.

## Token-efficiency preparation, 2026-11-16 (pre-install evidence)

Preparation status at that checkpoint: repository implementation verified;
global installation had not yet been authorized. The approved rollout above
supersedes pending-installation statements in this historical section.
The owner already supplied/installed v2.2 and split several large skills before
this continuation. That work is retained. Concurrent Kaggle/config edits and
untracked consulting resources are outside this batch and were not overwritten.

`VERIFIED_CODE`: repeated integration detail moves from the hot shared prompt to
three hash-pinned conditional references. Before that domain's work the shared
entrypoint explicitly requires the applicable reference; missing guidance holds
dependent actions. Original deck brief/Canva/FigCraft, REA dynamic-action and
XN-Motion exact-storyboard approval boundaries are retained. CORE_RULES.md and
host-installed prompts are unchanged. The canonical candidate is v2.3.0; old
v2.2 validation remains supported. A regression prevents removing a referenced
domain policy from the manifest even when other hashes are updated.

`context-engineering` keeps its original metadata and preserves its entire prior
body verbatim in `references/context-contract.md` (SHA verified). Its smaller
entrypoint selects resources instead of loading all procedures. The existing
native Codex skill symlink points to this repository, so the next native skill
read sees the changed entrypoint; no separate global skill copy was rewritten.

Existing `tool_catalog` and `skill_list` gain optional `query`, `offset` and
`compact` arguments; skill_list also accepts a limit. Default output/signatures
remain backward compatible through optional defaults; full public MCP enumeration
is retained. Compact tool rows preserve risk, approval and idempotency fields.
Filtering does not grant permission. No new tools, database or runtime dependency
is added. The skill-context helper now honors its existing max-character setting,
retaining its trust guard or omitting metadata that cannot fit. This is a character
contract in that helper, not a universal host token-budget guarantee.

`VERIFIED_RUNTIME`, cl100k_base serialized-text measurements:

| Comparable view | Before | After | Reduction |
|---|---:|---:|---:|
| Codex referenced hot composition |2653|2109|20.51%|
| Claude referenced hot composition |2757|2213|19.73%|
| OpenCode referenced hot composition |2655|2111|20.49%|
| Selected context-engineering body |1555|584|62.44%|
| Same250 tool metadata rows, full vs compact |19426|10124|47.88%|
| Same120 skill metadata rows, full vs compact |6863|6515|5.07%|

Filtered discovery additionally returns five memory-tool rows in195 tokens and
up to two context-skill rows in124 tokens. These deliberately contain less data;
their savings must not be described as compression of the entire catalog.
Conditional prompt references add730 tokens only when all three domains are
needed. Registry schema text actually grows103450→103599 tokens (+149) because
optional arguments need documentation. No tools/list/startup/billing saving is
claimed. Actual model behavior, native-host parity and latency deltas are unmeasured.

Verification: initial regressions7 failed/4 passed; final expanded selection
**162 passed in24.02s**, including routing, prompt/skill contracts, budget,
adapter/approval and minimal-import coverage. Earlier84 passes overlap this run.
Root Ruff and diff checks pass; the native skill creator's quick validator passes.
Actual STDIO SDK checks from source and a fresh frozen base-only non-editable
installation pass compact pagination, legacy output, selected skill/reference
loading and consequential-action denial. The smoke copies one reviewed skill
fixture; it does not prove a complete wheel-bundled skill catalog.

Whole-package parity was checked and failed for concurrent core/Kaggle changes
outside this batch. All three changed runtime files match the installed wheel;
the bounded installed smoke still passes. No full-package/release parity claim
is inferred. No owner store, credential, account, host prompt/configuration or
native agent process was changed by these test fixtures.

Files: `docs/prompt-injection-core/{CORE_PROMPT,CLI_SHARED_INSTRUCTIONS}.md`,
`manifest.json`, `references/{artifacts-and-design,reverse-engineering,product-videos}.md`;
`.agents/skills/context-engineering/{SKILL.md,references/context-contract.md}`;
`xninetzy/skills/{tools,prompting}.py`, `xninetzy/tools/ecosystem/tool_catalog_tools.py`;
`scripts/{validate_prompt_contract,measure_context_cost,smoke_context_discovery}.py`;
`tests/{governance/test_prompt_contract,tools/test_compact_discovery,skills/test_context_budget}.py`;
CI and these architecture/evaluation reports. No migration is required.

Exact reporting/CI files: `.github/workflows/quality-gates.yml`,
`docs/evaluation/{GLOBAL_AGENTIC_BASELINE.md,CONTEXT_COST_RESULTS.json}`,
`docs/architecture/{GLOBAL_PROMPT_ARCHITECTURE.md,TOOL_GOVERNANCE.md}`,
`docs/audits/{PROMPT_CONFLICT_REPORT.md,SKILL_VALIDATION_REPORT.md}`,
`docs/implementation/{PHASE_0_REPORT.md,PHASE_2_REPORT.md}` and
`docs/release/{RELEASE_READINESS.md,KNOWN_LIMITATIONS.md}`.
Tools used: code graph/coverage, local Python/uv/pytest/Ruff, Context7 official
MCP documentation, canonical skill discovery and isolated SDK STDIO. Skills:
context-engineering, optimize-prompt and the system skill-creator. The prompt
optimizer explicitly requires owner-approved application; this checkpoint
prepares the concrete bundle without pretending host installation occurred.
Sources: current code, measured files/hashes and the official MCP architecture
reference in CONTEXT_COST_RESULTS.json. No publication, account mutation or
production deployment was performed. The task-created temporary wheel environment
was removed after completed verification; owner files/caches were not pruned.

Reproduce: `python scripts/measure_context_cost.py`; `python scripts/smoke_context_discovery.py`;
`python scripts/validate_prompt_contract.py`; the tests/commands and raw before/after
data are in [CONTEXT_COST_RESULTS.json](../evaluation/CONTEXT_COST_RESULTS.json).
`--installed` is deliberately nonzero until the reviewed v2.3 bundle is installed;
it never writes host files. The prompt optimizer skill requires approved rollout;
no approval was invented or delegated to a tool description.

Rollback: restore only this batch's reviewed runtime/test/skill/prompt hunks and
manifest together; retain the full context reference until readers are coordinated.
No user data rollback is needed. Existing calls without optional discovery flags
remain compatible. Before host installation review all nine manifest files,
back up owner copies, obtain explicit owner approval, apply atomically and verify;
then reconnect MCP clients for their cached schemas. Do not replace unrelated
host additions. Overall release readiness remains separate and NOT_READY.

Date: 2026-11-10. Status: **PARTIAL phase; repository candidate verified, host rollout not performed**.

## Result and evidence

Corrected repository L0/L1/L2 authority language, separated valid workflow customization from authorization bypass, removed unconditional reasoning-tool loops from the candidate, used capability-aware native/domain tool selection, made L3/L4 dynamic, and added a canonical continuity source. Installed host instructions and active developer requirements remain unchanged. The candidate describes independently enforced policies; it does not implement authorization.

| Finding | Before | Candidate / evidence |
|---|---|---|
| Local Markdown authority | Claims it overrides vendor/host defaults | Explicit host/developer constraints; VERIFIED_CODE |
| Skip-validation override | No explicit protected-boundary exclusion | Workflow customization cannot bypass auth/approval/critical checks; VERIFIED_CODE |
| Repeated reasoning/catalog instructions | Fixed FIRST/LAST calls and unconditional workflow/context | Adaptive task guidance and progressive loading, subordinate to active host rules; VERIFIED_CODE |
| Prompt integrity | Heading/line checks protect old design | SHA-256 manifest, required references, known-conflict negative tests and unsafe-path checks; VERIFIED_TEST |
| Host files | Existing owner copies with additions | Read-only drift comparison; no overwrite; VERIFIED_TEST |
| Codex referenced composition | 5268 cl100k tokens installed | 1861 candidate, -3407 (-64.7% text only); VERIFIED_RUNTIME |

## Files changed

Canonical sources: `docs/prompt-injection-core/CORE_PROMPT.md`, `CORE_RULES.md`, `CLI_SHARED_INSTRUCTIONS.md`, `cli-overrides/codex-AGENTS.md`, `cli-overrides/claude-CLAUDE.md`, `cli-overrides/opencode-xninetzy-paksa.md`, `manifest.json`.

Validation: `scripts/validate_prompt_contract.py`, `scripts/verify_prompt_injection.sh`, `tests/governance/test_prompt_contract.py`. Architecture/evidence: [global prompt governance](../architecture/GLOBAL_PROMPT_ARCHITECTURE.md), [instruction inventory](../audits/GLOBAL_INSTRUCTION_INVENTORY.md), [conflict report](../audits/PROMPT_CONFLICT_REPORT.md), [global baseline](../evaluation/GLOBAL_AGENTIC_BASELINE.md).

Verification: 10 static/integrity test cases; canonical shell check passes; installed comparison returns nonzero drift and performs no writes. Known unsafe source edits are tested even after their content hash is updated. This is not a complete natural-language policy checker, adversarial model evaluation or security-proof mechanism.

## Measured and unmeasured

Actual cl100k_base tokens are measured for the same referenced composition. Candidate Claude composition: 1840 vs5295 installed; OpenCode:1835 vs5217. No actual billing, model accuracy, completion rate, tool-call reduction or latency gain was measured. Native cross-client parity remains NOT_VERIFIED_IN_LIVE_ENVIRONMENT.

The existing ranker has measured Indonesian intent failures; metadata extraction/registry groups are incomplete. No semantic router, new agent framework, global installer or additional MCP tool was introduced. G2 metadata compatibility, G3 typed handoffs, G4 runtime context budget wiring, G5 cross-domain outcomes, G6 controlled rollout, G7 approved sync and G8 behavioral evaluation remain open.

## Compatibility, rollback and next action

No public tool contract or data migration changed. Shell default still inspects installed state; `--canonical` targets repository-only validation. Missing optional client instruction files are reported as missing relative to the candidate bundle; users need not install every client. No host install or destructive rollback is automatic.

Restore repository source/manifest/validator changes together to roll back. Host rollback is unnecessary because installed files did not change. Before future installation: review exact diffs and owner additions, preserve backups, obtain required authorization, apply atomically and verify. Before routing optimization: curate objective held-out requests and compare against the measured current selector; do not hardcode benchmark answers.
