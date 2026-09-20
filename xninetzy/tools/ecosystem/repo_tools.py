from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import tool


REPO_ROOT = Path(__file__).resolve().parents[3]

_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".codebase-memory",
}

_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".mp3", ".mp4", ".wav", ".mov", ".mkv",
    ".pyc", ".pyo", ".so", ".dll", ".dylib", ".class",
    ".ttf", ".otf", ".woff", ".woff2",
}

_DEFAULT_LIMITS = {
    "repo_search": {"limit": 30, "max_file_bytes": 200_000},
    "repo_symbol": {"limit": 1},
    "repo_dependency": {"limit": 200},
    "repo_test": {"limit": 50},
    "repo_diff": {"limit": 50},
    "repo_architecture": {"limit": 80},
    "repo_risk": {"limit": 60},
}

_SCOPE_ALIASES = {
    "self": REPO_ROOT,
    "host": REPO_ROOT,
    "home": REPO_ROOT,
    "repo": REPO_ROOT,
}


@dataclass(slots=True)
class RepoHit:
    path: str
    line: int
    preview: str
    score: int = 0


@dataclass(slots=True)
class SymbolInfo:
    name: str
    kind: str
    file: str
    line: int
    signature: str = ""
    doc_summary: str = ""


@dataclass(slots=True)
class DepEdge:
    source: str
    target: str
    kind: str = "import"


@dataclass(slots=True)
class TestEntry:
    path: str
    framework: str
    test_count: int
    collected: bool


@dataclass(slots=True)
class DiffHunk:
    file: str
    status: str
    additions: int = 0
    deletions: int = 0
    sample: str = ""


@dataclass(slots=True)
class ArchNode:
    path: str
    kind: str
    description: str = ""
    binding: bool = False


@dataclass(slots=True)
class RiskFinding:
    file: str
    line: int
    pattern: str
    excerpt: str
    severity: str
    rationale: str


_RISK_RULES: list[tuple[str, str, str, str]] = [
    ("subprocess", r"\bsubprocess\.(?:Popen|run|call|check_output|check_call)\b", "high", "subprocess call"),
    ("os.system", r"\bos\.system\s*\(", "high", "shell execution"),
    ("eval", r"\beval\s*\(", "high", "dynamic code execution"),
    ("exec", r"\bexec\s*\(", "high", "dynamic code execution"),
    ("pickle_load", r"\bpickle\.loads?\s*\(", "medium", "unsafe deserialization"),
    ("yaml_load_unsafe", r"\byaml\.load\s*\((?![^)]*Loader\s*=)", "medium", "unsafe YAML load"),
    ("shell_true", r"shell\s*=\s*True", "medium", "shell=True risk"),
    ("http_no_timeout", r"\bhttpx\.[A-Za-z_]+\s*\([^)]*\)", "low", "httpx call without explicit timeout"),
    ("requests_no_timeout", r"\brequests\.[A-Za-z_]+\s*\([^)]*\)", "low", "requests call without explicit timeout"),
    ("hardcoded_password", r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]", "high", "hardcoded password"),
    ("hardcoded_token", r"(?i)(api_key|token|secret)\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]", "high", "hardcoded credential"),
    ("sql_concat", r"(?i)\b(?:SELECT|INSERT|UPDATE|DELETE)\b[^;\n]*%[sd]", "medium", "SQL string format"),
    ("sql_fstring", r"execute\s*\(\s*f['\"][^'\"]*\{", "medium", "SQL f-string injection"),
    ("open_path_traversal", r"\bopen\s*\([^)]*\+[^)]*\)", "low", "open() with concatenated path"),
    ("random_usesecrets", r"\brandom\.[A-Za-z_]+\b", "low", "non-cryptographic random"),
    ("md5_password", r"(?i)hashlib\.md5", "low", "weak hash function"),
    ("sha1_password", r"(?i)hashlib\.sha1", "low", "weak hash function"),
    ("disable_ssl", r"verify\s*=\s*False", "medium", "TLS verification disabled"),
    ("allow_offscreen_canvas", r"getContext\s*\(\s*['\"]webgl['\"][^)]*\{[^}]*preserveDrawingBuffer", "low", "webgl fingerprint pattern"),
]


def _resolve_root(root: str) -> Path:
    candidate = (root or "").strip()
    if not candidate or candidate in _SCOPE_ALIASES:
        return REPO_ROOT
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not path.exists() or not path.is_dir():
        return REPO_ROOT
    return path


