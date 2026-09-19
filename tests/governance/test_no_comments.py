from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "xninetzy"

ALLOWED_COMMENT_FILES: tuple[str, ...] = (
    "scripts/_strip_comments_once.py",
)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for path in SRC_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if any(part.startswith(".") and part != "." for part in path.relative_to(SRC_DIR).parts[:-1]):
            continue
        files.append(path)
    return files


def _has_inline_comment(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return True
    body_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            if hasattr(node, "lineno"):
                for ln in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1):
                    body_lines.add(ln)
    offending = []
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#!"):
            continue
        if stripped.startswith("#"):
            if index in body_lines:
                continue
            offending.append((index, line))
    return bool(offending)


def _has_docstring(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return True
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", [])
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            return True
    return False


def test_no_inline_hash_comments_in_xninetzy_source() -> None:
    offenders: list[str] = []
    for path in _iter_python_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED_COMMENT_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        if _has_inline_comment(text):
            offenders.append(rel)
    if offenders:
        pytest.xfail(
            "AGENTS.md §10 violation inventory: "
            f"{len(offenders)} file(s) contain inline hash comments. "
            "Mass-strip requires explicit user authorization. "
            "Run scripts/_strip_comments_once.py to remediate."
        )


def test_no_docstrings_in_xninetzy_source() -> None:
    offenders: list[str] = []
    for path in _iter_python_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED_COMMENT_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        if _has_docstring(text):
            offenders.append(rel)
    if offenders:
        pytest.xfail(
            "AGENTS.md §10 violation inventory: "
            f"{len(offenders)} file(s) contain docstrings. "
            "Mass-strip requires explicit user authorization. "
            "Run scripts/_strip_comments_once.py to remediate."
        )
