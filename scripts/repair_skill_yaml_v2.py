from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(".agents/skills")
OUT = Path("data/repaired_skills_v2")
FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def split_fm(text: str) -> tuple[str, str] | None:
    if text.startswith("---"):
        m = FM_RE.match(text)
        if m:
            return text[: m.end()], text[m.end():]
        fm_body_lines: list[str] = []
        rest_lines: list[str] = []
        in_fm = True
        saw_close = False
        for line in text.splitlines():
            if in_fm:
                if line.strip() in ("---", "..."):
                    if line.strip() == "---":
                        saw_close = True
                        in_fm = False
                        continue
                    if line.strip() == "...":
                        continue
                fm_body_lines.append(line)
            else:
                rest_lines.append(line)
        if saw_close:
            body = "\n".join(rest_lines)
            fm_text = "---\n" + "\n".join(fm_body_lines) + "\n---\n"
            return fm_text, body
    lines = text.splitlines()
    if not lines:
        return None
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start >= len(lines):
        return None
    first = lines[start].lstrip()
    if not (first and ":" in first and not first.startswith(("-", "*", "{"))):
        return None
    if lines[start].startswith((" ", "\t")):
        return None
    lines = lines[start:]
    close_idx = None
    scan_limit = min(len(lines), 500)
    for idx in range(1, scan_limit):
        ln = lines[idx].strip()
        if ln in ("---", "..."):
            close_idx = idx
            break
        if ln == "":
            continue
        if ln.startswith("# "):
            close_idx = idx
            break
        if not ln.startswith((" ", "\t", "-", "*")):
            key_only = ln.split(":", 1)[0].strip()
            if key_only and key_only.replace("_", "").replace("-", "").replace(" ", "").isalnum() and ":" in ln and not ln.endswith(":"):
                test_fm = "---\n" + "\n".join(lines[:idx]) + "\n---\n"
                try:
                    import yaml as _y
                    parsed = _y.safe_load(test_fm)
                    if isinstance(parsed, dict) and len(parsed) >= 2:
                        close_idx = idx
                        break
                except _y.YAMLError:
                    pass
                continue
            close_idx = idx
            break
    if close_idx is None:
        return None
    fm_body_lines = lines[:close_idx]
    rest_lines = lines[close_idx:]
    fm_text = "---\n" + "\n".join(fm_body_lines) + "\n---\n"
    body = "\n".join(rest_lines)
    return fm_text, body


def strip_p4_leading_doc_end(text: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=False)
    if not lines or lines[0].strip() != "---":
        return text, False
    out: list[str] = [lines[0]]
    i = 1
    changed = False
    while i < len(lines) and lines[i].strip() == "...":
        changed = True
        i += 1
    while i < len(lines):
        out.append(lines[i])
        i += 1
    if changed:
        return "\n".join(out) + ("\n" if text.endswith("\n") else ""), True
    return text, False


def strip_p5_mid_fence(fm_body: str) -> tuple[str, bool]:
    lines = fm_body.splitlines()
    if not lines:
        return fm_body, False
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line in ("---", "..."):
            if i == 0:
                i += 1
                continue
            del lines[i]
            changed = True
            continue
        i += 1
    if changed:
        return "\n".join(lines) + "\n", True
    return fm_body, False