def _iter_files(root: Path, glob: str) -> list[Path]:
    if glob and glob != "**/*":
        results: list[Path] = []
        for path in root.glob(glob):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in _BINARY_SUFFIXES:
                continue
            results.append(path)
        return sorted(results)
    results: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in _SKIP_DIRS or path.name.startswith(".") and path.name not in {".github"}:
                continue
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        results.append(path)
    return results


def _safe_read(path: Path, max_bytes: int) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return ""
    if size > max_bytes:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""


def _score_line(line: str, terms: list[str], use_regex: bool) -> int:
    if use_regex:
        for term in terms:
            if re.search(term, line):
                return 1
        return 0
    lowered = line.lower()
    return sum(1 for term in terms if term in lowered)


def _truncate_preview(line: str, width: int = 160) -> str:
    line = line.rstrip("\n")
    if len(line) > width:
        return line[: width - 3] + "..."
    return line


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


@tool
def repo_search(
    query: str,
    root: str = "self",
    glob: str = "**/*.py",
    limit: int = 30,
    use_regex: bool = False,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Cari teks/regex di repository.

    Args:
        query: String atau pola yang dicari (case-insensitive kecuali regex).
        root: Path atau alias: self|host|home|repo (default self = Xninetzy repo).
        glob: Pola file (default **/*.py). "**/*" untuk semua teks-eligible.
        limit: Maks jumlah baris yang dikembalikan (cap 200).
        use_regex: True untuk memperlakukan query sebagai regex.
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 200))
    terms: list[str]
    if use_regex:
        terms = [query]
    else:
        terms = [t.strip().lower() for t in query.split() if t.strip()]
    if not terms:
        return json.dumps({"query": query, "hits": [], "count": 0}, ensure_ascii=False)

    hits: list[RepoHit] = []
    max_bytes = _DEFAULT_LIMITS["repo_search"]["max_file_bytes"]
    for path in _iter_files(base, glob):
        text = _safe_read(path, max_bytes)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            score = _score_line(line, terms, use_regex)
            if score <= 0:
                continue
            hits.append(RepoHit(
                path=_rel(base, path),
                line=line_no,
                preview=_truncate_preview(line),
                score=score,
            ))
            if len(hits) >= bounded_limit * 4:
                break
        if len(hits) >= bounded_limit * 4:
            break

    hits.sort(key=lambda h: (-h.score, h.path, h.line))
    top = hits[:bounded_limit]
    payload = {
        "root": str(base),
        "query": query,
        "glob": glob,
        "regex": use_regex,
        "limit": bounded_limit,
        "count": len(top),
        "truncated": len(hits) > bounded_limit,
        "hits": [
            {"path": h.path, "line": h.line, "preview": h.preview, "score": h.score}
            for h in top
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_symbol(
    name: str,
    root: str = "self",
    glob: str = "**/*.py",
    limit: int = 5,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Lokasi + signature sebuah symbol Python (function/class/method) via AST.

    Args:
        name: Nama symbol persis atau akhiran (mis. ``idempotent_call``).
        root: Path atau alias repo (default self).
        glob: Pola file Python (default **/*.py).
        limit: Maks jumlah definisi yang dikembalikan (cap 25).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 25))
    needle = name.strip()
    if not needle:
        return json.dumps({"symbol": name, "matches": [], "count": 0}, ensure_ascii=False)

    matches: list[SymbolInfo] = []
    for path in _iter_files(base, glob):
        text = _safe_read(path, _DEFAULT_LIMITS["repo_search"]["max_file_bytes"])
        if not text:
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name != needle and not node.name.endswith(needle):
                continue
            sig = _render_signature(node)
            doc = ast.get_docstring(node) or ""
            if doc:
                doc = doc.splitlines()[0][:200]
            kind = "class" if isinstance(node, ast.ClassDef) else (
                "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            )
            matches.append(SymbolInfo(
                name=node.name,
                kind=kind,
                file=_rel(base, path),
                line=node.lineno,
                signature=sig,
                doc_summary=doc,
            ))

    matches.sort(key=lambda s: (s.file, s.line))
    top = matches[:bounded_limit]
    payload = {
        "symbol": name,
        "root": str(base),
        "count": len(top),
        "truncated": len(matches) > bounded_limit,
        "matches": [
            {
                "name": m.name,
                "kind": m.kind,
                "file": m.file,
                "line": m.line,
                "signature": m.signature,
                "doc_summary": m.doc_summary,
            }
            for m in top
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _render_signature(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    args = getattr(node, "args", None)
    if args is None:
        return node.name
    parts: list[str] = []
    pos = list(getattr(args, "posonlyargs", [])) + list(getattr(args, "args", []))
    defaults_count = len(getattr(args, "defaults", []))
    if pos:
        head = pos[: len(pos) - defaults_count]
        tail = pos[len(pos) - defaults_count:]
        for a in head:
            parts.append(a.arg)
        for a in tail:
            parts.append(f"{a.arg}=...")
    if getattr(args, "vararg", None):
        parts.append(f"*{args.vararg.arg}")
    elif getattr(args, "kwonlyargs", None):
        parts.append("*")
    for kw in getattr(args, "kwonlyargs", []):
        parts.append(kw.arg)
    if getattr(args, "kwarg", None):
        parts.append(f"**{args.kwarg.arg}")
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    return f"{prefix}{node.name}({', '.join(parts)})"


@tool
def repo_dependency(
    root: str = "self",
    glob: str = "**/*.py",
    limit: int = 200,
    include_stdlib: bool = False,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Edges graph impor antar-modul (internal + eksternal).

    Args:
        root: Path atau alias repo (default self).
        glob: Pola file Python (default **/*.py).
        limit: Maks jumlah edges (cap 500).
        include_stdlib: True untuk menyertakan modul stdlib di edges.
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    import sys
    stdlib = set(getattr(sys, "stdlib_module_names", set()))

    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 500))
    edges: list[DepEdge] = []
    modules: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()

    for path in _iter_files(base, glob):
        rel_path = _rel(base, path)
        if rel_path.endswith("__pycache__") or "/__pycache__/" in rel_path:
            continue
        text = _safe_read(path, _DEFAULT_LIMITS["repo_search"]["max_file_bytes"])
        if not text:
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        mod_key = rel_path[:-3].replace("/", ".").removesuffix(".__init__") if rel_path.endswith(".py") else rel_path
        modules.add(mod_key)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name.split(".")[0]
                    key = (mod_key, target)
                    if key not in seen_edges:
                        seen_edges.add(key)
                        edges.append(DepEdge(source=mod_key, target=target))
            elif isinstance(node, ast.ImportFrom):
                if node.module is None or node.level > 0:
                    continue
                target = node.module.split(".")[0]
                key = (mod_key, target)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append(DepEdge(source=mod_key, target=target, kind="from"))

    if not include_stdlib:
        edges = [e for e in edges if e.target not in stdlib]

    incoming: Counter[str] = Counter(e.target for e in edges if e.target in modules)
    outgoing: Counter[str] = Counter(e.source for e in edges)
    truncated = len(edges) > bounded_limit
    edges = edges[:bounded_limit]
    payload = {
        "root": str(base),
        "module_count": len(modules),
        "edge_count": len(edges),
        "truncated": truncated,
        "most_imported": [
            {"module": name, "incoming": count}
            for name, count in incoming.most_common(10)
        ],
        "most_dependent": [
            {"module": name, "outgoing": count}
            for name, count in outgoing.most_common(10)
        ],
        "edges": [
            {"source": e.source, "target": e.target, "kind": e.kind}
            for e in edges
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_test(
    root: str = "self",
    limit: int = 50,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Inventaris file test + jumlah test function (pytest/unittest).

    Args:
        root: Path atau alias repo (default self).
        limit: Maks jumlah file test yang dikembalikan (cap 200).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 200))
    entries: list[TestEntry] = []

    for path in sorted(base.rglob("tests/**/*.py")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        text = _safe_read(path, _DEFAULT_LIMITS["repo_search"]["max_file_bytes"])
        if not text:
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        pytest_count = 0
        unittest_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    pytest_count += 1
            elif isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                if any("TestCase" in b for b in bases):
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if child.name.startswith("test_"):
                                unittest_count += 1
        total = pytest_count + unittest_count
        if total <= 0:
            continue
        framework = "pytest" if pytest_count >= unittest_count else "unittest"
        entries.append(TestEntry(
            path=_rel(base, path),
            framework=framework,
            test_count=total,
            collected=True,
        ))
        if len(entries) >= bounded_limit:
            break

    by_framework = Counter(e.framework for e in entries)
    payload = {
        "root": str(base),
        "file_count": len(entries),
        "by_framework": dict(by_framework),
        "tests": [
            {"path": e.path, "framework": e.framework, "count": e.test_count}
            for e in entries
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_diff(
    target: str = "HEAD",
    base: str = "HEAD",
    limit: int = 50,
    include_sample: bool = True,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Ringkasan diff ``git diff <base>..<target>``: status, +/-/file, sample.

    Args:
        target: Ref target (default HEAD).
        base: Ref base (default HEAD).
        limit: Maks jumlah file (cap 200).
        include_sample: True untuk menyertakan cuplikan diff.
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    import subprocess

    bounded_limit = max(1, min(limit, 200))
    target_ref = target.strip() or "HEAD"
    base_ref = base.strip() or "HEAD"
    cmd = ["git", "diff", "--numstat", f"{base_ref}...{target_ref}"]
    try:
        proc = subprocess.run(
            cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=20
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return json.dumps({"error": f"git unavailable: {exc}"}, ensure_ascii=False)
    if proc.returncode != 0:
        return json.dumps({
            "error": (proc.stderr or "").strip()[:400],
            "command": " ".join(cmd),
        }, ensure_ascii=False)

    hunks: list[DiffHunk] = []
    additions = 0
    deletions = 0
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, file_path = parts
        additions += int(added) if added.isdigit() else 0
        deletions += int(deleted) if deleted.isdigit() else 0
        status = "modified"
        if added == "0" and deleted != "0":
            status = "deleted"
        elif deleted == "0" and added != "0":
            status = "added"
        hunks.append(DiffHunk(
            file=file_path,
            status=status,
            additions=int(added) if added.isdigit() else 0,
            deletions=int(deleted) if deleted.isdigit() else 0,
        ))

    if include_sample and hunks:
        sample_proc = subprocess.run(
            ["git", "diff", "--no-color", f"{base_ref}...{target_ref}"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
        if sample_proc.returncode == 0:
            sections: list[str] = []
            current_file = ""
            current_section: list[str] = []
            for line in sample_proc.stdout.splitlines():
                if line.startswith("diff --git "):
                    if current_file and current_section:
                        sections.append("\n".join(current_section))
                    current_file = line.split(" b/", 1)[-1]
                    current_section = [line]
                elif current_file:
                    if len(current_section) < 12:
                        current_section.append(line)
            if current_file and current_section:
                sections.append("\n".join(current_section))
            for hunk, idx in zip(hunks, sections[: len(hunks)]):
                hunk.sample = _truncate_preview(idx, width=600)

    truncated = len(hunks) > bounded_limit
    hunks = hunks[:bounded_limit]
    payload = {
        "base": base_ref,
        "target": target_ref,
        "file_count": len(hunks),
        "truncated": truncated,
        "additions": additions,
        "deletions": deletions,
        "files": [
            {
                "file": h.file,
                "status": h.status,
                "additions": h.additions,
                "deletions": h.deletions,
                "sample": h.sample,
            }
            for h in hunks
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_architecture(
    root: str = "self",
    depth: int = 2,
    limit: int = 80,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Peta top-level direktori + file binding (CLAUDE.md/AGENTS.md/README) + entry tools.

    Args:
        root: Path atau alias repo (default self).
        depth: Kedalaman direktori (1=root only, 2=subdir).
        limit: Maks node (cap 200).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 200))
    max_depth = max(1, min(depth, 4))

    nodes: list[ArchNode] = []
    binding_files = {"AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml"}

    def _walk(path: Path, current_depth: int) -> None:
        if len(nodes) >= bounded_limit:
            return
        rel = _rel(base, path)
        is_root = path == base
        nodes.append(ArchNode(
            path=rel or ".",
            kind="root" if is_root else "directory",
        ))
        if current_depth >= max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except (PermissionError, OSError):
            return
        for child in children:
            if child.name in _SKIP_DIRS or child.name.startswith("."):
                continue
            if child.is_dir():
                _walk(child, current_depth + 1)
            elif child.is_file() and child.name in binding_files:
                nodes.append(ArchNode(
                    path=_rel(base, child),
                    kind="file",
                    binding=True,
                ))

    _walk(base, 1)

    entrypoints: list[str] = []
    for path in _iter_files(base, "**/*.py"):
        rel = _rel(base, path)
        if rel.startswith("xninetzy/tools/registry") or rel.endswith("main.py"):
            entrypoints.append(rel)
            if len(entrypoints) >= 10:
                break

    payload = {
        "root": str(base),
        "depth": max_depth,
        "node_count": len(nodes),
        "entrypoints": entrypoints,
        "nodes": [
            {"path": n.path, "kind": n.kind, "binding": n.binding}
            for n in nodes
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_risk(
    root: str = "self",
    glob: str = "**/*.py",
    limit: int = 60,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Pemindai SAST ringan: subprocess/eval/pickle/yaml.unsafe/hardcoded creds/SQL format/disable_ssl/dll.

    Args:
        root: Path atau alias repo (default self).
        glob: Pola file Python (default **/*.py).
        limit: Maks jumlah finding (cap 200).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded_limit = max(1, min(limit, 200))
    findings: list[RiskFinding] = []
    counts: Counter[str] = Counter()

    for path in _iter_files(base, glob):
        text = _safe_read(path, _DEFAULT_LIMITS["repo_search"]["max_file_bytes"])
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for rule_id, pattern, severity, rationale in _RISK_RULES:
                try:
                    if re.search(pattern, line):
                        findings.append(RiskFinding(
                            file=_rel(base, path),
                            line=line_no,
                            pattern=rule_id,
                            excerpt=_truncate_preview(line, width=180),
                            severity=severity,
                            rationale=rationale,
                        ))
                        counts[rule_id] += 1
                except re.error:
                    continue
        if len(findings) >= bounded_limit * 3:
            break

    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 99), f.file, f.line))
    top = findings[:bounded_limit]
    payload = {
        "root": str(base),
        "rule_count": len({f.pattern for f in findings}),
        "finding_count": len(top),
        "truncated": len(findings) > bounded_limit,
        "by_rule": dict(counts.most_common()),
        "findings": [
            {
                "file": f.file,
                "line": f.line,
                "pattern": f.pattern,
                "severity": f.severity,
                "rationale": f.rationale,
                "excerpt": f.excerpt,
            }
            for f in top
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def repo_file_outline(
    path: str,
    root: str = "self",
    max_symbols: int = 40,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Ringkasan satu file: top-level symbols + 5 baris pertama (untuk context agent).

    Args:
        path: Path relatif terhadap root.
        root: Path atau alias repo (default self).
        max_symbols: Maks jumlah symbol yang dikembalikan (cap 100).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    base = _resolve_root(root)
    bounded = max(1, min(max_symbols, 100))
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not target.exists() or not target.is_file():
        return json.dumps(
            {"path": path, "found": False, "reason": "missing"},
            ensure_ascii=False,
        )
    if base not in target.parents and target != base:
        return json.dumps(
            {"path": path, "found": False, "reason": "outside_root"},
            ensure_ascii=False,
        )
    text = _safe_read(target, _DEFAULT_LIMITS["repo_search"]["max_file_bytes"])
    rel = _rel(base, target)
    symbols: list[dict] = []
    if target.suffix == ".py":
        try:
            tree = ast.parse(text, filename=str(target))
        except SyntaxError as exc:
            tree = None
            parse_error = str(exc)
        else:
            parse_error = None
        if tree is not None:
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                symbols.append(
                    {
                        "name": node.name,
                        "kind": (
                            "class"
                            if isinstance(node, ast.ClassDef)
                            else "async_function"
                            if isinstance(node, ast.AsyncFunctionDef)
                            else "function"
                        ),
                        "line": node.lineno,
                        "signature": _render_signature(node),
                        "doc_summary": ((ast.get_docstring(node) or "").splitlines() or [""])[0][:160],
                    }
                )
                if len(symbols) >= bounded:
                    break
    else:
        parse_error = None
    preview_lines = text.splitlines()[:5]
    payload = {
        "path": rel,
        "found": True,
        "size_bytes": target.stat().st_size,
        "language": "python" if target.suffix == ".py" else target.suffix.lstrip(".") or "text",
        "symbol_count": len(symbols),
        "symbols": symbols,
        "preview": preview_lines,
        "parse_error": (locals().get("parse_error") if locals().get("parse_error") else None),
    }
    return json.dumps(payload, ensure_ascii=False)
