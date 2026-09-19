"""Repair YAML frontmatter in pre-existing broken SKILL.md files.

Writes repaired copies to `data/repaired_skills/<name>.md` (NOT directly to
`.agents/skills/`) because the in-session auto-linter hook re-damages
files immediately after every Write. Run from outside Claude Code to apply.

Handles 3 broken patterns:
  P1: `key: "value,` (unterminated quote) + bare continuation lines.
  P2: `key: >` (folded indicator) + bare continuation lines without indent.
  P3: `* item:` (list item with trailing colon) inside `metadata:` block.

Usage:
    python scripts/repair_skill_yaml.py                  # repair to data/repaired_skills/
    python scripts/repair_skill_yaml.py --inplace       # repair in-place (DANGEROUS, fights hook)
    python scripts/repair_skill_yaml.py --dry-run       # validate only, no writes
    python scripts/repair_skill_yaml.py --target NAME  # repair one specific skill
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(".agents/skills")
OUT = Path("data/repaired_skills")
FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def split_fm(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    m = FM_RE.match(text)
    if m:
        return text[: m.end()], text[m.end():]
    fm_body_lines: list[str] = []
    rest_lines: list[str] = []
    in_fm = True
    for line in text.splitlines():
        if in_fm:
            if line.strip() == "---":
                in_fm = False
                continue
            fm_body_lines.append(line)
        else:
            rest_lines.append(line)
    if in_fm:
        return None
    body = "\n".join(rest_lines)
    fm_text = "---\n" + "\n".join(fm_body_lines) + "\n---\n"
    return fm_text, body


def parse_frontmatter(fm_text: str) -> dict:
    lines = fm_text.splitlines()
    parsed: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("---"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent != 0:
            i += 1
            continue
        if line.lstrip().startswith("- "):
            i += 1
            continue
        key_part, _, value_part = line.partition(":")
        key_name = key_part.strip()
        value_part = value_part.strip()
        if not value_part:
            j = i + 1
            child_indent = None
            child_count = 0
            has_list_child = False
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                leading = len(nxt) - len(nxt.lstrip(" "))
                if leading == 0:
                    break
                if child_indent is None:
                    child_indent = leading
                if leading == child_indent:
                    child_count += 1
                    if nxt.lstrip().startswith(("- ", "* ")):
                        has_list_child = True
                j += 1
            if child_count > 0:
                if has_list_child:
                    parsed.append({"key": key_name, "type": "list", "lines": lines[i + 1 : j]})
                elif all(
                    lines[k].lstrip().startswith(("- ", "* "))
                    for k in range(i + 1, j)
                    if lines[k].strip()
                ):
                    parsed.append({"key": key_name, "type": "list", "lines": lines[i + 1 : j]})
                else:
                    parsed.append({"key": key_name, "type": "mapping", "lines": lines[i + 1 : j]})
            else:
                parsed.append({"key": key_name, "type": "scalar", "value": ""})
            i = j
            continue
        if value_part.startswith('"') and not value_part.endswith('"'):
            buf = [value_part.rstrip(",").rstrip().rstrip('"')]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                leading = len(nxt) - len(nxt.lstrip(" "))
                if leading == 0:
                    break
                if nxt.lstrip().startswith("- "):
                    break
                if ":" in nxt and nxt.split(":", 1)[0].strip().replace("-", "").replace("_", "").isalpha() and leading <= 2:
                    break
                buf.append(nxt.strip().rstrip(",").rstrip().rstrip('"'))
                j += 1
            joined = " ".join(p for p in buf if p)
            joined = re.sub(r"\s+", " ", joined).strip()
            escaped = joined.replace("\\", "\\\\").replace('"', '\\"')
            parsed.append({"key": key_name, "type": "scalar", "value": f'"{escaped}"'})
            i = j
            continue
        if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
            has_continuation = False
            for j_check in range(i + 1, len(lines)):
                nxt_check = lines[j_check]
                if not nxt_check.strip():
                    continue
                leading = len(nxt_check) - len(nxt_check.lstrip(" "))
                if leading == 0:
                    break
                if nxt_check.lstrip().startswith("- "):
                    break
                if ":" in nxt_check and nxt_check.split(":", 1)[0].strip().replace("-", "").replace("_", "").isalpha() and leading <= 2:
                    break
                has_continuation = True
                break
            if has_continuation:
                buf = [value_part.rstrip(",").rstrip().rstrip('"')]
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    leading = len(nxt) - len(nxt.lstrip(" "))
                    if leading == 0:
                        break
                    if nxt.lstrip().startswith("- "):
                        break
                    if ":" in nxt and nxt.split(":", 1)[0].strip().replace("-", "").replace("_", "").isalpha() and leading <= 2:
                        break
                    buf.append(nxt.strip().rstrip(",").rstrip().rstrip('"'))
                    j += 1
                joined = " ".join(p for p in buf if p)
                joined = re.sub(r"\s+", " ", joined).strip()
                escaped = joined.replace("\\", "\\\\").replace('"', '\\"')
                parsed.append({"key": key_name, "type": "scalar", "value": f'"{escaped}"'})
                i = j
                continue
            parsed.append({"key": key_name, "type": "scalar", "value": value_part})
            i += 1
            continue
        if value_part in (">", ">-", "|", "|-"):
            j = i + 1
            buf = []
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                leading = len(nxt) - len(nxt.lstrip(" "))
                if leading == 0:
                    break
                if leading < 2:
                    break
                buf.append(nxt.strip())
                j += 1
            joined = " ".join(buf)
            joined = re.sub(r"\s+", " ", joined).strip()
            escaped = joined.replace("\\", "\\\\").replace('"', '\\"')
            parsed.append({"key": key_name, "type": "scalar", "value": f'"{escaped}"'})
            i = j
            continue
        parsed.append({"key": key_name, "type": "scalar", "value": value_part})
        i += 1
    return {"_entries": parsed}


def parse_simple_mapping(lines: list[str]) -> dict:
    result: dict = {}
    for line in lines:
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped.startswith(("- ", "* ")):
            item = stripped[2:].rstrip(":").rstrip().rstrip('"')
            result.setdefault("_items", []).append(item)
            continue
        if ":" not in stripped:
            continue
        key_part, _, value_part = line.partition(":")
        key = key_part.strip()
        value = value_part.strip()
        if value.startswith('"') and value.endswith('"') and value.count('"') == 2:
            result[key] = value
        elif value:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            result[key] = f'"{escaped}"'
        else:
            result[key] = ""
    return result


def rebuild(parsed: dict) -> str:
    out: list[str] = []
    for entry in parsed["_entries"]:
        key = entry["key"]
        if entry["type"] == "scalar":
            out.append(f"{key}: {entry['value']}")
        elif entry["type"] == "list":
            for ln in entry.get("lines", []):
                stripped = ln.lstrip()
                if stripped.startswith(("- ", "* ")):
                    item = stripped[2:].rstrip(":").rstrip().rstrip('"')
                    escaped = item.replace("\\", "\\\\").replace('"', '\\"')
                    out.append(f'  - "{escaped}"')
        elif entry["type"] == "mapping":
            sub = parse_simple_mapping(entry["lines"])
            if sub:
                if "_items" in sub:
                    items = sub.pop("_items")
                    out.append(f"{key}:")
                    for it in items:
                        escaped = it.replace("\\", "\\\\").replace('"', '\\"')
                        out.append(f'  - "{escaped}"')
                else:
                    out.append(f"{key}:")
                for sk, sv in sub.items():
                    out.append(f"  {sk}: {sv}")
    return "\n".join(out) + "\n"


def repair_text(text: str) -> tuple[str | None, str]:
    parts = split_fm(text)
    if parts is None:
        return None, "no_frontmatter"
    fm_text, body = parts
    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        pass
    else:
        if parsed is not None:
            return None, "already_ok"
    fm_body = fm_text[4:].rsplit("\n---", 1)[0]
    parsed_struct = parse_frontmatter(fm_body)
    rebuilt_fm = rebuild(parsed_struct)
    try:
        yaml.safe_load(rebuilt_fm)
    except yaml.YAMLError as exc:
        return None, f"still_broken: {str(exc)[:80]}"
    wrapped = "---\n" + rebuilt_fm + "...\n"
    return wrapped + body, "rebuilt"


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair SKILL.md YAML frontmatter")
    ap.add_argument("--dry-run", action="store_true", help="validate only, no writes")
    ap.add_argument("--inplace", action="store_true", help="write back to .agents/skills/ (fights linter hook)")
    ap.add_argument("--target", help="repair one specific skill by name")
    args = ap.parse_args()

    if args.inplace:
        out_root = ROOT
    else:
        out_root = OUT

    if out_root is OUT:
        out_root.mkdir(parents=True, exist_ok=True)

    if args.target:
        targets = [ROOT / args.target / "SKILL.md"]
    else:
        targets = sorted(ROOT.glob("*/SKILL.md"))

    fixed = 0
    skipped = 0
    failed: list[tuple[str, str]] = []
    for sm in targets:
        if not sm.exists():
            print(f"MISSING: {sm}")
            continue
        text = sm.read_text(encoding="utf-8")
        repaired_text, msg = repair_text(text)
        if msg == "already_ok":
            if not args.inplace:
                shutil.copy(sm, out_root / sm.parent.name / "SKILL.md")
            skipped += 1
            continue
        if repaired_text is None:
            failed.append((sm.parent.name, msg))
            print(f"FAILED:  {sm.parent.name} -- {msg}")
            continue
        if args.dry_run:
            print(f"DRY-OK:  {sm.parent.name}")
            fixed += 1
            continue
        target_path = out_root / sm.parent.name / "SKILL.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(repaired_text, encoding="utf-8")
        fixed += 1
        print(f"wrote:   {target_path}")

    print(f"\nfixed {fixed}, skipped {skipped} (already ok), failed {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
