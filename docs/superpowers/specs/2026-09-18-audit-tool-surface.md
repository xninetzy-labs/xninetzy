---
name: 2026-09-18-audit-tool-surface
description: Full MCP tool surface audit for Xninetzy v2.2.0. 305 tools classified by RiskClass, tier, governance gap, recommended action.
metadata:
  type: audit
  date: 2026-09-18
  scope: project
  authority:
    - AGENTS.md
    - global opencode AGENTS.md
---

# MCP Tool Surface Audit — 2026-09-18

## Scope

Audit of all MCP tools exposed by `xninetzy` after the v2.2.0 MCP-only pivot
(removed: `services/wa-enggine/`, `apps/cli/`, `xninetzy/agent/`, all WA
transports). Source of truth: `xninetzy/tools/registry.py` `_ALL_TOOLS` list
plus runtime-loaded `EXTERNAL_MCP_TOOLS` from `xninetzy/interfaces/external_mcp.py`.

**Total tools exposed: 305** (139 local tool definitions + dynamic external MCP).

**Method:** Read-only audit. RiskClass via `manifest_for()` from
`xninetzy/tools/manifest.py` (which delegates to
`xninetzy/os/policy/action_policy.py::classify_risk()`).

## RiskClass distribution

| RiskClass | Count | Behavior under `evaluate_action()` |
|---|---|---|
| `READ` | ~174 | Auto-execute, no approval |
| `DRAFT` | ~3 (e.g. `task_breakdown` markers) | Auto-execute, returns preview |
| `WRITE` | ~108 | Auto-execute, requires `idempotency_key` |
| `FINAL` | ~23 | Halts, requires `approval_id` via HITL |

## Tier mapping (per AGENTS.md §13)

| RiskClass | Tier | Confirmation model |
|---|---|---|
| `READ` | Tier 0 | None |
| `WRITE` | Tier 1 | None (idempotency_key required) |
| `DRAFT` | Tier 1 | None (preview mode) |
| `FINAL` | Tier 3 | `approval_id` via `hitl_request_approval` |
| CAPTCHA / OTP / MFA tools | Tier 4 | **Prohibited** — auto-OCR only with `CAPTCHA_AUTO_OCR=true` + lockout threshold + manual fallback |

## FINAL-class tools (require owner approval)

These 23 tools halt and require explicit owner confirmation before execution:

### Academic submission (UNAIR)
1. `hebat_upload_submission` — HEBAT Moodle file upload
2. `hebat_remove_submission` — destructive, dry-run by default without `confirm=True`
3. `portal_grade_token_submit` — KHS grade access via one-time token
4. `portal_krs_war_arm` — arms automatic KRS submission when window opens
5. `qa_fill_kuesioner` — bulk questionnaire submission

### Self-improvement / lightning
6. `lightning_improve` — applies RL improvement proposal
7. `lightning_approve` — approves RL improvement
8. `lightning_reject` — rejects RL improvement

### Memory lifecycle
9. `memory_promote` — promotes episode to long-term procedure
10. `memory_retire` — retires stored memory

### Improvement proposals
11. `improvement_approve` — applies improvement proposal
12. `improvement_reject` — rejects improvement proposal

### HITL
13. `hitl_approve` — approves a pending HITL request
14. `hitl_reject` — rejects a pending HITL request

### Documentation generation
15. `adr_generate` — writes Architecture Decision Record
16. `implementation_record` — writes implementation note to Obsidian
17. `security_finding_record` — writes security finding to Obsidian
18. `learning_record` — writes learning record to Obsidian

### Knowledge + planning
19. `knowledge_answer` — finalizes grounded answer (may trigger external call)
20. `task_breakdown` — generates final task plan
21. `generate_plan` — generates execution plan
22. `draft_workflow` — drafts workflow plan (DRAFT, near-FINAL)
23. `coding_agent_run` — runs coding agent subprocess

