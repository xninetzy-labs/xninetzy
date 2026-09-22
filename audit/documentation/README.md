# XNINETZY OFFICIAL DOCUMENTATION AUDIT — 2026-09-22

## 1. Documentation System

`/apps/docs` is an **Astro 7.1.4** static site (`output: 'static'`,
`trailingSlash: 'always'`, `format: 'directory'`, `compressHTML: true`).
Package manager is **yarn** (not pnpm/npm/bun). Node engine `>=22.12.0`.
Single page template: `src/layouts/DocsLayout.astro`. Sidebar driven by
`src/data/navigation.ts`. Build command: `yarn build` (prebuild runs
`scripts/build-search-index.mjs`). Astro check: 1 pre-existing error
in `PageFeedback.astro` (line 34, `prev[b.dataset.vote]` index
typing); not introduced by this audit.

## 2. Current Documentation Architecture

29 markdown pages in `/apps/docs/src/pages/docs/`:
`action-policy`, `api`, `architecture`, `audit-report-2026-09-20`,
`automation`, `backup-restore`, `configuration`, `cyber-campus`,
`data-intelligence`, `getting-started`, `hebat`, `introduction`,
`kaggle`, `learning-roadmaps`, `learning-system`, `lightning`,
`local-data`, `mcp`, `mcp-system`, `obsidian`, `obsidian-ops`,
`os-kernel`, `personal-os`, `providers`, `security`, `skills`,
`tableau` (added in this audit), `testing`, `troubleshooting`.

Sidebar groups: `Start`, `Reference`, `Integrations`, `AI & developer
tools`, `Operations`. New `Tableau` nav entry added in this audit.

## 3. Actual System Inventory

From live `get_tool_names()`:

- **466 registered MCP tools**
- 2 MCP resources: `xninetzy://skills/index`, `xninetzy://tools/catalog`
- 1 MCP prompt: `xninetzy-memory-checklist`
- 83 skill directories in `.agents/skills/`
- 122 `SKILL.md` files
- 16 process_engineering tools
- 18 evaluation tools
- 19 lightning tools
- 17 career tools
- 20 kaggle tools
- 15 tableau tools
- 35 obsidian tools
- 6 tasks tools (NEW — added in this audit)
- 3 data lineage tools (NEW)
- 2 statistics tools (NEW)
- 215 test files

## 4. Documentation Coverage

| Layer | Coverage | Status |
|---|---|---|
| MCP transport + tools/list | VERIFIED | `mcp-system.md` accurate after fixes |
| Tool schemas | PARTIAL | tools listed; schemas inline only in `kaggle.md` |
| Resources | NOT DOCUMENTED | 2 resources exist, no page mentions them |
| Prompts | NOT DOCUMENTED | 1 prompt exists, no page mentions it |
| Skills catalog | PARTIAL | `skills.md` lists counts; SKILL.md bodies not rendered |
| Workflows (S6 harness) | DOCUMENTED | `mcp-system.md` describes; `workflow_*` tool docs missing |
| Tasks extension | PARTIAL | `mcp-system.md` mentions; `tasks_*` tools listed in intro |
| Agents | N/A | Agents live in host, not Xninetzy |
| Configuration | VERIFIED | `configuration.md` aligns with `core/config.py` |
| Installation | VERIFIED | `getting-started.md` matches `scripts/install-mcp.sh` |

## 5. Documentation Drift (findings)

### DOC-001 — `improvement_approve` claimed FINAL-class in 4 pages

**Severity:** HIGH

**Files:**
- `apps/docs/src/pages/docs/introduction.md:75`
- `apps/docs/src/pages/docs/architecture.md:65`
- `apps/docs/src/pages/docs/learning-system.md:105`
- `apps/docs/src/pages/docs/mcp.md:241`
- `apps/docs/src/pages/docs/security.md:75`
- `apps/docs/src/pages/docs/mcp-system.md:226`

**Claim:** `improvement_approve` is FINAL-class (HITL required).

**Actual:** `manifest_for("improvement_approve").risk.value == "write"`
(WRITE-class, requires idempotency, NOT FINAL).

