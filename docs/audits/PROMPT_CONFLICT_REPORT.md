# Prompt Conflict Report

November16 continuation (`VERIFIED_CODE/TEST/RUNTIME`): preserve the owner's
v2.2 operating choices and remove repeated hot integration detail in a v2.3
bundle, now installed after explicit owner approval. Conditional domain references retain the prior wording;
the hot entrypoint requires them before work. Nine-file hashes, known unsafe
policy regressions and untracked-reference deletion checks pass. CORE_RULES.md
and actual host permissions are unchanged. L0/shared and three references were
installed with private backups; installed comparison now reports9/9 matching
hashes. The checker remains read-only and grants no permissions. Native loading
and behavioral equivalence remain separate. Higher-priority developer reasoning rules
still apply even when a candidate suggests fewer reasoning calls.

Native context-engineering metadata is unchanged and its prior body is retained
verbatim in a resource. No assurance of equivalent LLM behavior follows from
structural tests. Cost and exact limits are in CONTEXT_COST_RESULTS.json / Phase2.

Audit date: 2026-11-10. Repository baseline: `main` at `2d0f13f`, with preexisting user changes preserved. This report records the baseline before candidate prompt changes. Evidence labels: `VERIFIED_CODE` for inspected files; `VERIFIED_RUNTIME` for local execution; `VERIFIED_TEST` for passing tests; `DOCUMENTED_ONLY` for unexecuted intended behavior; `UNKNOWN` for unavailable evidence.

Findings are baseline static instruction defects, not proof of an executed authorization bypass. Runtime enforcement must be tested separately. Repository candidates may resolve canonical text while owner-installed files remain unchanged.

| ID | Classification | Evidence | Impact / priority | Recommended correction |
|---|---|---|---|---|
| PR-01 | CRITICAL_CONFLICT | Baseline docs/prompt-injection-core/CORE_PROMPT.md:2; CORE_RULES.md:14-17; installed equivalents | Local Markdown claims highest priority over vendor/host defaults; P1 | Explicit host/developer/authorized-owner hierarchy; specificity grants no permissions |
| PR-02 | SECURITY_CONFLICT | Baseline CORE_RULES.md:123-127; installed continuity:153-160 | Skip validation override has no security exclusion; P1 potential policy confusion | Allow workflow customization only; never bypass auth, approvals, critical validation or institutional boundaries |
| PR-03 | BEHAVIOR_CONFLICT | Baseline CORE_PROMPT.md:15, CORE_RULES.md:35,49; ~/.agents/AGENTS.md:441 onward | Universal FIRST/LAST reasoning vs adaptive per-task guidance; P1 | Use external reasoning when it supplies useful structured planning; do not retain raw private reasoning |
| PR-04 | REDUNDANT_INSTRUCTION | Baseline CORE_PROMPT.md:10 and 40-44; continuity:71-160 repeats routing/permissions | Duplicate mandatory skill stages/context; P2 | Keep L0 identity/routing, L1 shared contract, L2 genuine client differences |
| PR-05 | BEHAVIOR_CONFLICT | Baseline CORE_PROMPT.md:23-38; ~/.agents/AGENTS.md:309-316 | Prefix priority makes native tools last resort independent of capability; P1 | Canonical domain tools for owned state; native tools for authorized local coding |
| PR-06 | AMBIGUOUS_RULE | Baseline CORE_RULES.md:108-120 and L2 permission tables | Name patterns cannot enforce side-effect semantics or all external writes; P1 | Canonical policy metadata + independent runtime gate; prompts describe rather than grant permissions |
| PR-07 | OUTDATED_INSTRUCTION | Baseline cli-overrides/arkcli-SKIPPED.md:1-8 vs shutil.which(arkcli) | Installed arkcli contradicts historical skip decision; P2 | Mark snapshot historical; verify client behavior before adding adapter |
| PR-08 | EXCESSIVE_CONTEXT | Installed OpenCode AGENTS.md=7815 tokens, shared .agents/AGENTS.md=7407, primary role=4431 | Large overlapping instruction surfaces; P2 | Measure actual loaded subset and evaluate minimal selected context; do not sum unverified loading |
| PR-09 | OUTDATED_INSTRUCTION | docs/SKILLS_INDEX.md:3; registry_extractor/extract.py:14-15 | 69/70 skill count claim vs125 direct/166 recursive; stale tool/skill constants; P2 | Generated inventory with explicit scopes, avoid hand-maintained counts |
| PR-10 | UNVERIFIED_ASSUMPTION | Baseline scripts/verify_prompt_injection.sh checks headings/counts, requires REASONING ENGINE/WORKFLOW LOCK | Format checks do not establish behavioral correctness; P1 | Semantic policy tests and mutation cases; leave live parity unclaimed |
| PR-11 | AMBIGUOUS_RULE | Installed OpenCode role files start with heading + fenced YAML | Native agent frontmatter loading not executed; UNKNOWN | Validate through actual installed parser before declaring roles available |
| PR-12 | OUTDATED_INSTRUCTION | Baseline tests/governance/test_skill_frontmatter.py:28-37; tests/os/skills/test_skills.py:58-64 | Broad xfail attributes kebab-name errors to YAML/hook damage; P1 | Resolved in this batch: strict YAML test + canonical validation + explicit legacy rejection + isolated health check |

## Verification and implementation

The two stale broad xfail branches were replaced without changing runtime or user skills. `tests/governance/test_skill_frontmatter.py` now checks strict YAML in every direct file, validates all eligible canonical definitions, and documents the two existing underscore mirrors with exact rejection assertions and canonical replacements. `tests/os/skills/test_skills.py` now isolates user discovery and asserts the exact two legacy name errors. New unexpected damage fails.

Focused verification: `MCP_HOST_DATA_DIR=/tmp/xn-audit-ntrdbz3g DATA_DIR=/tmp/xn-audit-ntrdbz3g SQLITE_PATH=/tmp/xn-audit-ntrdbz3g/skill-tests.sqlite3 .venv/bin/python -m pytest -q tests/governance/test_skill_frontmatter.py tests/os/skills/test_skills.py` → **14 passed, no xfail**. `.venv/bin/ruff check` on those files → **passed**. This closes misleading test evidence, not the deeper skill-discovery/routing gaps.

No host instruction files changed. Behavioral latency improvement from removing ceremonial reasoning is NOT_MEASURED. Next: parent implementation batch validates canonical prompt changes; subsequent approved sync must preserve owner additions and backups. Rollback: restore only the two changed tests and generated reports from the reviewed patch; no schema migration or production state change.

Repository candidate status: canonical L0/L1/L2 and the new canonical continuity source now correct PR-01 through PR-06 in template text. Installed host copies still retain the baseline conflicts; no automatic install occurred. See GLOBAL_AGENTIC_BASELINE.md for actual token counts. A corrected prompt and passing regex/hash checks do not prove behavioral injection resistance or runtime policy enforcement.
