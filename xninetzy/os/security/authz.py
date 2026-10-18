from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OWNERSHIP = ("own", "linked", "foreign", "anonymous")
ANONYMOUS_ROLE = "ANONYMOUS"
DEFAULT_GUARD_PATTERN = r"assertFixtureDatabase|isTestDatabase|assertTestDatabase|guard_test_database"
SENSITIVE_OPERATION = re.compile(r"role|permission|privilege|admin|delete|remove|password|token|impersonat|grant|revoke", re.IGNORECASE)
_TYPE_HEADER = re.compile(r"^\s*(?:extend\s+)?type\s+(Query|Mutation|Subscription)\b[^{]*\{", re.MULTILINE)
_FIELD = re.compile(r"^\s*(\w+)\s*(\((?:[^()]|\([^()]*\))*\))?\s*:\s*([\w\[\]!]+)([^\n]*)", re.MULTILINE)
_ID_ARG = re.compile(r"\b\w*(?:id|ids)\b\s*:", re.IGNORECASE)
_ROLE_WRITE = re.compile(
    r"\b(?:role|roles|isSuperAdmin|is_superuser|is_admin|permissions?|capabilit\w*|privilege\w*)\b\s*(?::|\+=|=(?!=))"
    r"|\b(?:setRole|assignRole|grantRole|set_role|assign_role)\b",
    re.IGNORECASE,
)
_TYPE_DECL = re.compile(r"^\s*(?:readonly\s+)?\w+\??\s*:\s*[A-Za-z_][\w\[\]<>|\"' ]*;\s*$")
_GUARD = re.compile(
    r"\b(?:(?:require|assert|ensure|check|verify)\w*(?:Role|Admin|SuperAdmin|Permission|Auth|Access|Privilege)\w*"
    r"|hasRole|canAssign\w*|authorize\w*|guard\w*|is_super_admin|isSuperAdmin)\b",
    re.IGNORECASE,
)
_FUNC_HEADERS = (
    re.compile(r"\bfunction\s+(\w+)\s*\("),
    re.compile(r"\bdef\s+(\w+)\s*\("),
    re.compile(r"^\s*(\w+)\s*:\s*(?:async\s*)?(?:function\b|\()"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function\b|\()"),
    re.compile(r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\{\s*$"),
)
_NOT_FUNCTIONS = frozenset({"if", "for", "while", "switch", "catch", "function", "return", "else", "with"})
_SOURCE_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".py"})
_SKIP_DIRS = frozenset({".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next"})
_TEST_MARKERS = ("__tests__", "tests", "test", "fixtures", "__mocks__")
MAX_FILES = 3000
MAX_FILE_BYTES = 1_000_000


@dataclass(slots=True)
class Operation:
    kind: str
    name: str
    args: list[str]
    returns: str
    object_scoped: bool
    sensitive: bool


def _block(text: str, open_index: int) -> str:
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:i]
    return text[open_index + 1:]


def parse_sdl(text: str) -> list[Operation]:
    operations: list[Operation] = []
    for match in _TYPE_HEADER.finditer(text):
        body = _block(text, match.end() - 1)
        cleaned = re.sub(r'""".*?"""', "", body, flags=re.DOTALL)
        cleaned = "\n".join(line for line in cleaned.splitlines() if not line.strip().startswith("#"))
        for field in _FIELD.finditer(cleaned):
            raw_args = field.group(2) or ""
            args = [a.strip() for a in raw_args.strip("()").split(",") if a.strip()]
            name = field.group(1)
            operations.append(Operation(
                kind=match.group(1).lower(),
                name=name,
                args=args,
                returns=field.group(3),
                object_scoped=bool(_ID_ARG.search(raw_args)),
                sensitive=bool(SENSITIVE_OPERATION.search(name)),
            ))
    return operations


def parse_openapi(data: dict[str, Any]) -> list[Operation]:
    operations: list[Operation] = []
    for path, methods in (data.get("paths") or {}).items():
        for method, spec in (methods or {}).items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            name = str((spec or {}).get("operationId") or f"{method.upper()} {path}")
            operations.append(Operation(
                kind="query" if method.lower() == "get" else "mutation",
                name=name,
                args=[str(p.get("name")) for p in (spec or {}).get("parameters") or []],
                returns="",
                object_scoped="{" in path,
                sensitive=bool(SENSITIVE_OPERATION.search(name + path)),
            ))
    return operations


def build_matrix(operations: list[Operation], roles: list[str], selected: list[str] | None = None) -> list[dict[str, Any]]:
    wanted = {name for name in (selected or [])}
    rows: list[dict[str, Any]] = []
    for op in operations:
        if wanted and op.name not in wanted:
            continue
        ownerships = OWNERSHIP[:3] if op.object_scoped else ("n/a",)
        for role in [*roles, ANONYMOUS_ROLE]:
            cases = ("anonymous",) if role == ANONYMOUS_ROLE and op.object_scoped else ownerships
            for ownership in cases:
                rows.append({
                    "role": role,
                    "operation": op.name,
                    "kind": op.kind,
                    "ownership": ownership,
                    "sensitive": op.sensitive,
                    "expected": None,
                })
    return rows