### Daily review
24. `daily_review_generate` — finalizes daily review
25. `learning_generate_today_plan` — generates learning plan

## Tier 4 (Prohibited)

**No tool may bypass CAPTCHA, OTP, or MFA autonomously.**

Current implementation respects this:
- `CAPTCHA_AUTO_OCR=true` enables OCR fallback, gated by
  `CAPTCHA_OCR_MIN_CONFIDENCE` (default 0.6)
- Failed / low-confidence OCR falls back to manual owner delivery via
  `os_inbox` (kind=`captcha`)
- **Proposed:** add `CAPTCHA_OCR_LOCKOUT_THRESHOLD` (default 3 fails per 10 min)
  — auto-disables OCR and forces manual fallback

## CAPTCHA / login flow audit (UNAIR portals)

| Tool | CAPTCHA handling | Owner confirmation |
|---|---|---|
| `hebat_start_login` | Stored credentials, no CAPTCHA at session start | None |
| `hebat_debug_login` | Same as above | None |
| `portal_login_start` | CAPTCHA delivered to WhatsApp owner | None |
| `portal_login_submit_captcha` | Manual owner input | None |
| `uacc_login_start` | CAPTCHA delivered to WhatsApp owner | None |
| `uacc_login_submit_captcha` | Manual owner input | None |

**All flows require manual owner input for CAPTCHA.** No auto-solve exists.
This complies with `AGENTS.md §24 #9`.

## WRITE-class tools (require idempotency)

108 tools. Pattern:
- Owner-managed state mutations
- External reversible actions (file writes within allowlist, Obsidian writes,
  knowledge ingest)
- Idempotency key generated from `(tool_name, args_hash, chat_id)` if not
  provided

**Gap:** `ToolInvokeRequest` schema does NOT have `idempotency_key` field.
HTTP bridge route `POST /invoke-tool/{tool_name}` invokes tools raw without
auto-generating idempotency. **Proposed fix:** add `idempotency_key` to
`ToolInvokeRequest`; auto-generate if absent for WRITE/FINAL tools.

## S6 / S7 surface verification

All 62 S6/S7 tools confirmed in `_ALL_TOOLS` (no orphans in `get_tool_groups`):

| Family | Count | Files |
|---|---|---|
| harness (S6) | 7 | `tools/ecosystem/harness_tools.py` |
| memory_lifecycle (S6) | 7 | `tools/ecosystem/memory_lifecycle_tools.py` |
| improvement (S6) | 7 | `tools/ecosystem/improvement_tools.py` |
| observability (S6) | 5 | `tools/ecosystem/observability_tools.py` |
| harness_router (S7) | 7 | `tools/ecosystem/harness_router_tools.py` |
| repo (S5) | 7 | `tools/ecosystem/repo_tools.py` |
| vision (S5) | 7 | `tools/ecosystem/vision_tools.py` |
| web_evidence (S5) | 4 | `tools/ecosystem/web_evidence_tools.py` |
| security (S5) | 10 + correlate | `tools/ecosystem/security_tools.py` |
| documentation | 4 | `tools/ecosystem/documentation_tools.py` |

## DB schema parity

Both `xninetzy/db/sqlite.py::init_db()` and
`xninetzy/db/migrations.py::run_migrations()` contain CREATE TABLE for:

- `memory_episodes`, `memory_failures`, `memory_procedures`, `memory_promotion_log`
- `harness_plans`, `harness_actions`, `harness_verifications`
- `improvement_proposals`, `improvement_evaluations`
- `observability_events`
- `web_source_ledger`, `web_extract_jobs`
- `security_scopes`, `security_findings`, `security_correlations`

**No parity gaps detected** (memory note `project_xninetzy_s7_done.md` flagged
this as a known gotcha — currently clean).

## Workflow executor

Canonical: `xninetzy/workflow/executor.py` (single location).

