from __future__ import annotations

import ast
import io
import json
import os
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name("no_comment_baseline.json")
SCOPES = ("xninetzy", "tests", "scripts")
SKIPPED_DIRECTORIES = {"node_modules", ".venv", "__pycache__"}
GENERATED_PREFIXES = ("scripts/kaggle_biodiversity/jobs/",)
TOOL_PRAGMAS = ("#!", "# type:", "# noqa", "# pragma", "# fmt:", "# pylint:", "# pyright:", "# mypy:")
DOCUMENTED_NODES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def python_files():
    for scope in SCOPES:
        for path in sorted((ROOT / scope).rglob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            if SKIPPED_DIRECTORIES.isdisjoint(path.parts) and not relative.startswith(GENERATED_PREFIXES):
                yield path


def violations(source: str) -> int:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        tree = ast.parse(source)
    except (SyntaxError, tokenize.TokenError, ValueError):
        return 0
    comments = sum(
        1 for token in tokens
        if token.type == tokenize.COMMENT and not token.string.startswith(TOOL_PRAGMAS)
    )
    docstrings = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, DOCUMENTED_NODES) and ast.get_docstring(node, clean=False) is not None
    )
    return comments + docstrings


def measure() -> dict[str, int]:
    counts = {}
    for path in python_files():
        count = violations(path.read_text(encoding="utf-8"))
        if count:
            counts[path.relative_to(ROOT).as_posix()] = count
    return counts


def test_violation_counter_detects_comments_and_docstrings():
    assert violations("x = 1\n") == 0
    assert violations("x = 1  # note\n") == 1
    assert violations('"""module"""\n\ndef f():\n    """doc"""\n') == 2
    assert violations("#!/usr/bin/env python\nx = 1  # noqa: E501\ny = 2  # type: ignore\n") == 0


def test_no_file_gains_comments_or_docstrings():
    current = measure()
    if os.environ.get("UPDATE_NO_COMMENT_BASELINE") == "1":
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    regressions = {
        path: {"allowed": baseline.get(path, 0), "found": count}
        for path, count in current.items()
        if count > baseline.get(path, 0)
    }
    assert not regressions, f"comments or docstrings added against CLAUDE.md section 3: {regressions}"