def render_bun_skeleton(rows: list[dict[str, Any]]) -> str:
    lines = ['import { describe, test } from "bun:test";', "", 'describe("authorization matrix", () => {']
    by_operation: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_operation.setdefault(row["operation"], []).append(row)
    for operation, cases in by_operation.items():
        lines.append(f'  describe("{operation}", () => {{')
        for case in cases:
            lines.append(f'    test.todo("{case["role"]} / {case["ownership"]}");')
        lines.append("  });")
    lines.append("});")
    return "\n".join(lines) + "\n"


def render_pytest_skeleton(rows: list[dict[str, Any]]) -> str:
    cases = ",\n".join(f'    ("{r["role"]}", "{r["operation"]}", "{r["ownership"]}")' for r in rows)
    return (
        "import pytest\n\n"
        f"MATRIX = [\n{cases},\n]\n\n\n"
        '@pytest.mark.parametrize("role,operation,ownership", MATRIX)\n'
        '@pytest.mark.skip(reason="expected outcome not filled")\n'
        "def test_authorization_matrix(role, operation, ownership):\n"
        "    raise NotImplementedError\n"
    )


def find_test_db_guard(project_root: Path, pattern: str = DEFAULT_GUARD_PATTERN) -> list[str]:
    compiled = re.compile(pattern)
    found: list[str] = []
    for path in _source_files(project_root, include_tests=True):
        try:
            if compiled.search(path.read_text(encoding="utf-8", errors="replace")):
                found.append(str(path.relative_to(project_root)))
        except OSError:
            continue
        if len(found) >= 5:
            break
    return found


def _is_test_path(rel: Path) -> bool:
    parts = rel.parts
    if any(part in _TEST_MARKERS for part in parts[:-1]):
        return True
    return bool(re.search(r"(?:^test_|_test\.|\.test\.|\.spec\.)", parts[-1]))


def _source_files(root: Path, include_tests: bool) -> list[Path]:
    files: list[Path] = []
    stack = [root]
    while stack and len(files) < MAX_FILES:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in _SKIP_DIRS:
                    stack.append(entry)
            elif entry.suffix.lower() in _SOURCE_SUFFIXES and entry.stat().st_size <= MAX_FILE_BYTES:
                if include_tests or not _is_test_path(entry.relative_to(root)):
                    files.append(entry)
    return sorted(files)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _enclosing_function(lines: list[str], index: int) -> tuple[int, int, str] | None:
    limit = _indent(lines[index])
    for j in range(index - 1, -1, -1):
        line = lines[j]
        if not line.strip() or _indent(line) >= limit:
            continue
        for header in _FUNC_HEADERS:
            match = header.search(line)
            if match and match.group(1) not in _NOT_FUNCTIONS:
                return j, _block_end(lines, j), match.group(1)
        limit = _indent(line)
    return None


def _block_end(lines: list[str], start: int) -> int:
    base = _indent(lines[start])
    is_python = lines[start].lstrip().startswith(("def ", "async def "))
    for k in range(start + 1, len(lines)):
        line = lines[k]
        if not line.strip():
            continue
        if _indent(line) <= base:
            if is_python:
                return k - 1
            if line.lstrip().startswith(("}", ")")):
                return k
            if _indent(line) < base:
                return k - 1
    return len(lines) - 1


def _guards(lines: list[str], start: int, end: int) -> list[str]:
    found: set[str] = set()
    for line in lines[start:end + 1]:
        for match in _GUARD.finditer(line):
            token = match.group(0)
            if token.lower() in {"issuperadmin", "is_super_admin"} and _ROLE_WRITE.search(line):
                continue
            found.add(token.lower())
    return sorted(found)


def scan_role_paths(root: Path, include_tests: bool = False) -> list[dict[str, Any]]:
    paths: dict[tuple[str, str], dict[str, Any]] = {}
    for file in _source_files(root, include_tests):
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith(("//", "#", "*", "/*")):
                continue
            if not _ROLE_WRITE.search(line) or _TYPE_DECL.match(line):
                continue
            func = _enclosing_function(lines, index)
            if func is None:
                continue
            start, end, name = func
            key = (str(file.relative_to(root)), name)
            if key in paths:
                continue
            paths[key] = {
                "file": key[0],
                "line": index + 1,
                "function": name,
                "write": line.strip()[:120],
                "guards": _guards(lines, start, end),
            }
    ordered = sorted(paths.values(), key=lambda p: (p["file"], p["line"]))
    return _classify(ordered)


def _classify(paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for path in paths:
        mine = set(path["guards"])
        weaker: list[str] = []
        differs: list[str] = []
        for other in paths:
            if other is path:
                continue
            theirs = set(other["guards"])
            if mine < theirs:
                weaker.append(other["function"])
            elif mine != theirs and mine - theirs and theirs - mine:
                differs.append(other["function"])
        path["weaker_than"] = sorted(set(weaker))
        path["differs_from"] = sorted(set(differs))
        if not mine:
            path["status"] = "unguarded"
        elif weaker:
            path["status"] = "weaker"
        else:
            path["status"] = "ok"
    return paths
