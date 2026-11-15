# CLI Prompt Injection — Smoke Test Plan

**Date:** 2026-09-28
**Spec:** docs/superpowers/specs/2026-09-28-cli-prompt-injection-core-routing-design.md

## Test Queries

For each query below, run in each CLI (OpenCode, Claude Code, Codex, arkcli)
and verify the expected routing behavior.

### Query 1: Academic

**Input:** "Bantu saya kerjakan tugas HEBAT hari ini"

**Expected:**
- Agent invokes `xninetzy_skill_suggest_for_request` FIRST
- Top match: `hebat-academic` or `xninetzy-hebat`
- Follows skill procedure (input → evidence → structure)
- Uses `xninetzy_hebat_*` MCP tools

### Query 2: Coding

**Input:** "Cari bug di function X"

**Expected:**
- Agent invokes `xninetzy_skill_suggest_for_request` FIRST
- Top match: `debugging` or `systematic-debugging`
- Uses `codebase-memory-mcp` for code discovery

### Query 3: Security

**Input:** "Audit SAST pada repo ini"

**Expected:**
- Agent invokes `xninetzy_skill_suggest_for_request` FIRST
- Top match: `security-review` or `xninetzy-security-testing`
- Uses `xninetzy_security_sast` MCP tool

### Query 4: Career

**Input:** "Cari lowongan backend remote"

**Expected:**
- Agent invokes `xninetzy_skill_suggest_for_request` FIRST
- Top match: `job-discovery` or `job-search`
- Uses `xninetzy_career_search_jobs` MCP tool

### Query 5: Life OS

**Input:** "Buat daily plan hari ini"

**Expected:**
- Agent invokes `xninetzy_skill_suggest_for_request` FIRST
- Top match: `todolife-daily-planner` or `personal-os`
- Uses `xninetzy_life_dashboard` MCP tool

## Verification Matrix

| CLI | Query 1 | Query 2 | Query 3 | Query 4 | Query 5 |
|-----|---------|---------|---------|---------|---------|
| OpenCode | ☐ | ☐ | ☐ | ☐ | ☐ |
| Claude Code | ☐ | ☐ | ☐ | ☐ | ☐ |
| Codex | ☐ | ☐ | ☐ | ☐ | ☐ |
| arkcli | ☐ | ☐ | ☐ | ☐ | ☐ |

## Notes

- Manual smoke test required because automated routing behavior is LLM-dependent.
- If a query fails to route correctly, investigate: (a) skill catalog, (b)
  MCP tool availability, (c) L2 override permission map.
- All tests should pass before Sub-A is considered complete.
