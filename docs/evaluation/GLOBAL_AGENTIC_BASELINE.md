# Global Agentic Context and Routing Baseline

## Current token-efficiency candidate, 2026-11-16

Named tokenizer: cl100k_base. [Raw before/after results](CONTEXT_COST_RESULTS.json)
come from `scripts/measure_context_cost.py` using disposable configuration and
no owner stores. Baseline is the owner's current v2.2 sources, not the historical
5268-token installation below. After explicit owner approval, bundle v2.3 is now
installed:9/9 file hashes match, with five changes and private rollback backups.

| Text surface | Before | Candidate | Interpretation |
|---|---:|---:|---|
| Codex referenced hot instructions |2653|2109|20.51% less; conditional references loaded when needed |
| Claude referenced hot instructions |2757|2213|19.73% less |
| OpenCode referenced hot instructions |2655|2111|20.49% less |
| Context-engineering selected body |1555|584|62.44% less; previous text preserved as reference |
| Same250 tool rows |19426|10124|47.88% less in opt-in compact output; policy fields retained |
| Same120 skill rows |6863|6515|5.07% less in opt-in compact output |
| Full registry schemas |103450|103599|149 more tokens for optional parameters; not an initialization reduction |

Five filtered memory-tool rows cost195 tokens; up to two filtered context-skill
rows124. Those disclose less information and are not full-catalog compression.
Loading all three conditional domain references adds730 tokens: the Codex
composition becomes2839, exceeding the old hot baseline for a task needing all
three domains. This is selected loading, not universal reduction or deleted policy.
Actual billed tokens, host tool injection, latency and model outcome quality are
NOT_MEASURED. The skill-context helper's configured limit is characters, not tokens;
no claim is made that every host invokes that helper.

Tests:7 failed/4 passed before the runtime fix; final expanded162 pass in24.02s,
overlapping the earlier84-case run. Routing/progressive disclosure, known unsafe
prompt changes, missing/untracked conditional policy, explicit approvals and
minimal-import contracts pass. Real SDK STDIO checks pass from source and a
fresh frozen base install. One reviewed skill fixture is copied into isolated
state; complete wheel-bundled skill availability and native host rollout are not
proved. All three edited runtime modules match the installed wheel. Whole-package
parity failed because concurrent unrelated core/Kaggle files changed during
installation; that failure is retained in the evidence rather than excluded.

Owner review/approval and nine-file installation are complete; native-client
reload/evaluation remains a separate gate. Installed file compositions independently
measure2109/2213/2111 cl100k_base tokens for Codex/Claude/OpenCode. Eleven prompt
tests and five installer fixture groups pass. No agent process was restarted and
no runtime permission/configuration was changed. No owner data mutation was
introduced by the fixtures. Phase2
records exact files, commands, safeguards and rollback.

Audit date: 2026-11-10. Repository baseline: `main` at `2d0f13f`, with preexisting user changes preserved. This report records the baseline before candidate prompt changes. Evidence labels: `VERIFIED_CODE` for inspected files; `VERIFIED_RUNTIME` for local execution; `VERIFIED_TEST` for passing tests; `DOCUMENTED_ONLY` for unexecuted intended behavior; `UNKNOWN` for unavailable evidence.

## Measurement method

Read-only instruction/skill snapshots were tokenized locally using tiktoken cl100k_base. Full hashes and file sizes are in GLOBAL_INSTRUCTION_INVENTORY.md and SKILL_VALIDATION_REPORT.md. Token counts are exact for that encoding; actual host-model billing counts are UNKNOWN. No model/provider call was made. Isolated routing used Settings(_env_file=None), DATA_DIR=/tmp/xn-audit-ntrdbz3g, and an empty user skill directory. Workload:8 hand-selected requests,1 timing sample each, on existing direct built-in catalog. This is a diagnostic sample, not a 50-task golden completion benchmark or a statistical performance claim.

