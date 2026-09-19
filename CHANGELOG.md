# Changelog — Xninetzy

Format: [Keep a Changelog 1.1](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

## [2.2.0] — 2026-09-11 — MCP-only pivot

### Removed
- Baileys WhatsApp engine
- Ink CLI
- LangGraph conversational agent loop
- `services/ai`, `services/wa-enggine`, `services/cli` (compose stack)
- Pre-pivot OS implementation progress doc (archived to `docs/archive/2026-09-11/`)

### Added
- Lightning RL bandit service (`xninetzy/os/lightning/`, 15 `lightning_*` tools)
- MCP resources and prompts (`xninetzy/interfaces/mcp_server.py`: 2 resources + 1 prompt)
- `redact_secrets` taxonomy (`xninetzy/core/security.py`, 8 patterns)
- `<memory_quarantine>` fence in `format_memories_for_prompt` (`xninetzy/os/memory/memory_store.py`)
- PyPI Trusted Publishing via OIDC (`.github/workflows/publish.yml`)
- Career Intelligence domain (17 tools in `xninetzy/tools/ecosystem/career_tools.py`, 19 skill bodies)
- Governance tests: `tests/governance/test_no_comments.py`,
  `tests/governance/test_skill_frontmatter.py`,
  `tests/governance/test_mcp_surface.py`

### Changed
- Architecture boundary: domain modules must never import `httpx`, `fastapi`, or MCP primitives
- RiskClass taxonomy: READ/DRAFT/WRITE/FINAL enforced via `xninetzy/os/policy/action_policy.py`
- FINAL tool whitelist: `hebat_upload_submission`, `portal_krs_war_arm`, `qa_fill_kuesioner`
  (drift detection in `tests/governance/test_mcp_surface.py`)

### Known issues
- ISS-20260919-01: SKILL.md YAML damage (CRITICAL, BLOCKED by hook — see `KNOWN_ISSUES.md`)

## [Unreleased]

### Documentation
- New: `KNOWN_ISSUES.md`, `CHANGELOG.md`, `ISSUE_TEMPLATE.md`
- New: `docs/runbooks/skill-repair.md`, `docs/SKILLS_INDEX.md`
- Archived: `docs/progress/XNINETZY_OS_IMPLEMENTATION_PROGRESS.md`,
  `docs/plan/phase_1_shared_contracts_goal.md`
- Banner-stripped: `docs/AI_PROVIDERS_CODING_AGENTS_MCP.md`
- Fixed: `CLAUDE.md` count drift (§6: 36→70, §7f: 14→19)
- Fixed: `CLAUDE.md` domain-creep contradiction (L22-23)