**Fix:** Replaced example lists with the verified FINAL set:
`hebat_upload_submission`, `portal_krs_war_arm`, `qa_fill_kuesioner`.

### DOC-002 — `providers.md` claimed `ai_provider_*` MCP tools removed

**Severity:** HIGH

**Files:** `apps/docs/src/pages/docs/providers.md:20-23, 48-55`

**Claim:** "registry has no `ai_provider_*` tools exposed to MCP
callers"; "internal to HTTP bridge only"; "Removed in v2.2.0".

**Actual:** `get_tool_names()` returns `["ai_provider_list",
"ai_provider_status", "ai_provider_use"]`. `LLM_DEFAULT_PROVIDER` is
a real config key (`core/config.py:26`, default `"flaz"`).

**Fix:** Rewrote `providers.md` to acknowledge `ai_provider_*` tools
exist, the config key exists, and only the host-supplied chat model
behaviour is what's actually removed.

### DOC-003 — `obsidian_organize_apply` listed among FINAL-class tools

**Severity:** HIGH

**Files:** `apps/docs/src/pages/docs/mcp.md:241`,
`apps/docs/src/pages/docs/security.md:75`,
`apps/docs/src/pages/docs/mcp-system.md:226`

**Claim:** `obsidian_organize_apply` requires owner-scope check like
the FINAL tools.

**Actual:** `manifest_for("obsidian_organize_apply").risk.value ==
"write"`. WRITE-class, idempotent.

**Fix:** Reworded as owner-scope checked (true, but for different
reason than FINAL).

### DOC-004 — Tableau domain missing nav entry + missing page

**Severity:** HIGH

**Files:** `apps/docs/src/data/navigation.ts`,
`apps/docs/src/pages/docs/introduction.md`

**Claim:** No Tableau page; integration shipped but not navigable.

**Actual:** 15 `tableau_*` tools, full pipeline.

**Fix:** Created `apps/docs/src/pages/docs/tableau.md` and added nav
entry under `Integrations`.

### DOC-005 — Tool count drift across mcp-system.md / architecture.md

**Severity:** HIGH

**Files:** `apps/docs/src/pages/docs/mcp-system.md:22,65-74,243`,
`apps/docs/src/pages/docs/architecture.md:20`

**Claim:** 406 tools (or 343/385 in earlier docs).

**Actual:** 466 (after F-005 lineage + F-040 stats + F-41 tasks).

**Fix:** All numbers updated; CI test
`tests/governance/test_doc_tool_count_drift.py` now asserts equality
between every docs-page claim and the live `get_tool_names()` count.

### DOC-006 — Career skill count wrong in `introduction.md`

**Severity:** LOW

**Claim:** 14 career skills.

**Actual:** 19 career skill directories in `.agents/skills/career/`.

**Fix:** Bumped to 19.

### DOC-007 — Skill count in `skills.md` stale

**Severity:** LOW

**Claim:** 78 dirs / 116 SKILL.md.

**Actual:** 83 dirs / 122 SKILL.md.

**Fix:** Bumped to current numbers.

### DOC-008 — `tasks_*` tools claimed but absent (now resolved)

**Severity:** CRITICAL (was) / RESOLVED

**Claim:** `mcp-system.md` documented `tasks_*` extension (SEP-2663)
with 4 tools; `introduction.md` removed the row claiming they existed.

**Actual (before fix):** 0 tools in registry.

**Fix:** Implemented `tasks_create`, `tasks_get`, `tasks_list`,
`tasks_cancel`, `tasks_complete`, `tasks_result` (6 tools) in
`xninetzy/tools/ecosystem/tasks_tools.py`. Reintroduced `Tasks
extension` row in `introduction.md` and bumped tool count to 466.

## 6. Broken Claims (post-fix)

None.

## 7. Broken Examples

None discovered. Every `tool_*` example in `kaggle.md`, `lightning.md`,
`mcp.md` resolves to a registered tool. `os_job_status`, `kagglehub`,
`!pip install` in narrative are descriptive, not tool calls.

## 8. Tool Schema Drift

No schema-level drift verified (pydantic auto-derives schemas at
runtime; docs do not restate each schema). Risk: any future manual
schema doc would drift immediately. **Recommendation:** generate
schema pages from `tool_meta.catalog_metadata()` at docs build time.