| Instruction composition | Tokens | Interpretation |
|---|---|---|
| Installed L0 | 930 | Shared file |
| Installed L1 | 1579 | Shared file |
| Installed continuity | 1855 | Shared file |
| Installed Codex L2 | 904 | Host instruction file |
| L0+L1+continuity+Codex L2 | 5268 | Sum of referenced files only; excludes host system/developer/user/catalog/history |
| Repository AGENTS.md | 5126 | Large workspace policy; supplied session also contains additional L2 context |
| Installed OpenCode AGENTS.md | 7815 | Present/configured reference; native merged load not executed |
| Installed shared .agents/AGENTS.md | 7407 | Loading by each host UNKNOWN |
| Installed OpenCode primary role | 4431 | Role file, native parser not exercised |

## Measured skill-selection probes

| Request | Top3 names (scores) | rank latency ms | Selected metadata tokens |
|---|---|---|---|
| Apa prioritas yang harus aku kerjakan hari ini? | todolife-project-router(3), todolife-budget-tracker(2), todolife-core-tracker(2) | 163.427 | 0 |
| Bantu aku memahami materi ini dan buat latihan. | todolife-budget-tracker(1), todolife-core-tracker(1), todolife-daily-planner(1) | 159.462 | 0 |
| Cari penelitian terbaru dan bandingkan pendekatannya. | NO_MATCH | 160.027 | 0 |
| Audit repository ini dan jelaskan risikonya. | dependency-audit(6), secret-audit(5), security-ownership-map(3) | 158.253 | 235 |
| Buat roadmap belajar dari kemampuan yang aku miliki. | it-learning(3) | 157.724 | 0 |
| Lanjutkan workflow yang sebelumnya gagal. | tdd-workflow(5), gh-fix-ci(3), debugging(1) | 160.049 | 192 |
| Tunjukkan apa yang sudah berubah sejak review terakhir. | code-review(6), literature-review(6), literature-review-writer(6) | 171.544 | 255 |
| tolong gunakan playwright untuk portal | playwright(20), playwright-interactive(8), playwright-mcp-workflows(6) | 156.873 | 217 |

Local rank latency across this diagnostic sample: min=156.873ms; median=159.744ms; max=171.544ms; n=8. No p95 or confidence interval is inferred from one sample per distinct request. No before/after latency improvement is claimed.

`VERIFIED_RUNTIME`: Indonesian research request returns no skill; workflow recovery selects tdd-workflow; daily priority and learning-plan matches score below default auto-inject threshold4 and yield empty context. These are selector results; complete owner outcomes were not attempted. `confidence=1` means a maximum normalized relative score, including weak score1 matches, and is not an accuracy probability.

`VERIFIED_CODE`: build_relevant_skill_context loads metadata rather than complete bodies. XNINETZY_SKILL_AUTO_INJECT_MAX_CHARS=8000 is declared but unused by this builder at baseline. Repository text search finds the builder only in its definition and tests; actual runtime auto-injection wiring is NOT_VERIFIED. build_skill_prompt can enumerate all descriptions but has no discovered production caller.

## Coverage and acceptance status

| Dimension | Status | Evidence/limit |
|---|---|---|
| Direct skill YAML | VERIFIED_TEST | All125 direct files strict-parse; no blanket xfail |
| Canonical direct runtime parse | VERIFIED_TEST | 123 eligible;2 explicitly rejected legacy copies with valid canonical replacements |
| Nested skill compatibility | VERIFIED_RUNTIME | 43 total recursive runtime rejects incl root catalog, legacy copies, metadata and PPTX contracts |
| Skill reference completeness | UNKNOWN | Existing regex coverage is partial |
| 8 skill routing probes | VERIFIED_RUNTIME | Actual selector outputs above; no model synthesis |
| 50 curated golden tasks | NOT_EXECUTED | Do not claim end-to-end completion from8 probes |
| Cross-client parity | NOT_VERIFIED_IN_LIVE_ENVIRONMENT | Executables/configuration present; no native owner workflow executed |
| Prompt injection resistance | NOT_VERIFIED_IN_LIVE_ENVIRONMENT | Static prompt changes cannot prove model behavior or runtime authorization |
| Reasoning-tool latency gain | NOT_MEASURED | No controlled task comparison |
| Model token usage | NOT_MEASURED | Local text encoding only |
| Full context assembly latency | NOT_MEASURED | Only rank_skills measured |
| Host prompt install/sync | NOT_EXECUTED | Owner settings preserved |

