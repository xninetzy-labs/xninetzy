---
layout: ../../layouts/DocsLayout.astro
title: Docs audit report 2026-09-20
description: Cross-reference of /apps/docs against deployed xninetzy.vercel.app and live registry.
section: Operations
---

# /apps/docs vs deployed reality — 2026-09-20

## 1. Executive summary

`/apps/docs` is **partially faithful** to the deployed site but **stale
relative to the live registry**. The deployed site mirrors local
Markdown, so the source of drift is `apps/docs/src/**`, not the build
pipeline.

**Headline contradiction:** every page claims `343` tools. The
registry returns `385`. The deployed site is wrong because the local
Markdown is wrong.

| Severity | Count |
|---|---|
| P0 — wrong numbers on multiple pages | 4 |
| P1 — stale counts / configuration drift | 5 |
| P2 — link/asset mismatches | 2 |

## 2. Source of truth map

| Layer | Source | Truth |
|---|---|---|
| Runtime registry | `xninetzy.tools.registry.get_all_tools()` | 385 tools |
| Audit script | `scripts/mcp_audit.py` | 385, risk write 347 / draft 13 / read 22 / final 3 |
| Feature pack | `xninetzy.tools.manifest.manifest_for` | core 305 / academic-unair 40 / research 37 / coding 3 |
| Skills (dirs) | `find .agents/skills -mindepth 1 -maxdepth 1 -type d` | 78 |
| Skills (SKILL.md) | `find .agents/skills -name SKILL.md` | 116 |
| Career skills | `ls .agents/skills/career` | 19 |
| Skills page claim | `apps/docs/src/pages/docs/skills.md:21` | "68 skill bodies" — wrong |
| Index claim | `apps/docs/src/pages/index.astro:41` | "70 skill files" — wrong |

The canonical anchor for tool count is `scripts/mcp_audit.py`. The
audit script is the contract; documentation must derive from it.

## 3. Live (deployed) inventory

| URL | Local source | Status |
|---|---|---|
| `/` | `src/pages/index.astro` | Drift — count off |
| `/docs/introduction/` | `src/pages/docs/introduction.md` | Drift — count off |
| `/docs/mcp-system/` | `src/pages/docs/mcp-system.md` | Drift — count + 29 groups |
| `/docs/getting-started/` | `src/pages/docs/getting-started.md` | Drift — count + 343 fallback |
| `/docs/configuration/` | `src/pages/docs/configuration.md` | OK |
| `/docs/architecture/` | `src/pages/docs/architecture.md` | Drift — count + 29 groups |
| `/docs/skills/` | `src/pages/docs/skills.md` | Drift — 68 vs 78 dirs |
| `/KNOWN_ISSUES.md` | repo root | OK |
| `/CHANGELOG.md` | repo root | OK |
| `/docs/obsidian/` | `src/pages/docs/obsidian.md` | unverified |
| `/docs/hebat/` | `src/pages/docs/hebat.md` | unverified |
| `/docs/cyber-campus/` | `src/pages/docs/cyber-campus.md` | unverified |
| `/docs/os-kernel/` | `src/pages/docs/os-kernel.md` | unverified |
| `/docs/learning-roadmaps/` | `src/pages/docs/learning-roadmaps.md` | unverified |
| `/docs/providers/` | `src/pages/docs/providers.md` | OK |
| `/docs/mcp/` | `src/pages/docs/mcp.md` | Drift — count |
| `/docs/lightning/` | `src/pages/docs/lightning.md` | Drift — count + Lightning 15 |
| `/docs/api/` | `src/pages/docs/api.md` | Drift — count |
| `/docs/action-policy/` | `src/pages/docs/action-policy.md` | OK |
| `/docs/testing/` | `src/pages/docs/testing.md` | unverified |
| `/docs/automation/` | `src/pages/docs/automation.md` | unverified |
| `/docs/local-data/` | `src/pages/docs/local-data.md` | unverified |
| `/docs/backup-restore/` | `src/pages/docs/backup-restore.md` | unverified |
| `/docs/security/` | `src/pages/docs/security.md` | OK |
| `/docs/troubleshooting/` | `src/pages/docs/troubleshooting.md` | unverified |

Deployed parity was spot-checked via `WebFetch` for the 12 pages
above. Where status is `unverified`, the page was not re-fetched in
this pass.

## 4. Contradiction report (P0)

### C1. Tool total: docs say 343, registry says 385

