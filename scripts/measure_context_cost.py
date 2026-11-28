from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def measure(root: Path) -> dict:
    import tiktoken

    encoding = tiktoken.get_encoding("cl100k_base")

    def count(value) -> int:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return len(encoding.encode(text, disallowed_special=()))

    with tempfile.TemporaryDirectory(prefix="xn-context-measure-") as temporary:
        os.environ.update(MCP_RUNTIME_MODE="container", DATA_DIR=temporary,
                          SQLITE_PATH=str(Path(temporary) / "fixture.sqlite3"),
                          XNINETZY_SKILLS_DIR=str(Path(temporary) / "skills"))
        for flag in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED", "LIGHTNING_ENABLED",
                     "NEO4J_ENABLED", "NEO4J_AUTOSTART_ENABLED", "EXTERNAL_MCP_ENABLED"):
            os.environ[flag] = "false"
        for flag in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
            os.environ.pop(flag, None)
        from xninetzy.core.config import Settings, get_settings
        Settings.model_config["env_file"] = None
        get_settings.cache_clear()
        from xninetzy.skills.registry import list_skills, read_skill_markdown
        from xninetzy.skills.tools import skill_list
        from xninetzy.tools.ecosystem.tool_catalog_tools import tool_catalog
        from xninetzy.tools.registry import get_all_tools

        sources = root / "docs/prompt-injection-core"
        shared = [sources / name for name in ("CORE_PROMPT.md", "CORE_RULES.md", "CLI_SHARED_INSTRUCTIONS.md")]
        prompt_files = shared + list(sorted((sources / "cli-overrides").glob("*.md"))) + list(sorted((sources / "references").glob("*.md")))
        prompt_rows = {str(path.relative_to(root)): {"tokens": count(path.read_text()),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in prompt_files}
        compositions = {}
        for client, adapter in (("codex", "codex-AGENTS.md"), ("claude", "claude-CLAUDE.md"),
                                ("opencode", "opencode-xninetzy-paksa.md")):
            files = [*shared, sources / "cli-overrides" / adapter]
            compositions[client] = count("\n".join(path.read_text() for path in files))
        body = read_skill_markdown("context-engineering") or ""
        default_tools = tool_catalog.invoke({"limit": 250})
        catalog = {"full_250": count(default_tools), "rows": len(default_tools)}
        if "compact" in tool_catalog.args_schema.model_fields:
            catalog["compact_same_250"] = count(tool_catalog.invoke({"limit": 250, "compact": True}))
            catalog["compact_memory_5"] = count(tool_catalog.invoke({"query": "memory", "limit": 5, "compact": True}))
        skills = list_skills()
        discovery = {"full_list": count(skill_list.invoke({})), "valid_skills": len(skills),
                     "context_engineering_body": count(body),
                     "context_engineering_body_sha256": hashlib.sha256(body.encode()).hexdigest()}
        if "compact" in skill_list.args_schema.model_fields:
            discovery["compact_same_catalog"] = count(skill_list.invoke({"compact": True}))
            discovery["compact_context_2"] = count(skill_list.invoke({"query": "context", "limit": 2, "compact": True}))
        schemas = [{"name": tool.name, "description": tool.description,
                    "inputSchema": tool.args_schema.model_json_schema()} for tool in get_all_tools()]
        return {"encoding": encoding.name, "prompt_files": prompt_rows, "referenced_client_compositions": compositions,
                "skills": discovery, "catalog": catalog, "registry_schema_text_tokens": count(schemas),
                "tool_count": len(schemas), "owner_data_used": False,
                "limitations": "Registry schemas include server-side identity fields; this is not actual MCP wire or host billing. Full and filtered catalogs disclose different amounts of information. Prompt composition counts each referenced file once."}


if __name__ == "__main__":
    print(json.dumps(measure(Path(__file__).resolve().parents[1]), indent=2))
