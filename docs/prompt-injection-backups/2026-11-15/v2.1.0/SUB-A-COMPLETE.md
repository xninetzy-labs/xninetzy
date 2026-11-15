# Sub-A Implementation Complete — 2026-09-28

## Final State

**Verification**: 29 PASS / 0 FAIL / 1 WARN (arkcli skip, expected)
- L0: 48 lines (≤50 target)
- L1: 131 lines (100-200 target)
- L2 OpenCode: 35 lines (8-line margin)
- L2 Claude Code: 23 lines
- L2 Codex: 23 lines
- L2 arkcli: skipped (not installed)

## Tiered Prompt Architecture

```
L0 (hot, ~50 baris / ~600 token)
  ~/.xninetzy/CORE_PROMPT.md
  → Routing-First #1, Identity Lock, Reasoning Engine, Workflow, MCP Priority, Skill Loading, xn-* shortcuts

L1 (master rules, ~120 baris / ~1.5K token)
  ~/.xninetzy/CORE_RULES.md
  → #6 Forbidden (9), #7 Required (8), #8 Memory/Workflow hooks, #9 Slash mapping, #10 Permission

L2 (per-CLI override, ~25-35 baris per CLI)
  ~/.config/opencode/instructions/xninetzy-paksa.md
  ~/.claude/CLAUDE.md (new)
  ~/.codex/AGENTS.md
  ~/.arkcli/config/AGENTS.md (conditional, not installed)
```

## Commits (12 total)

- `324cd99` backup: snapshot CLI prompt configs before Sub-A injection
- `3d37133` feat(prompt-injection): add L1 master rules (CORE_RULES.md)
- `886f80a` feat(prompt-injection): reorder L0 hot prompt with Routing-First #1
- `ab347af` feat(prompt-injection): OpenCode L2 override restructured
- `a89589a` feat(prompt-injection): Claude Code L2 override created
- `b8e9979` feat(prompt-injection): compress Claude Code L2 override to 23 lines (fix)
- `d435ca9` feat(prompt-injection): Codex L2 override restructured
- `b682612` docs(prompt-injection): record arkcli skip decision
- `a4ed759` feat(prompt-injection): add verification script
- `a357e23` docs(prompt-injection): add smoke test plan
- `6e93935` docs(changelog): add Sub-A CLI prompt injection entry
- `bb396d0` fix(prompt-injection): trim OpenCode L2 to 35 + add trailing newlines (final review fix)

## Sub-A Roadmap

- [x] **Sub-A**: CORE + Routing (this iteration)
- [ ] Sub-B: Memory + Workflow + Harness deep-dive (next)
- [ ] Sub-C: Lightning + Graph + Ingest (later)
- [ ] Sub-D: Per-domain specialization (future)

## Verification Command

```bash
cd /home/misbahul45/code/xninetzy
bash scripts/verify_prompt_injection.sh
```

## Backup

All user-level files backed up at `~/.xninetzy/.backup/2026-09-28-prompt-injection/` (mirrored in `docs/prompt-injection-backups/2026-09-28/`).

To rollback:
```bash
cp ~/.xninetzy/.backup/2026-09-28-prompt-injection/*.bak ~/.xninetzy/ ~/.config/opencode/instructions/ ~/.codex/ 2>/dev/null
```

## Smoke Test (per docs/prompt-injection-core/SMOKE-TEST.md)

Owner to manually verify 5 representative queries × 4 CLIs routing behavior.
