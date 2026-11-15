# Capability and ownership matrix

November15 additions (`VERIFIED_TEST/RUNTIME`): pure anti-slop/output/readiness
checks work through MCP under default approval mode; they never authorize
submission. Opted-in MCP worker activation and FAISS restart/resync dedup pass
from source and a fresh frozen install. Both explicit hash256 and cached offline
MiniLM384 run on CPU. The three-node exact-title check is a smoke, not a semantic
benchmark.178 related tests pass. Owner worker activation, all-host native parity,
independent positive approval and golden-task outcome metrics remain unverified.

Date: 2026-11-10. This maps logical responsibilities onto current code. It does not introduce independently running agents. Unless noted, evidence is `VERIFIED_CODE`; a current source path is not evidence of a successful user journey.

Recovery update2026-11-15: controlled local process/MCP evidence is in [Phase3](../implementation/PHASE_3_REPORT.md). Earlier outcome gaps below remain open unless specifically superseded. The current installed minimal container is verified; live optional services and owner deployment remain separate gates.

| Logical responsibility | Current canonical implementation | Actual boundary | Verification status and next check |
|---|---|---|---|
| Primary coordination | MCP host plus `xninetzy/context/routing/`, `context/orchestrator/pipeline.py` | Host plans; routing/execution helpers are callable capabilities | `VERIFIED_CODE`; full bounded plan-execute-verify-resume user flow `UNKNOWN` |
| Research | `xninetzy/os/research/`, `tools/ecosystem/research_tools.py` | Light acquisition and deeper research session engines | `VERIFIED_CODE`; provider access and grounded synthesis live outcomes `NOT_VERIFIED_IN_LIVE_ENVIRONMENT` |
| Evidence verification | `xninetzy/os/knowledge/retrieval.py`, research citations, context evaluation | Deterministic evidence filters plus model-assisted synthesis where selected | `VERIFIED_CODE`; measured citation validity and independent task evaluation pending |
| Personal memory | `xninetzy/os/memory/` and existing lifecycle ecosystem tools | Canonical SQLite records; scoped owner search | `VERIFIED_CODE`; correction/supersession end-to-end pending |
| Knowledge/graph | `xninetzy/os/knowledge/`, `os/graph/v3/` | SQLite canonical truth, optional vector/graph projections | `VERIFIED_TEST` / `VERIFIED_RUNTIME`: local lease/revision fencing and real isolated Neo4j outage/retry/duplicate/delete pass; full owner reconciliation/live FAISS durability remain unverified |
| Adaptive learning | `xninetzy/domains/it_learning/` and `os/learning/` | Roadmaps, study sessions, mastery/recall helpers | `VERIFIED_CODE`; no scientifically validated learning improvement claimed |
| Academic assistance | `xninetzy/os/academic/` and validated academic skills | Institutional sessions and domain-specific approvals remain required | `VERIFIED_CODE`; no authentication, CAPTCHA solving, submission or live mutation performed |
| Life OS | `xninetzy/os/life/`, `os/inbox/`, `context/personal_os/`, ecosystem reducers | Canonical goals/tasks and event consumers | `VERIFIED_CODE`; realistic daily prioritization with fresh deadlines needs golden-task fixture |
| Career intelligence | `xninetzy/os/career/`, `domains/career/` | Opportunity acquisition, matching and evaluation helpers | `VERIFIED_CODE`; listing freshness/provider reliability not measured here |
| Software engineering | Native host coding tools, repository analysis/routing skills, existing internal tools | Authorized checkout only | `VERIFIED_TEST`: runtime root and telemetry regression fixes delivered locally |
| Security | `xninetzy/os/security/`, policy services and security skills | Explicit owner target scope; deterministic action boundaries | `VERIFIED_CODE` with synthetic policy/redaction reproductions; no unauthorized scanning performed |
| Artifacts | Existing document/tableau/media integrations and artifact skills | Canonical output policies and format validation | `VERIFIED_CODE`; no new generated user artifact claimed |
| Workflow recovery | `xninetzy/workflow/executor.py`, `store.py`, `tools.py`; separate harness/task records retained | Same-plan typed checkpoints in existing SQLite tables; cooperative local POSIX exclusion | `VERIFIED_TEST` / `VERIFIED_RUNTIME`: interrupted local recovery, preserved successful writes and installed-MCP resume; uncertain mutation held. Not universal external reconciliation |
| Controlled improvement | `xninetzy/os/lightning/`, `context/evaluation/`, `context/learning/` | Episode/reward/proposal records and offline evaluation helpers | `VERIFIED_TEST`: redacted RL event persistence; learned routing advantage `UNKNOWN` |

