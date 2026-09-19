from __future__ import annotations

from xninetzy.tools.registry import get_all_tools

_EXPECTED = (
    "improvement_detect",
    "improvement_propose",
    "improvement_evaluate",
    "improvement_approve",
    "improvement_reject",
    "improvement_regress",
    "improvement_list",
)


def test_improvement_tools_registered():
    names = {t.name for t in get_all_tools()}
    missing = [n for n in _EXPECTED if n not in names]
    assert not missing, f"missing improvement tools: {missing}"


def test_no_dead_os_improvement_imports():
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            "grep", "-rn", "-l",
            "--include=*.py",
            r"xninetzy\.os\.improvement",
            "xninetzy", "tests",
        ],
        capture_output=True,
        text=True,
        cwd=root,
    )
    refs = [
        line for line in result.stdout.splitlines()
        if line and not line.endswith("test_improvement_tools_registered.py")
    ]
    assert not refs, f"dead imports of xninetzy.os.improvement remain: {refs}"