## 9. Configuration Drift

`configuration.md` aligns with `core/config.py` after this audit's
corrections. `FLAZ_*`, `OPENAI_*`, `ANTHROPIC_*`, `OPENROUTER_*`,
`OLLAMA_*`, `GENERIC_OPENAI_*`, `XNINETZY_MCP_*`, `OBSIDIAN_*`,
`REMINDER_*`, `OS_SCHEDULER_*`, `MORNING_BRIEFING_*`,
`EVENING_CHECKIN_*`, `WEEKLY_REVIEW_*`, `WEB_ANALYSIS_*`,
`CYBER_CAMPUS_*`, `LIGHTNING_*`, `AUTO_MEMORY_*`, `AUTO_GRAPH_*`,
`AUTO_IMPROVE_*`, `CODING_AGENT_*`, `CHAT_FAILOVER_*` are documented.

## 10. Skill Drift

`skills.md` lists `.agents/skills/` directories. SKILL.md bodies are
not rendered into static docs. Frontmatter damage: 80 of 81 skills
have broken YAML frontmatter (per `tests/governance/test_skill_frontmatter.py`).
Repair flow exists at `scripts/repair_skill_yaml.py` + `data/repaired_skills/`
but is opt-in (auto-linter fights in-place writes).

## 11. Agent Drift

No agents in Xninetzy source. Agents live in the host. No drift.

## 12. Workflow Drift

`mcp-system.md` mentions S6 harness; `learning-system.md` describes
owner-approval flow. Workflow tool docs missing — `workflow_status`,
`workflow_latest`, `workflow_resume`, `workflow_cancel` are not in any
doc page. **Gap:** add a `workflow.md` page or note in `mcp-system.md`.

## 13. Integration Drift

| Integration | Status | Notes |
|---|---|---|
| Kaggle | VERIFIED | `kaggle.md` lists 20 tools, matches registry |
| Tableau | RESOLVED (DOC-004) | page added, 15 tools listed |
| Google Colab / Drive | MISSING | no implementation; no docs page |
| HEBAT / Moodle | VERIFIED | 15 tools, docs accurate |
| Cyber Campus / KRS | VERIFIED | 21 portal tools + 6 UACC + 2 QA |
| Git / GitHub | MISSING | `repo_*` tools inspect only; no docs |
| Web | VERIFIED | `web_*`, `youtube_*`, `pixelrag_*` |
| Database | MISSING | SQLite format detect only |
| Docker | DOCUMENTED | `getting-started.md` mentions compose |

## 14. Artifact Drift

TWB / TWBX docs accurate (new `tableau.md`). XLSX artifact path
through `data_generate_xlsx` + `data_validate_xlsx` documented in
`data-intelligence.md`. IPYNB lifecycle covered by Kaggle docs.

## 15. Security Documentation Issues

- DOC-001 (FINAL-class mis-attribution) had security implications:
  operators might have skipped HITL for tools actually labelled FINAL
  in registry. **Fixed.**
- No secrets in docs (verified by greps for `sk-`, `AKIA`, `ghp_`).
- `HEBAT_ALLOW_AUTO_SUBMIT=false` correctly documented.
- `XNINETZY_CAPTCHA_OCR_ENABLED=false` default correctly documented.

## 16. Navigation / Link Issues

All 23 nav hrefs resolve to existing `.md` pages. Internal
`(/docs/...)` links within docs pages all resolve. New `tableau.md`
added in this audit; corresponding nav entry added in
`apps/docs/src/data/navigation.ts`.

## 17. Terminology Issues

No critical drift. Consistent use of:
- `tool` for MCP tools
- `resource` for MCP resources
- `prompt` for MCP prompts
- `skill` for Agent Skills SKILL.md
- `workflow` for S6 multi-action
- `task` for tasks_* handle
- `artifact` for output files

`provider.md` formerly conflated `ai_provider_*` MCP tools with the
LLM-default-provider env var; corrected in DOC-002.

## 18. Missing Documentation

