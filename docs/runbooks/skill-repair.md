# Runbook — Repairing SKILL.md YAML Frontmatter

## Symptom

`tests/governance/test_skill_frontmatter.py::test_skill_catalog_yaml_parses` xfails with:

> YAML frontmatter damage in N of M skill(s): [...]. Root cause: Claude Code auto-linter hook re-damages repaired files.

`from xninetzy.skills.registry import list_skills` returns only 1 skill (`audit-test`); 69 skills are silently skipped.

## Root cause

A Claude Code auto-linter hook (in `~/.claude/settings.json`, **user-global — not in this repo**) re-damages YAML frontmatter in `.agents/skills/*/SKILL.md` files every time a `Write` lands on that path. The hook fires on both the `Write`/`Edit` tools AND shell writes (`cp`, `tee`), so the damage happens within milliseconds of any write attempt.

This repo **cannot disable the hook from inside a Claude Code session**. The fix must run outside the session.

## Repair procedure (run OUTSIDE Claude Code)

1. **Validate first**:
   ```bash
   python scripts/repair_skill_yaml.py --dry-run
   ```
   Reports parseable vs broken files without writing anything.

2. **Repair to staging** (default writes to `data/repaired_skills/`, NOT `.agents/skills/`):
   ```bash
   python scripts/repair_skill_yaml.py
   ```
   Output: `data/repaired_skills/<name>/SKILL.md` for each repairable skill.

3. **Review the diff**:
   ```bash
   diff -r .agents/skills data/repaired_skills
   ```
   Inspect any unexpected structural changes.

4. **Copy repaired files into place** (shell `cp` from outside any Claude Code session):
   ```bash
   for d in data/repaired_skills/*/SKILL.md; do
     name=$(basename "$(dirname "$d")")
     cp -f "$d" ".agents/skills/$name/SKILL.md"
   done
   ```

5. **Verify the catalog parses**:
   ```bash
   uv run pytest tests/governance/test_skill_frontmatter.py::test_skill_catalog_yaml_parses -v
   ```
   The test will still `xfail` until step 6 lands.

6. **Remove the xfail and convert to a hard assert** in `tests/governance/test_skill_frontmatter.py`:
   - Delete the `if broken: pytest.xfail(...)` block.
   - Replace with `assert not broken, f"YAML still broken in: {broken}"`.
   - Commit as `fix(test): enforce skill YAML catalog (Refs ISS-20260919-01)`.

7. **Run the full governance suite** to confirm no regressions:
   ```bash
   uv run pytest tests/governance/ -v
   ```

## In-session safety

**Do NOT call `Write` on `.agents/skills/*/SKILL.md` from inside Claude Code.** The hook will re-damage the file within milliseconds of the write — the file will look fine when you stop writing and broken again by the next test run.

If you must write a SKILL.md from inside Claude Code:
- Write to `data/repaired_skills/<name>/SKILL.md` first.
- Copy it into `.agents/skills/<name>/SKILL.md` via `Bash` `cp` after exiting the Claude Code session.

## Patterns repaired

From `scripts/repair_skill_yaml.py` docstring (the script handles 3 known broken patterns):

- **P1** — `key: "value,` (unterminated quote) + bare continuation lines on subsequent non-blank lines.
- **P2** — `key: >` (folded block indicator) + bare continuation lines without proper indentation.
- **P3** — `- item:` (list item with trailing colon) inside a `metadata:` block.

The hand-rolled parser in `scripts/repair_skill_yaml.py:55-200` detects each pattern and emits valid YAML. Files with deeply damaged nested structures (flattened indentation, orphan fences) cannot be auto-repaired — these need manual editing.

## Verifying the fix is permanent

Once `test_skill_catalog_yaml_parses` passes (after step 6), the catalog is restored. To prevent regression:

- Add a CI job that runs `uv run pytest tests/governance/test_skill_frontmatter.py` on every PR.
- Re-run the repair script after any large batch of SKILL.md edits.

## Related

- `KNOWN_ISSUES.md` — ISS-20260919-01 (CRITICAL, BLOCKED)
- `scripts/repair_skill_yaml.py` — the repair tool
- `xninetzy/skills/registry.py` — the YAML loader (`FRONTMATTER_PATTERN`, `_yaml_load_tolerant`, `_to_folded_block_scalars`)