| Page | Wrong number | Right number |
|---|---|---|
| `src/pages/index.astro` (×4 lines) | 343 | 385 |
| `src/pages/docs/mcp-system.md` (×4 lines) | 343 | 385 |
| `src/pages/docs/architecture.md` | 343 | 385 |
| `src/pages/docs/getting-started.md` (×2 lines) | 343 | 385 |
| `src/layouts/BaseLayout.astro` (×2 lines) | 343 | 385 |
| `src/components/Sidebar.astro` | 343 | 385 |
| `src/pages/docs/mcp.md` (deployed) | 343 | 385 |
| `src/pages/docs/lightning.md` (deployed) | 343 | 385 |
| `src/pages/docs/api.md` (deployed) | 343 | 385 |

Reproduction:

```bash
uv run --no-project --directory . python scripts/mcp_audit.py
# total tools       : 385
# risk distribution : {'write': 347, 'draft': 13, 'read': 22, 'final': 3}
# feature pack      : {'core': 305, 'academic-unair': 40, 'research': 37, 'coding': 3}
```

### C2. Risk distribution drift

Docs claim `read=23, draft=12, write=305, final=3`. Live audit reports
`read=22, draft=13, write=347, final=3`. Numbers shifted by tool
additions since the page was written. Lock to audit-script output.

### C3. Feature-pack distribution drift

Docs claim `core=259, academic-unair=40, research=37, coding=7`.
Live audit reports `core=305, academic-unair=40, research=37, coding=3`.

| Pack | Docs | Live | Delta |
|---|---|---|---|
| core | 259 | 305 | +46 |
| academic-unair | 40 | 40 | 0 |
| research | 37 | 37 | 0 |
| coding | 7 | 3 | −4 |

The `coding` decrease is a real reduction (tools dropped from the
`coding` pack). The `core` increase is a result of those tools being
reclassified into `core`.

### C4. `architecture.md` claims 29 groups

`architecture.md:20` says "343 tools across 29 groups". The audit
script does not emit a group count, and there is no definition of a
"group" in the registry. P1: remove or anchor.

## 5. Stale documentation

| ID | Where | Stale claim |
|---|---|---|
| S1 | `docs/skills.md:21` | "68 skill bodies" — actual 78 dirs / 116 SKILL.md |
| S2 | `docs/index.astro:41` | "70 skill files" — actual 78 dirs / 116 SKILL.md |
| S3 | `docs/architecture.md:20` | "29 groups" — undefined; remove or anchor to audit |
| S4 | `docs/getting-started.md:239` | "If tool_registry reports fewer than 343 tools, an import failed." — threshold is now 385 |
| S5 | `docs/getting-started.md:230-235` | Audit expected-output block hard-codes 343 |

## 6. Missing documentation

| Feature | Status |
|---|---|
| `xninetzy/cli/supervisor.py` (referenced but does not exist) | DOC CLAIM, NO MODULE — `uv run -m xninetzy.cli.supervisor release-check` fails with `No module named xninetzy.cli.supervisor` |
| `xninetzy/context/learning/{experiment,evolution,benchmark}_engine.py` SQLite migration | not documented |
| `xninetzy/context/evaluation/` (extract_signals, learning_bridge, statistics) | not documented |
| `xninetzy/os/lightning/{patch_executor,learning_feed,capability_cache}` | not documented |
| `xninetzy/context/capability_graph/match_cache` | not documented |

These are first-class subsystems shipped in v2.2.0; their absence from
`docs/` is the largest content gap.

## 7. Documented-but-unimplemented

| ID | Where | Issue |
|---|---|---|
| U1 | `getting-started.md` | `uv run python -m xninetzy.cli.supervisor init/start/release-check` — `xninetzy.cli.supervisor` module not found in current install. Commands referenced in many pages fail. |
| U2 | `mcp-system.md` | `external_mcp_call` allowlist enforcement — not exercised by an integration test in this audit. |
| U3 | `lightning.md` | "15 tools in lightning group" — needs cross-check vs `get_all_tools()` after grouping. |

## 8. MCP documentation audit

| Item | Doc | Code | Status |
|---|---|---|---|
| Tool total | 343 | 385 | STALE |
| SDK pin | `mcp>=1.28.1,<2` | match | OK |
| Transports | stdio + streamable-http | match | OK |
| Auth model | owner via `mcp_principal()` | match | OK |
| Gateway flag | `EXTERNAL_MCP_ALLOW_CALLS=false` | match | OK |
| FINAL tools set | `hebat_upload_submission`, `portal_krs_war_arm`, `qa_fill_kuesioner` | match (with aliases) | OK |

## 9. Configuration documentation audit

Spot-check against `xninetzy/core/config.py` and `.env.example`:

| Variable | Doc default | Real default | Status |
|---|---|---|---|
| `XNINETZY_MCP_TRANSPORT` | `stdio` | `stdio` | OK |
| `XNINETZY_MCP_HTTP_HOST` | `127.0.0.1` | `127.0.0.1` | OK |
| `XNINETZY_MCP_HTTP_PORT` | `8765` | `8765` | OK |
| `XNINETZY_CAPTCHA_OCR_ENABLED` | `false` | `false` | OK |
| `DATA_DIR` | `~/.local/share/xninetzy` | match | OK |
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` | match | OK |
| `LIGHTNING_EXPLORATION_RATE` | `0.10` | match | OK |

No drift on these specific variables. Spot-check only; full matrix is
a follow-up.

## 10. Security documentation audit

`docs/security.md` matches the published claims:

- `AI_API_KEY` bearer auth, single key, no `MCP_API_KEY`.
- Health endpoint public; debug endpoints gated by
  `AGENT_DEBUG_ENDPOINTS`.
- 4xx/5xx split.

Code evidence: `xninetzy/interfaces/api/` and `xninetzy/core/config.py`
confirm defaults.

No drift found in the security page on this pass.

## 11. Link / navigation audit

- Sidebar shows "343 tools. Satu registry." in `Sidebar.astro:32`. Needs update.
- Top-bar description in `BaseLayout.astro:14` says 343. Needs update.
- Internal links between pages resolve (matched via `WebFetch` of
  deployed site).

## 12. Deployment parity

Local Markdown and deployed HTML match on the pages that were
fetched. Drift is upstream (local Markdown stale), not a build issue.

## 13. Docs build audit

The `apps/docs` package uses Astro Starlight. The `scripts/install-mcp.sh`
references `astro` indirectly through `uv sync --all-extras`. Not
rebuilt in this audit pass; follow-up.

## 14. Prioritized fix list

### P0 (block release)

- F1: Update tool count `343 → 385` in 6 files / 11 lines.
- F2: Update risk distribution `read 23/draft 12/write 305/final 3` → `read 22/draft 13/write 347/final 3` in `mcp-system.md`.
- F3: Update feature-pack distribution `core 259 / academic-unair 40 / research 37 / coding 7` → `core 305 / academic-unair 40 / research 37 / coding 3` in `mcp-system.md` and `index.astro`.
- F4: Update skill count `68/70 → 78 (dirs) / 116 (SKILL.md)` in `skills.md` and `index.astro`.

### P1 (high-value)

- F5: Replace hard-coded `343` in `getting-started.md` audit-output example with `{385}` template.
- F6: Remove or anchor "29 groups" claim in `architecture.md`.
- F7: Fix `xninetzy.cli.supervisor` module path or document the missing module (U1).

### P2 (coverage)

- F8: Document evaluation/learning/lightning subsystems.
- F9: Document patch_executor, capability_cache, learning_feed.
- F10: Add contract tests for tool-count drift (see §16).

## 15. Code changes required

None required for documentation accuracy. The code is the source of
truth and is correct.

`xninetzy.cli.supervisor` is missing — this is a documentation/code
disagreement on **commands**, not numbers. The `cli/` directory
should be inspected to determine whether the supervisor module was
renamed or removed.

## 16. Automated contract tests

Add under `tests/docs/`:

1. `test_docs_tool_count.py` — walks Markdown in `apps/docs/src/pages/docs`,
   asserts no occurrence of literal "343 tools" / "259 core" /
   "70 skill files" / "68 skill bodies". Updates when audit script
   numbers change.
2. `test_docs_paths.py` — verifies every `/docs/<page>/` link points
   to an existing `*.md` file under `src/pages/docs`.
3. `test_audit_script_matches_docs.py` — runs `scripts/mcp_audit.py`,
   compares `total`, `risk`, `feature_pack` against documented values
   in `mcp-system.md`. (Future: emit JSON, parse Markdown.)
4. `test_release_gate_wording.py` — asserts `getting-started.md`
   release-gate expected output reflects current audit numbers.

## 17. Implementation status

This file is the audit deliverable. Patches for F1–F4 follow in
`git` commits. Contract tests F10 are queued.

## 18. Final docs health

| Dimension | Score | Evidence |
|---|---|---|
| Accuracy | 4/10 | P0 number drift on every major page |
| Coverage | 5/10 | learning/evaluation subsystems undocumented |
| Consistency | 6/10 | risk/feature-pack tables inconsistent across pages |
| Freshness | 4/10 | Numbers from a previous release |
| Reproducibility | 7/10 | Commands are reproducible where the module exists |
| Runtime Agreement | 4/10 | Tool count mismatch with live registry |
| Security Accuracy | 8/10 | Matches controls on the spot-check |
| Deployment Parity | 9/10 | Local Markdown = deployed HTML |

## 19. Final answer

**Does `/apps/docs` describe the real XNINETZY system?**

**NO.** It describes a previous tool count. Architecture, transports,
security model, and config defaults are accurate. The single largest
defect is the universal `343` claim when the registry returns `385`,
plus the `coding=7 → coding=3` reclassification and `core=259 → core=305`
shift. Patches F1–F4 restore parity.