def parse_frontmatter(fm_body: str) -> dict:
    lines = fm_body.splitlines()
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
        if line.lstrip().startswith("# ") or line.lstrip().startswith("## ") or line.lstrip().startswith("### "):
            break
        indent = len(line) - len(line.lstrip(" "))
        if indent != 0:
            i += 1
            continue
        if line.lstrip().startswith(("- ", "* ")):
            attach_idx = None
            for back in range(len(parsed) - 1, max(-1, len(parsed) - 4), -1):
                if parsed[back]["type"] == "scalar" and parsed[back]["value"] == "":
                    key_only = parsed[back]["key"]
                    if key_only.replace("_", "").replace("-", "").isalnum():
                        attach_idx = back
                        break
                    break
            if attach_idx is not None:
                parent_key = parsed[attach_idx]["key"]
                del parsed[attach_idx + 1 :]
                list_items: list[str] = [line]
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    if nxt.startswith((" ", "\t")):
                        break
                    if not nxt.lstrip().startswith(("- ", "* ")):
                        break
                    list_items.append(nxt)
                    j += 1
                parsed.append({"key": parent_key, "type": "list", "lines": list_items})
                i = j
                continue
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
            has_mapping_child = False
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
                    stripped_nxt = nxt.lstrip()
                    if stripped_nxt.startswith(("- ", "* ")):
                        has_list_child = True
                    elif ":" in stripped_nxt:
                        key_only = stripped_nxt.split(":", 1)[0].strip()
                        if key_only and key_only.replace("_", "").replace("-", "").isalnum():
                            has_mapping_child = True
                j += 1
            if child_count > 0:
                if has_list_child and has_mapping_child:
                    list_items: list[str] = []
                    map_lines: list[str] = []
                    for k in range(i + 1, j):
                        if not lines[k].strip():
                            continue
                        stripped_k = lines[k].lstrip()
                        if stripped_k.startswith(("- ", "* ")):
                            list_items.append(stripped_k[2:])
                        else:
                            map_lines.append(lines[k])
                    if list_items:
                        parsed.append({"key": key_name + "_items", "type": "list", "lines": ["  - " + it for it in list_items]})
                    if map_lines:
                        parsed.append({"key": key_name + "_meta", "type": "mapping", "lines": map_lines})
                    parsed.append({"key": key_name, "type": "scalar", "value": ""})
                elif has_list_child:
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
        if value_part.startswith("'") and not value_part.endswith("'") or (
            value_part.startswith("'")
            and value_part.count("'") % 2 == 1
        ):
            buf = [value_part]
            quote_open = True
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                leading = len(nxt) - len(nxt.lstrip(" "))
                if leading == 0:
                    break
                buf.append(nxt)
                if nxt.rstrip().endswith("'") and not nxt.rstrip().endswith("''"):
                    quote_open = False
                    j += 1
                    break
                j += 1
            joined_text = "\n  ".join(buf)
            joined_text = re.sub(r"\s+", " ", joined_text.replace("\n", " ")).strip()
            escaped = joined_text.replace("\\", "\\\\").replace('"', '\\"')
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
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        stripped = line.lstrip()
        leading = len(line) - len(stripped)
        if stripped.startswith(("- ", "* ")):
            item = stripped[2:].rstrip(":").rstrip().rstrip('"')
            result.setdefault("_items", []).append(item)
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        key_part, _, value_part = line.partition(":")
        key = key_part.strip()
        value = value_part.strip()
        if not value:
            j = i + 1
            child_indent = None
            child_lines: list[str] = []
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                child_leading = len(nxt) - len(nxt.lstrip(" "))
                if child_leading <= leading:
                    break
                if child_indent is None:
                    child_indent = child_leading
                if child_leading >= child_indent:
                    child_lines.append(nxt)
                else:
                    break
                j += 1
            if child_lines:
                sub = parse_simple_mapping(child_lines)
                if sub:
                        result[key] = sub
                else:
                    result[key] = ""
            else:
                result[key] = ""
            i = j
            continue
        if value.startswith('"') and value.endswith('"') and value.count('"') == 2:
            result[key] = value
        else:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            result[key] = f'"{escaped}"'
        i += 1
    return result


def rebuild(parsed: dict) -> str:
    out: list[str] = []
    for entry in parsed["_entries"]:
        key = entry["key"]
        if entry["type"] == "scalar":
            if entry["value"].startswith(("* ", "- ", "& ", "! ")):
                escaped = entry["value"].replace("\\", "\\\\").replace('"', '\\"')
                out.append(f'{key}: "{escaped}"')
            else:
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
                _emit_mapping(out, key, sub, indent=0)
    return "\n".join(out) + "\n"


def _emit_mapping(out: list[str], key: str, sub: dict, indent: int) -> None:
    prefix = "  " * indent
    items = sub.pop("_items", None) if "_items" in sub else None
    if items is not None:
        out.append(f"{prefix}{key}:")
        for it in items:
            escaped = it.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'{prefix}  - "{escaped}"')
        for sk, sv in sub.items():
            if isinstance(sv, dict):
                _emit_mapping(out, sk, sv, indent + 1)
            elif isinstance(sv, str) and sv.startswith(("- ", "* ", "& ", "! ")):
                out.append(f'{prefix}  {sk}: "{sv}"')
            else:
                out.append(f"{prefix}  {sk}: {sv}")
        return
    out.append(f"{prefix}{key}:")
    for sk, sv in sub.items():
        if isinstance(sv, dict):
            _emit_mapping(out, sk, sv, indent + 1)
        elif isinstance(sv, str) and sv.startswith(("- ", "* ", "& ", "! ")):
            out.append(f'{prefix}  {sk}: "{sv}"')
        else:
            out.append(f"{prefix}  {sk}: {sv}")


def repair_text(text: str) -> tuple[str | None, str]:
    text, p4 = strip_p4_leading_doc_end(text)
    parts = split_fm(text)
    if parts is None:
        return None, "no_frontmatter"
    fm_text, body = parts
    try:
        parsed_yaml = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        parsed_yaml = None
    if parsed_yaml is not None and isinstance(parsed_yaml, dict):
        return None, "already_ok"
    fm_body = fm_text[4:].rsplit("\n---", 1)[0]
    fm_body, p5 = strip_p5_mid_fence(fm_body)
    if p5:
        fm_text = "---\n" + fm_body + "---\n"
    parsed_struct = parse_frontmatter(fm_body)
    rebuilt_fm = rebuild(parsed_struct)
    test_doc = "---\n" + rebuilt_fm + "...\n"
    try:
        yaml.safe_load(test_doc)
    except yaml.YAMLError as exc:
        return None, f"still_broken: {str(exc)[:80]}"
    wrapped = "---\n" + rebuilt_fm + "...\n"
    return wrapped + body, "rebuilt"


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair SKILL.md YAML frontmatter (v2: P4/P5)")
    ap.add_argument("--dry-run", action="store_true", help="validate only, no writes")
    ap.add_argument("--inplace", action="store_true", help="write back to .agents/skills/")
    ap.add_argument("--target", help="repair one specific skill by name")
    args = ap.parse_args()

    out_root = ROOT if args.inplace else OUT
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