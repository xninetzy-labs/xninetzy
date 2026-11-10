# Known limitations at the current checkpoint

Recorded 2026-11-10; release decision NOT_READY. [Risk register](../audits/SECURITY_RISK_REGISTER.md) contains threat/evidence details and [backlog](../audits/GAP_ANALYSIS.md) supplies priorities.

- Approval authenticity/atomic use is unresolved in the context invocation gate; valid side-effect metadata can still be caller-supplied. Rejecting malformed names is a narrow improvement.
- Idempotency retains payload-sensitive keys, optional blank keys and release after ordinary exceptions. Pending crashes require reconciliation. Providers without idempotency/reconciliation cannot have exactly-once delivery guaranteed by this helper.
- Root correction may refuse host startup when an old sibling database exists. Explicitly select the intended store in process configuration after review; no data is auto-migrated or selected by timestamp/size.
- Redaction protects tested future Lightning serialization. It does not retroactively clean logs or prove complete secret detection. Other automatic-memory/graph hooks need input minimization and independent privacy checks.
- 571 registrations do not mean 571 available or production-ready capabilities. Schema absence, approval argument absence and heuristic risk labels require call-path investigation rather than blanket vulnerability claims.
- Two legacy underscore skill mirrors remain rejected with canonical replacements. Nested career/self-improvement metadata and resource discovery require compatible repair; disabled/embedded skill files are not all active capabilities.
- Indonesian skill-routing probes demonstrate gaps; no new router or tested 50-task end-to-end success rate is delivered.
- Prompt candidates are repository-local. Host files still carry the old instructions; no approved installation/automatic merge occurred. Hash/regex checks do not prove LLM injection resistance.
- Local STDIO works with temporary data. HTTP remote auth, current-spec support, native cross-client parity, portal actions, complete deployment, full suite/lint, backup/restore and retrieval quality remain incomplete.
- Workflow incomplete outcomes now persist FAILED while retaining successful steps; general DAG dependencies and safe restart/resume remain open. Graph False acknowledgements and exhausted claims are corrected, but live recovery/resync and complete index consistency are unverified; disabled projections require explicit resync when enabled.
- Performance samples are small, background hooks disabled and not a comparative benchmark. RSS probe was invalid; resource metrics remain NOT_MEASURED.

Preserve user data and existing permission/authentication boundaries when addressing these limits. No new infrastructure is justified until a measured existing limitation requires it.
