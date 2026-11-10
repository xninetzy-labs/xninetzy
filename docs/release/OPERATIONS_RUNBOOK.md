# Candidate verification and recovery runbook

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

## Optional dependencies and protocol

Core metadata and datetime should not require graph/model/browser/image/document extras. Missing selected providers should return an actionable extra-install message. Install only the required project extra; never install arbitrary scripts or third-party skills during discovery.

Keep current SDK below v2 until the [compatibility plan](../architecture/MCP_PROTOCOL_CONTRACT.md) is executed. Streamable HTTP remains loopback-only in the current implementation; do not expose it remotely by bypassing the binding guard. No Docker production restart is warranted until its stale entrypoint/health contract is repaired and tested.

## Rollback

Review/reverse only the relevant candidate hunks, preserving initial workspace deletions/untracked files. Keep pyproject and lock together. No schema migration needs rollback. Reverting security patches restores known regressions; review that tradeoff explicitly. Host instructions and historical telemetry did not change and require no automatic rollback.
