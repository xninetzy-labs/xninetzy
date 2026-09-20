from __future__ import annotations

import re
from pathlib import Path


CONTEXT_ROOT = Path("xninetzy/context")
FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(from|import)\s+httpx\b"),
    re.compile(r"^\s*(from|import)\s+fastapi\b"),
    re.compile(r"^\s*(from|import)\s+mcp(\.|\s|$)"),
    re.compile(r"^\s*(from|import)\s+uvicorn\b"),
    re.compile(r"^\s*(from|import)\s+starlette\b"),
    re.compile(r"^\s*(from|import)\s+langchain"),
    re.compile(r"^\s*(from|import)\s+requests\b"),
    re.compile(r"^\s*(from|import)\s+urllib3\b"),
    re.compile(r"^\s*(from|import)\s+aiohttp\b"),
)

INTAKE_FORBIDDEN_CALLABLES: tuple[str, ...] = (
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "os.system",
    "os.popen",
    "git.Repo",
    "shutil.which",
    "urllib.request.urlopen",
    "urlopen",
)

REQUIRED_INTAKE_FILES: dict[str, bool] = {
    "xninetzy/context/intake/__init__.py": True,
    "xninetzy/context/intake/urls.py": True,
    "xninetzy/context/intake/layout.py": True,
    "xninetzy/context/intake/classify.py": True,
    "xninetzy/context/intake/register.py": True,
}

REQUIRED_INVOCATION_FILES: dict[str, bool] = {
    "xninetzy/context/invocation/__init__.py": True,
    "xninetzy/context/invocation/contract.py": True,
    "xninetzy/context/invocation/classify.py": True,
    "xninetzy/context/invocation/resolve.py": True,
}

REQUIRED_POLICY_FILES: dict[str, bool] = {
    "xninetzy/context/policy/__init__.py": True,
    "xninetzy/context/policy/gate.py": True,
    "xninetzy/context/policy/audit.py": True,
}

REQUIRED_ORCHESTRATOR_FILES: dict[str, bool] = {
    "xninetzy/context/orchestrator/__init__.py": True,
    "xninetzy/context/orchestrator/invokable.py": True,
    "xninetzy/context/orchestrator/pipeline.py": True,
}

REQUIRED_REASONING_FILES: dict[str, bool] = {
    "xninetzy/context/reasoning/__init__.py": True,
    "xninetzy/context/reasoning/depth.py": True,
    "xninetzy/context/reasoning/critic.py": True,
    "xninetzy/context/reasoning/stop.py": True,
}

REQUIRED_PROCESS_ENGINEERING_FILES: dict[str, bool] = {
    "xninetzy/context/process_engineering/__init__.py": True,
    "xninetzy/context/process_engineering/model.py": True,
    "xninetzy/context/process_engineering/validate.py": True,
    "xninetzy/context/process_engineering/bpmn_io.py": True,
    "xninetzy/context/process_engineering/providers.py": True,
    "xninetzy/context/process_engineering/simulation.py": True,
    "xninetzy/context/process_engineering/mining.py": True,
    "xninetzy/context/process_engineering/execution.py": True,
}

REQUIRED_OPTIMIZATION_FILES: dict[str, bool] = {
    "xninetzy/context/capability_graph/match_cache.py": True,
    "xninetzy/context/gateway/provider_cache.py": True,
    "xninetzy/context/exam_qa/assertions.py": True,
}

REQUIRED_EVALUATION_FILES: dict[str, bool] = {
    "xninetzy/context/evaluation/__init__.py": True,
    "xninetzy/context/evaluation/outcome.py": True,
    "xninetzy/context/evaluation/context_eval.py": True,
    "xninetzy/context/evaluation/memory_eval.py": True,
    "xninetzy/context/evaluation/routing_eval.py": True,
    "xninetzy/context/evaluation/skill_eval.py": True,
    "xninetzy/context/evaluation/tool_eval.py": True,
    "xninetzy/context/evaluation/security_eval.py": True,
    "xninetzy/context/evaluation/hallucination.py": True,
    "xninetzy/context/evaluation/root_cause.py": True,
    "xninetzy/context/evaluation/benchmark.py": True,
    "xninetzy/context/evaluation/scoring.py": True,
    "xninetzy/context/evaluation/signal_gen.py": True,
    "xninetzy/context/evaluation/audit.py": True,
    "xninetzy/context/evaluation/integration.py": True,
    "xninetzy/context/evaluation/catalog_audit.py": True,
    "xninetzy/context/evaluation/self_audit.py": True,
}