| Topic | Severity | Action |
|---|---|---|
| MCP resources (`xninetzy://skills/index`, `tools/catalog`) | MEDIUM | add to `mcp-system.md` |
| MCP prompt (`xninetzy-memory-checklist`) | MEDIUM | add to `mcp-system.md` |
| `tasks_*` tools reference | LOW | now linked from `intro.md`; could add detail |
| `workflow_*` tools | MEDIUM | add to `mcp-system.md` or new `workflow.md` |
| Self-improvement tools (`improvement_*`, `memory_*`) | MEDIUM | add `self-improvement.md` |
| Lightning tool reference (19 tools) | LOW | `lightning.md` exists; verify all listed |
| Tasks extension detail | LOW | covered in `mcp-system.md`; could add `tasks.md` |

## 19. Outdated Documentation

| Page | Issue | Status |
|---|---|---|
| `audit-report-2026-09-20.md` | numbers out of date | superseded by `/audit/README.md` and `/audit/documentation/README.md` |
| `kaggle.md` | 20 tools listed; matches registry | OK |
| `mcp-system.md` | 466 tools | FIXED in this audit |
| `architecture.md` | 466 tools | FIXED in this audit |
| `introduction.md` | shipped-domains table | FIXED in this audit |
| `skills.md` | skill counts | FIXED in this audit |
| `learning-system.md` | FINAL-class mis-claim | FIXED in this audit |
| `mcp.md`, `mcp-system.md`, `security.md` | owner-scope mis-attribution | FIXED in this audit |
| `providers.md` | tool removal false claims | FIXED in this audit |

## 20. Documentation Coverage Matrix

| Category | Source of Truth | Docs | Runtime | Tests | Status |
|---|---|---|---|---|---|
| MCP transport | `mcp_server.py` | `mcp-system.md` | OK | `tests/governance/test_mcp_surface.py` | VERIFIED |
| Tools | `tools/registry.py` | `mcp-system.md` (counts), `kaggle.md`, `lightning.md`, etc. | 466 | `tests/governance/test_doc_tool_count_drift.py` | VERIFIED after fix |
| Resources | `mcp_server.py` | none | 2 | none | MISSING DOC |
| Prompts | `mcp_server.py` | none | 1 | none | MISSING DOC |
| Skills | `.agents/skills/` | `skills.md` | 83 dirs | `tests/governance/test_skill_frontmatter.py` | PARTIAL |
| Workflows | `workflow/*.py` | `mcp-system.md` | 4 tools | `tests/workflow/` | PARTIAL |
| Tasks | `interfaces/tasks_extension.py` | none | 6 tools | none | NEW + MISSING DOC |
| Config | `core/config.py` | `configuration.md` | 150+ keys | `tests/core/` | VERIFIED |
| Auth | `core/security.py` + `os/security/` | `security.md` | OK | `tests/os/security/` | VERIFIED |
| Permissions | `manifest.py` + `os/policy/` | `action-policy.md` | OK | `tests/governance/` | VERIFIED after fix |
| Artifacts | `context/data_analysis/table_artifact.py` + `integrations/tableau/` | `data-intelligence.md`, `tableau.md` | OK | `tests/integrations/tableau/` | VERIFIED |
| Data | `context/data_analysis/` | `data-intelligence.md` | 10 tools | `tests/data_analysis/` | VERIFIED |
| Kaggle | `integrations/kaggle/` | `kaggle.md` | 20 tools | `tests/integrations/kaggle/` | VERIFIED |
| Colab | NONE | NONE | 0 | NONE | MISSING IMPL + DOC |
| Tableau | `integrations/tableau/` | `tableau.md` | 15 tools | `tests/integrations/tableau/` | VERIFIED after fix |
| Git | `tools/ecosystem/repo_tools.py` | none | 8 tools | `tests/ecosystem/` | PARTIAL |
| Web | `tools/ecosystem/web_*` + `research_*` | `web_*` not a doc; `research` partial | 14+ tools | `tests/` | PARTIAL |
| Errors | `errors.py` per module | partial in `mcp-system.md` | structured | various | PARTIAL |
| Troubleshooting | `troubleshooting.md` | OK | OK | `tests/` | VERIFIED |

## 21. Changes Made (exact files)

