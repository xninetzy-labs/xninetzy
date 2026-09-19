# Known Issues — Xninetzy v2.2.0

> Authoritative tracker for defects that block correctness, security, or core UX.
> Each issue has an ID (`ISS-YYYYMMDD-NN`), severity, owner, status, and resolution pointer.

## Index

| ID | Title | Severity | Status | Owner |
|---|---|---|---|---|
| ISS-20260919-01 | SKILL.md YAML frontmatter damage (69/69 files) | CRITICAL | BLOCKED (hook) | tooling |
| ISS-20260919-02 | `repair_skill_yaml.py` undocumented + no runbook | HIGH | RESOLVED | tooling |
| ISS-20260919-03 | CLAUDE.md §6 skill count drift (36 vs 70) | HIGH | RESOLVED | docs |
| ISS-20260919-04 | CLAUDE.md §7f career skill count drift (14 vs 19) | LOW | RESOLVED | docs |
| ISS-20260919-05 | "7-layer memory stack" claim — location unverified | LOW | CLOSED-NOOP | docs |
| ISS-20260919-06 | Stale pre-pivot docs reference removed services | HIGH | RESOLVED | docs |
| ISS-20260919-07 | Domain-creep contradiction (CLAUDE.md §1 vs §7f) | MEDIUM | RESOLVED | docs |
| ISS-20260919-08 | `redact_secrets` taxonomy not in `SECURITY.md` | MEDIUM | OPEN | security |
| ISS-20260919-09 | MCP resources/prompts added but not documented | LOW | OPEN | docs |
| ISS-20260919-10 | CAPTCHA OCR cooldown not mirrored in `SECURITY.md` | LOW | OPEN | security |

## ISS-20260919-01 — SKILL.md YAML damage
**Severity:** CRITICAL — gates the skill catalog.
**Status:** BLOCKED by Claude Code auto-linter hook in `~/.claude/settings.json` (user-global, not project-local).
**Workaround:** `docs/runbooks/skill-repair.md` — run `python scripts/repair_skill_yaml.py` OUTSIDE Claude Code, then shell-copy repaired files into `.agents/skills/`.
**Repair script:** `scripts/repair_skill_yaml.py` (3-pattern coverage: P1 unterminated quote, P2 folded indicator, P3 list item with trailing colon).
**Verification:** `tests/governance/test_skill_frontmatter.py::test_skill_catalog_yaml_parses` (currently xfails).

## ISS-20260919-02 — Repair tool undocumented
**Severity:** HIGH.
**Status:** RESOLVED via runbook at `docs/runbooks/skill-repair.md` + cross-refs from `CLAUDE.md` and `README.md`.
**Verification:** `grep -rn "skill-repair" CLAUDE.md README.md`.

## ISS-20260919-03 — CLAUDE.md §6 skill count drift
**Severity:** HIGH.
**Old:** "36 built-in skills cover the project's MCP surface".
**New:** "70 built-in skill files (69 skill directories + 1 top-level SKILL.md) cover the project's MCP surface".
**Verification:** `grep -n "70 built-in" CLAUDE.md`.

## ISS-20260919-04 — CLAUDE.md §7f career skill count drift
**Severity:** LOW.
**Old:** "Skill bodies: 14 under `.agents/skills/career/`".
**New:** "Skill bodies: 19 under `.agents/skills/career/`".
**Verification:** `grep -n "Skill bodies: 19" CLAUDE.md`.

## ISS-20260919-05 — "7-layer memory stack" claim
**Severity:** LOW.
**Status:** CLOSED-NOOP. Grep across `xninetzy/`, `docs/`, `README.md`, `CLAUDE.md`, `AGENTS.md`, `SECURITY.md` returned zero hits. The claim lived in a prior session memory file (auto-generated, not in repo). `xninetzy/os/memory/` actually contains 3 files (`chat_store.py`, `memory_store.py`, `memory_tools.py`) — no 7-layer stack ever shipped.

## ISS-20260919-06 — Stale pre-pivot docs
**Severity:** HIGH.
**Files moved to `docs/archive/2026-09-11/`:**
- `docs/progress/XNINETZY_OS_IMPLEMENTATION_PROGRESS.md` (15+ Baileys/LangGraph refs)
- `docs/plan/phase_1_shared_contracts_goal.md` (L8 references WhatsApp/CLI/LangGraph)
**Banner-stripped:** `docs/AI_PROVIDERS_CODING_AGENTS_MCP.md` (post-pivot banner prepended).
**Verification:** `ls docs/archive/2026-09-11/` shows the two moved files.

## ISS-20260919-07 — Domain-creep contradiction
**Severity:** MEDIUM.
**Old:** "Xninetzy is a single-purpose MCP server ... exposing many sibling domains (Research, Career, Business, AI, ...)".
**New:** "Xninetzy is a single-purpose MCP server ... exposing tool groups defined by `xninetzy/tools/registry.py` (the sibling-domain phrasing in §7f refers to historical pre-pivot wording)".
**Verification:** `grep -n "many sibling" CLAUDE.md` empty.

## ISS-20260919-08 — `redact_secrets` taxonomy not in SECURITY.md
**Severity:** MEDIUM.
**Status:** OPEN — pending Phase B (B13).

## ISS-20260919-09 — MCP resources/prompts undocumented
**Severity:** LOW.
**Status:** OPEN — pending Phase C (C17).

## ISS-20260919-10 — CAPTCHA OCR cooldown not mirrored
**Severity:** LOW.
**Status:** OPEN — pending Phase B (B15).

## How to file

1. Pick next ID: `ISS-YYYYMMDD-NN` (NN is zero-padded sequence per day).
2. Add a row to the index table at the top of this file.
3. Add a section below the table with severity, status, owner, verification pointer.
4. Reference the ID in commit messages: `Refs ISS-YYYYMMDD-NN`.
5. Move status through `OPEN` → `IN_PROGRESS` → `BLOCKED` / `RESOLVED` → `CLOSED`.
6. For `BLOCKED` issues, document the blocker in the section body (not just the table).