REQUIRED_LEARNING_FILES: dict[str, bool] = {
    "xninetzy/context/learning/__init__.py": True,
    "xninetzy/context/learning/pattern_engine.py": True,
    "xninetzy/context/learning/experiment_engine.py": True,
    "xninetzy/context/learning/benchmark_engine.py": True,
    "xninetzy/context/learning/evolution_engine.py": True,
}

ALLOWED_IMPORT_PREFIXES = (
    "xninetzy.context",
    "xninetzy.core",
    "xninetzy.db",
    "xninetzy.os",
    "xninetzy.tools",
    "xninetzy.orchestration",
    "xninetzy.interfaces",
)

ALLOWED_STDLIB_PREFIXES = (
    "typing",
    "dataclasses",
    "datetime",
    "re",
    "json",
    "os",
    "sys",
    "math",
    "pathlib",
    "collections",
    "itertools",
    "functools",
    "logging",
    "hashlib",
    "uuid",
)

REQUIRED_TOP_LEVEL = {
    "xninetzy/context/__init__.py": True,
    "xninetzy/context/capability_graph/__init__.py": True,
    "xninetzy/context/gateway/__init__.py": True,
    "xninetzy/context/gateway/trust.py": True,
    "xninetzy/context/gateway/registry.py": True,
    "xninetzy/context/gateway/router.py": True,
}


def _python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def test_context_package_skeleton_exists():
    combined = {
        **REQUIRED_TOP_LEVEL,
        **REQUIRED_INTAKE_FILES,
        **REQUIRED_INVOCATION_FILES,
        **REQUIRED_POLICY_FILES,
        **REQUIRED_ORCHESTRATOR_FILES,
        **REQUIRED_REASONING_FILES,
        **REQUIRED_PROCESS_ENGINEERING_FILES,
        **REQUIRED_OPTIMIZATION_FILES,
        **REQUIRED_EVALUATION_FILES,
        **REQUIRED_LEARNING_FILES,
    }
    for relative in sorted(combined):
        target = Path(relative)
        assert target.exists(), f"missing context skeleton file: {relative}"
        assert target.stat().st_size > 0, f"empty skeleton file: {relative}"


def test_context_package_avoids_forbidden_imports():
    files = _python_files(CONTEXT_ROOT)
    assert files, "xninetzy/context must contain Python modules"
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    offenders.append(f"{path}:{line_no}: {line.strip()}")
    assert not offenders, (
        "context/ must stay free of httpx/fastapi/mcp/uvicorn/starlette "
        "imports (boundary enforced by AGENTS.md §3):\n" + "\n".join(offenders)
    )


def test_context_modules_depend_only_on_allowed_layers():
    files = _python_files(CONTEXT_ROOT)
    assert files
    violations: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped.startswith(("from ", "import ")):
                continue
            token = stripped.split()[1] if len(stripped.split()) > 1 else ""
            token = token.rstrip(",").rstrip(" as").strip()
            if not token:
                continue
            if token.startswith(ALLOWED_STDLIB_PREFIXES):
                continue
            if not token.startswith("xninetzy"):
                continue
            if not any(token.startswith(prefix) for prefix in ALLOWED_IMPORT_PREFIXES):
                violations.append(f"{path}:{line_no}: {stripped}")
    assert not violations, (
        "context/ modules may only import from context/core/db/os/tools/orchestration/interfaces layers:\n"
        + "\n".join(violations)
    )


def test_gateway_modules_exclude_transport_implementations():
    forbidden_callables = (
        "stdio_client",
        "ClientSession",
        "StdioServerParameters",
        "asyncio.run",
        "asyncio.get_event_loop",
    )
    files = _python_files(CONTEXT_ROOT / "gateway")
    assert files, "gateway package must contain modules"
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            for needle in forbidden_callables:
                if needle in stripped:
                    offenders.append(f"{path}:{line_no}: {stripped}")
    assert not offenders, (
        "gateway/ must stay transport-agnostic; "
        "transport code lives under xninetzy/interfaces/:\n" + "\n".join(offenders)
    )


def test_intake_modules_stay_pure_filesystem_only():
    intake_root = CONTEXT_ROOT / "intake"
    if not intake_root.exists():
        return
    files = _python_files(intake_root)
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            for needle in INTAKE_FORBIDDEN_CALLABLES:
                if needle in stripped:
                    offenders.append(f"{path}:{line_no}: {stripped}")
    assert not offenders, (
        "intake/ must stay filesystem-only; no subprocess/git/network calls (boundary enforced by AGENTS.md §3):\n"
        + "\n".join(offenders)
    )