## Agentic maturity distinctions

| Category | Current evidence | Limit |
|---|---|---|
| Tool calling | Registry objects exposed through `mcp_tool_adapter` | Does not establish planning or successful user outcome |
| Deterministic orchestration | `WorkflowExecutor`, context invocation pipeline, event reducers; common MCP policy gateway | Existing engine owns ordered workflow steps; no general DAG scheduler or universal internal dispatch certification |
| LLM-assisted planning | Research and workflow planner modules | Live model behavior not evaluated in this audit |
| Durable workflow state | SQLite workflow checkpoints and action ledger; separate harness/task stores | Controlled actual process interruption/recovery passes; domain outcome verification and ambiguous external effects remain separate |
| Bounded autonomy | Stop/depth helpers and explicit high-tier CLI halt | Universal budgets and cancellation across every invocation not established |
| Multi-agent collaboration | Skills describe delegation; primary responsibility can be assigned by host | No benchmark advantage established; no new multi-agent runtime justified |

## Required acceptance scenarios

| Scenario | Existing building blocks | Missing verification |
|---|---|---|
| A: Daily operating system | Goals, tasks, inbox, personal context, review helpers | Fresh deadlines/dependencies, explainable ranking and user outcome |
| B: Research to knowledge | Research source registries, evidence/citations, ingestion | Live evidence validation, contradiction disclosure and authorized persistence |
| C: Adaptive learning | Roadmap, concept/recall and study session services | Prerequisite adaptation linked to actual practice outcomes |
| D: Development audit | Local source analysis, isolated tests and evidence-labelled findings | Full release/dependency/backup/clean-install checks remain pending |
| E: Workflow recovery | Existing workflow exact-plan/state/checkpoint and current policy | Controlled local restart/no duplicate completed effect verified; live domain reconciliation/backup/mixed-version rollout remain unverified |
| F: Memory correction | Owner-scoped update/retire and lifecycle tooling | Supersession/provenance retained and obsolete fact excluded in retrieval |
| G: Malicious evidence | Memory quarantine text, trusted principal injection, policy helpers | End-to-end injection fixtures across documents, skills, MCP outputs and memory |

## Implementation effect

The two local fixes change root-path resolution and secret handling, preserving tool signatures and SQLite schema. Tests verify corrected behavior; they do not establish cross-client parity, provider availability, academic integration safety or complete prompt-injection resistance. Rollback is selective restoration of the reviewed source/test hunks. Next priorities are policy integrity, truthful workflow state, projection recovery, then measured golden tasks. Do not add a dashboard, agent service or storage engine to address these gaps.

An additional minimal-install batch now verifies base-only installed-wheel bootstrap, all **571** registered tools exposed/listed, and actual local `datetime_now` output with AI, image, spreadsheet, embedding and graph extras absent. Mandatory `langchain-core` was promoted from the existing AI extra, and imports of optional provider/vision/spreadsheet dependencies moved into selected operations. Existing optional operations retain schemas and behavior; missing packages produce actionable extra-install errors. Combined import/provider/vision/spreadsheet regression: **34 passed**. Live optional integrations remain `NOT_VERIFIED_IN_LIVE_ENVIRONMENT`, and Docker startup remains a separate blocker.