## Implementation batch and follow-up

The focused skill tests were corrected to distinguish valid YAML from invalid historical names and fail new contract damage:14 passed,0 xfail; focused Ruff passed. This changes test honesty, not user-visible routing. See parent phase reports for the canonical prompt candidate and its own before/after results.

Next: define objective expected skill sets for multilingual daily planning/research/recovery tasks, then compare deterministic routing changes using held-out requests. Use existing domain services and metadata before adding embeddings, agents or databases. Validate privacy/isolation and host compatibility independently. Rollback: revert only the reviewed test/report patch; no data or host changes.

## Repository candidate comparison

Candidate files were tokenized after the parent implementation batch. Installed host files remain unchanged; these are candidate text-size comparisons, not measured runtime latency or billing savings. The canonical continuity file is newly repository-managed.

| Candidate file | Bytes | Lines | cl100k tokens | SHA-256 |
|---|---|---|---|---|
| docs/prompt-injection-core/CORE_PROMPT.md | 1959 | 32 | 353 | ab1e42b47b6b9eb2f1e321b41cae55cc07120b1c353ae6ce02238cf1534e4cfd |
| docs/prompt-injection-core/CORE_RULES.md | 6223 | 94 | 1035 | 1b4eadadbe0b1e864c5ffe4daa5dc574f1e2ecfa6e5d81d29d2650d4aed34984 |
| docs/prompt-injection-core/CLI_SHARED_INSTRUCTIONS.md | 1499 | 22 | 275 | 7f7804eb6b2314f889d12c6e9700ca2f9190b89c66b7f5d3dd3fe0e884da2997 |
| docs/prompt-injection-core/cli-overrides/codex-AGENTS.md | 970 | 15 | 198 | 5339b63d5c988a3c85a68b60ccef42bbc33619259893ce98bc7f3f73434abfac |
| docs/prompt-injection-core/cli-overrides/claude-CLAUDE.md | 815 | 13 | 177 | a0a3a9034c98a716e010806852f8ae73ef6e363780388f473195caf030036267 |
| docs/prompt-injection-core/cli-overrides/opencode-xninetzy-paksa.md | 821 | 13 | 172 | 7c60342054e4a21230a09019cf1ebf1c44fdcb9f93074b0698ad31b29b17f7c1 |

| Referenced composition | Installed baseline tokens | Candidate tokens | Text-size change |
|---|---|---|---|
| L0 + L1 + continuity + Codex L2 | 5268 | 1861 | -3407 (-64.7%) |
| L0 + L1 + continuity + Claude L2 | 5295 | 1840 | -3455 (-65.3%) |
| L0 + L1 + continuity + OpenCode L2 | 5217 | 1835 | -3382 (-64.8%) |

Candidate correction removes absolute host-override language, mandatory FIRST/LAST reasoning loops and universal prefix permission grants, and clarifies workflow customization cannot bypass security boundaries. Static integrity tests validate template/hash contracts; they do not demonstrate LLM prompt-injection resistance, native client parity or authorization behavior. Any active developer mandate in the current host session remains authoritative until changed through that host. Host installation requires a separate reviewed action preserving owner additions and backups.

## Continuation checks

Re-tokenization confirms the canonical Codex composition remains353+1035+275+198 = **1861 cl100k_base tokens**. Canonical hash validation passes; host instruction files are not installed/replaced. MCP connection repair candidates are separate from global prompt distribution: [client implementation](../implementation/CLIENT_CONNECTIONS.md) records eight compatible hosts/nine configuration entries and actual isolated transport probes. Native Claude health and Codex config parsing are verified; complete cross-client reasoning, routing, approval UI and outcome parity remain unverified.

The781-test continuation includes deterministic routing/registry checks, not781 labeled skill-selection tasks. Existing performance group now maps into software and all34 current groups have a canonical mapping; this does not fill the244 tool group-membership gaps or repair all multilingual skill routing. Model self-approval is refused even when a skill/output claims owner consent, but full prompt-injection resistance and trusted authorization across all paths remain open gates.
