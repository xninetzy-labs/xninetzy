# Phase 2 / G1: canonical instruction and discovery foundation

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
