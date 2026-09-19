from __future__ import annotations

import ast
import pathlib
import sys
from typing import Iterable

ALLOWLIST_DIRS: tuple[str, ...] = (
    "xninetzy/os/knowledge/extraction",
)


def _is_docstring_expr(node: ast.stmt) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    value = node.value
    if not isinstance(value, ast.Constant):
        return False
    return isinstance(value.value, str)


def _strip_docstrings(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    class Visitor(ast.NodeTransformer):
        def _strip(self, node: ast.AST | None) -> None:
            if node is None:
                return
            body = getattr(node, "body", None)
            if not body:
                return
            if _is_docstring_expr(body[0]):
                body.pop(0)

        def visit_Module(self, node: ast.Module) -> ast.Module:
            self.generic_visit(node)
            self._strip(node)
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            self.generic_visit(node)
            self._strip(node)
            return node

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
            self.generic_visit(node)
            self._strip(node)
            return node

        def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
            self.generic_visit(node)
            self._strip(node)
            return node

    new_tree = Visitor().visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree) + "\n"


def _in_string(text: str) -> bool:
    triple_double = False
    triple_single = False
    in_double = False
    in_single = False
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if not triple_double and not triple_single and not in_double and not in_single:
            if ch == '"' and nxt == '"':
                peek = text[i + 2 : i + 5]
                if peek.startswith('"""'):
                    triple_double = True
                    i += 3
                    continue
            if ch == "'" and nxt == "'":
                peek = text[i + 2 : i + 5]
                if peek.startswith("'''"):
                    triple_single = True
                    i += 3
                    continue
        if triple_double:
            if ch == '"' and nxt == '"' and i + 2 < len(text) and text[i + 2] == '"':
                triple_double = False
                i += 3
                continue
        elif triple_single:
            if ch == "'" and nxt == "'" and i + 2 < len(text) and text[i + 2] == "'":
                triple_single = False
                i += 3
                continue
        elif in_double:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_double = False
        elif in_single:
            if ch == "\\":
                i += 2
                continue
            if ch == "'":
                in_single = False
        else:
            if ch == '"':
                in_double = True
            elif ch == "'":
                in_single = True
        i += 1
    return triple_double or triple_single or in_double or in_single


def _strip_inline_comments(source: str) -> str:
    out_lines: list[str] = []
    for line in source.splitlines():
        if not line.strip():
            out_lines.append(line)
            continue
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out_lines.append("")
            continue
        if "#" in line and _in_string(line) is False:
            hash_index = line.index("#")
            before = line[:hash_index].rstrip()
            if before:
                out_lines.append(before)
            else:
                out_lines.append("")
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if source.endswith("\n") else "")


def _collapse_blank_runs(source: str) -> str:
    lines = source.splitlines()
    out: list[str] = []
    blank = 0
    for line in lines:
        if not line.strip():
            blank += 1
            if blank <= 2:
                out.append("")
            continue
        blank = 0
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + "\n"


def _process_file(path: pathlib.Path) -> bool:
    rel = str(path)
    if not rel.startswith("xninetzy/"):
        return False
    if any(rel.startswith(prefix) for prefix in ALLOWLIST_DIRS):
        return False
    text = path.read_text(encoding="utf-8")
    new = _strip_docstrings(text)
    new = _strip_inline_comments(new)
    new = _collapse_blank_runs(new)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main(argv: Iterable[str]) -> int:
    roots = [pathlib.Path(a) for a in argv] or [pathlib.Path("xninetzy")]
    changed: list[str] = []
    for root in roots:
        if root.is_file():
            targets = [root]
        else:
            targets = sorted(root.rglob("*.py"))
        for p in targets:
            if "__pycache__" in p.parts:
                continue
            if _process_file(p):
                changed.append(str(p))
    print(f"changed={len(changed)}")
    for c in changed[:30]:
        print(f"  {c}")
    if len(changed) > 30:
        print(f"  ... and {len(changed) - 30} more")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