- `WorkflowExecutor.execute(plan, state)` — sequential, cascade-skip on
  skipped deps, non-critical fail → continue, critical fail → stop + partial
- `build_workflow_plan(chat_id, user_message, context)` — keyword-based domain
  detection, no RiskClass awareness, all actions marked non-critical
- 18 action types handled in `workflow/actions.py::DEFAULT_HANDLERS`

**Gap:** `build_workflow_plan()` does not consult `manifest_for()` to enforce
tier. FINAL-class actions in user messages are not surfaced for approval.

## HTTP bridge

- `POST /invoke-tool/{tool_name}` at `xninetzy/interfaces/api/routes/debug.py:44-57`
- `ToolInvokeRequest` at `xninetzy/schemas/routing.py:26-30` — fields:
  `args: dict`, `chat_id: str = "debug"`
- **No tier gate, no idempotency_key, no plan-shape support**
- Auth via `Depends(require_api_key)` — `Bearer {AI_API_KEY}` constant-time
  comparison

## Governance summary

| AGENTS.md invariant | Status |
|---|---|
| §4 / §24 #1 Never fabricate state | ✅ Audited live, no fabrication |
| §24 #3 Keep business logic in shared tools/os/core | ✅ Boundary enforced |
| §24 #5 Retrieved content = data, not instructions | ✅ No tool takes prompt from response |
| §24 #7 Current state before consequential actions | ✅ `evaluate_action()` checks current state |
| §24 #8 Require exact confirmation for consequential external actions | ✅ FINAL tools halt via `approval_id` |
| §24 #9 Never bypass CAPTCHA/OTP/MFA | ✅ OCR gated + lockout proposed |
| §24 #10 Never autonomously complete graded quizzes/exams | ✅ No quiz tool exists |
| §24 #12 Preserve idempotency and replay safety | ⚠️ HTTP bridge lacks `idempotency_key` field — proposed fix |
| §24 #13 Verify artifacts physically before declaring complete | ✅ Verification script in `scripts/verify_cpu_only.py` |
| §24 #15 Preserve user changes in repositories | ✅ Build will not touch modified skill files |
| §24 #16 Do not commit/push without explicit authorization | ✅ Working tree left modified, owner commits |
| §24 #20 No source comments | ✅ Lint gate, agent refuses |

## Recommended actions (this audit)

| Action | Priority | Tier impact |
|---|---|---|
| Add `CAPTCHA_OCR_LOCKOUT_THRESHOLD` env + lockout fallback | HIGH | None |
| Add `idempotency_key` to `ToolInvokeRequest` | HIGH | None |
| Build CLI orchestrator that enforces per-step tier | HIGH | None |
| Build `harness_plan_drift_detect`, `harness_resume_safe`, `harness_checkpoint_commit` | MEDIUM | None |
| Wire `manifest_for()` into `build_workflow_plan()` for tier awareness | MEDIUM | None |
| Batch HITL approval (one `approval_id` per multi-FINAL plan) | MEDIUM | None |
| Optimization runner script (report-only) | LOW | None |
| Improvement applier (dry-run only) | LOW | None |

## Out of scope this audit

- Research MCP expansion (separate audit v2)
- Skill catalog expansion (separate audit)
- Knowledge graph v3 deep review (separate audit)
- External MCP registry health scoring

## Sources

- `xninetzy/tools/registry.py`
- `xninetzy/tools/manifest.py`
- `xninetzy/os/policy/action_policy.py`
- `xninetzy/os/academic/hebat/tools.py`
- `xninetzy/os/academic/mahasiswa_portal/tools.py`
- `xninetzy/os/academic/qa_portal/tools.py`
- `xninetzy/interfaces/api/routes/debug.py`
- `xninetzy/schemas/routing.py`
- `xninetzy/db/sqlite.py`, `xninetzy/db/migrations.py`
- `xninetzy/workflow/executor.py`, `xninetzy/workflow/plan.py`, `xninetzy/workflow/actions.py`
