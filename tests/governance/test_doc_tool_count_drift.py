from __future__ import annotations

import re
from pathlib import Path

from xninetzy.tools.registry import get_tool_names


_DOCS_DIR = Path(__file__).resolve().parents[2] / "apps" / "docs" / "src" / "pages"
_TOOLS_NEAR = re.compile(
    r"\b(\d{2,4})\s*(?:MCP\s+)?(?:tools?|registered\s+tools?)\b",
    flags=re.IGNORECASE,
)
_PAGES_TO_SCAN = (
    "docs/mcp-system.md",
    "docs/architecture.md",
    "docs/introduction.md",
    "docs/api.md",
    "docs/mcp.md",
    "docs/lightning.md",
)


def _load_page(rel: str) -> str:
    path = _DOCS_DIR / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def test_runtime_tool_total_is_sane() -> None:
    total = len(get_tool_names())
    assert total >= 100, (
        f"runtime tool total suspiciously low: {total}"
    )


def test_doc_pages_quote_runtime_tool_total() -> None:
    runtime_total = len(get_tool_names())
    failures: list[str] = []
    for rel in _PAGES_TO_SCAN:
        text = _load_page(rel)
        if not text:
            continue
        for match in _TOOLS_NEAR.finditer(text):
            claimed = int(match.group(1))
            if 100 <= claimed <= 9999 and claimed != runtime_total:
                line = text[: match.start()].count("\n") + 1
                failures.append(
                    f"{rel}:{line} claims {claimed} tools; runtime = {runtime_total}"
                )
    assert not failures, "tool count drift:\n" + "\n".join(failures)


def test_introduction_lists_tableau_domain() -> None:
    text = _load_page("docs/introduction.md")
    assert "Tableau" in text, "introduction.md missing Tableau row in shipped-domains table"


def test_no_phantom_tasks_tools_claim() -> None:
    from xninetzy.tools.registry import get_tool_names

    tasks_tools = [n for n in get_tool_names() if n.startswith("tasks_")]
    if tasks_tools:
        return
    text = _load_page("docs/mcp-system.md")
    assert "tasks_*" not in text, (
        "mcp-system.md still claims `tasks_*` tools but registry has none"
    )