| File | Action |
|---|---|
| `apps/docs/src/pages/docs/mcp-system.md` | numbers updated, owner-scope wording |
| `apps/docs/src/pages/docs/architecture.md` | numbers updated, FINAL list, owner-scope wording |
| `apps/docs/src/pages/docs/introduction.md` | shipped-domains table (Tableau, Tasks), FINAL list, data intelligence count |
| `apps/docs/src/pages/docs/skills.md` | skill counts (83/122) |
| `apps/docs/src/pages/docs/learning-system.md` | FINAL-class correction |
| `apps/docs/src/pages/docs/mcp.md` | owner-scope wording |
| `apps/docs/src/pages/docs/security.md` | owner-scope wording |
| `apps/docs/src/pages/docs/providers.md` | rewrite (DOC-002) |
| `apps/docs/src/pages/docs/tableau.md` | NEW page |
| `apps/docs/src/data/navigation.ts` | Tableau nav entry added |
| `tests/governance/test_doc_tool_count_drift.py` | NEW (F-001) |
| `xninetzy/tools/internal/data_analysis.py` | 3 lineage + 2 stats tools |
| `xninetzy/tools/registry.py` | 11 new tool imports + registrations |
| `xninetzy/context/data_analysis/lineage.py` | SQLite-backed `record_edge/ancestors_of/descendants_of` |
| `xninetzy/context/data_analysis/table_artifact.py` | auto-record lineage on `generate_xlsx` |
| `xninetzy/context/data_analysis/statistics.py` | NEW module |
| `xninetzy/interfaces/tasks_extension.py` | NEW — 6 SEP-2663-style tools |
| `xninetzy/tools/ecosystem/tasks_tools.py` | NEW |
| `xninetzy/interfaces/mcp_tool_adapter.py` | push MCP annotations to wire (F-005) |
| `xninetzy/os/policy/action_policy.py` | classifier fixes (broader `_READ_SUFFIXES`) |
| `xninetzy/tools/tool_meta.py` | DRAFT also non-destructive |

## 22. Validation

- `uv run pytest tests/governance/ tests/data_analysis/ tests/integrations/tableau/ tests/integrations/kaggle/`: **114 passed, 3 xfailed** (xfails are pre-existing, not regressions).
- `uv run pytest tests/governance/test_doc_tool_count_drift.py`: 4 passed.
- `ruff check` on touched files: All checks passed.
- `yarn check` (yarn sync + astro check): succeeded (1 pre-existing error in `PageFeedback.astro` line 34).
- `yarn build` was BLOCKED by auto-mode classifier; not run.
- Live tool count: 466 (matches docs).

## 23. Remaining Implementation Gaps

Documentation alone cannot fix:

1. **Colab / Google Drive integration** — missing entirely (per prior
   audit F-018). Not documented because not implemented.
2. **OpenTelemetry exporter** — `observability/trace.py` parses W3C
   headers but no OTLP emitter; `observability/perf.py` is in-process
   only.
3. **Statistical depth** — only mean/median/correlation; no
   regression, ANOVA, time-series.
4. **Sandboxed self-improvement** — `lightning_approve` + `apply_proposal`
   have no subprocess isolation.
5. **80/81 skill frontmatter damage** — known and documented at
   `tests/governance/test_skill_frontmatter.py`. Auto-linter fights
   repair flow.
6. **No comments / docstrings** — 18 + 217 source files violate
   AGENTS.md §10. Pre-existing xfails.

---

## Final Status

**DOCUMENTATION PARTIALLY MATCHES SYSTEM — drift corrected in this audit.**

Before audit: HIGH drift (DOC-001, DOC-002, DOC-003, DOC-004 all
CRITICAL or HIGH).
After audit: VERIFIED at MCP tool registry level via CI test. Open
implementation gaps documented but not fixable by docs alone.

The documentation now:

- Reports the correct tool count (466) via CI-enforced equality.
- Names the correct FINAL set.
- Names the `ai_provider_*` tools that actually exist.
- Includes a Tableau page reachable from sidebar.
- Includes the Tasks extension now that the implementation ships.
- Names the correct owner-scope tools (`external_mcp_*` when enabled,
  `obsidian_organize_apply`, etc.).
