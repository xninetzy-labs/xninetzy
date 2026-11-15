"""Real MCP lifespan/FAISS restart smoke using disposable, offline state.

Run with a source/development install or a fresh frozen embeddings installation.
The semantic profile requires an already cached model; downloads are disabled.
No owner store, host client configuration or Neo4j instance is modified.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BOOTSTRAP = (
    "from xninetzy.core.config import Settings; Settings.model_config['env_file']=None; "
    "import runpy; runpy.run_module('xninetzy.interfaces.mcp_server',run_name='__main__')"
)


def configure(root: Path, provider: str) -> dict[str, str]:
    environment = {key: os.environ[key] for key in ("PATH", "LANG", "TZ", "HF_HOME", "HF_HUB_CACHE") if key in os.environ}
    environment.update(
        MCP_RUNTIME_MODE="container", SQLITE_PATH=str(root / "state.sqlite3"), DATA_DIR=str(root),
        MCP_PRINCIPAL_ID="graph-worker-fixture", MCP_DEFAULT_CHAT_ID="graph-worker-fixture",
        XNINETZY_MCP_TRANSPORT="stdio", GRAPHRAG_V3_ENABLED="true", GRAPH_SYNC_WORKER_ENABLED="true",
        GRAPH_SYNC_STARTUP_DELAY_SECONDS="0", GRAPH_SYNC_POLL_SECONDS="2",
        EMBEDDING_PROVIDER=provider, EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
    )
    for key in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED", "LIGHTNING_ENABLED",
                "NEO4J_ENABLED", "NEO4J_AUTOSTART_ENABLED", "EXTERNAL_MCP_ENABLED", "OS_SCHEDULER_ENABLED"):
        environment[key] = "false"
    for key in ("OUTPUT_DIR", "BACKUP_DIR", "HEBAT_DATA_DIR", "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_PATH",
                "VECTOR_DATA_DIR", "GRAPH_VECTOR_DATA_DIR", "XNINETZY_SKILLS_DIR"):
        environment[key] = str(root / key.lower())
    for key in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
        os.environ.pop(key, None)
    os.environ.update(environment)
    from xninetzy.core.config import Settings, get_settings
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    return environment


async def check(root: Path, provider: str) -> dict:
    environment = configure(root, provider)
    from xninetzy.db.sqlite import init_db, connect
    from xninetzy.db.migrations import run_migrations
    from xninetzy.os.graph.v3 import sqlite_store, faiss_store
    init_db()
    run_migrations()
    corpus = [
        ("Database transactions", "SQLite commits protect atomic database updates."),
        ("Spaced repetition", "Active recall schedules practice to improve learning retention."),
        ("Public key authentication", "Cryptographic identity verifies the sender without sharing a private key."),
    ]
    keys = [sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title=title, content=body)).key
            for title, body in corpus]
    vector_root = root / "graph_vector_data_dir"

    async def session_run(label: str, *, enabled: bool) -> dict:
        child_env = {**environment, "GRAPH_SYNC_WORKER_ENABLED": str(enabled).lower()}
        parameters = StdioServerParameters(command=sys.executable, args=["-I", "-c", BOOTSTRAP],
                                           env=child_env, cwd=str(root))
        started = time.perf_counter()
        with (root / f"{label}.stderr").open("w") as errors:
            async with asyncio.timeout(90):
                async with stdio_client(parameters, errlog=errors) as streams:
                    async with ClientSession(*streams) as session:
                        initialized = await session.initialize()
                        startup = time.perf_counter() - started
                        discovery_start = time.perf_counter()
                        catalog = await session.list_tools()
                        discovery = time.perf_counter() - discovery_start
                        assert "graph_v3_stats" in {tool.name for tool in catalog.tools}
                        if enabled:
                            async with asyncio.timeout(60):
                                while True:
                                    with connect() as conn:
                                        unfinished = conn.execute("SELECT count(*) FROM graph_sync_outbox WHERE status!='done'").fetchone()[0]
                                    if not unfinished:
                                        break
                                    await asyncio.sleep(0.1)
                        stats = await session.call_tool("graph_v3_stats", {})
                        assert not stats.isError
                        assert f"Projection worker configured: {enabled}, running: {int(enabled)}" in str(stats)
                        timings = []
                        for _ in range(10):
                            before = time.perf_counter()
                            result = await session.call_tool("datetime_now", {})
                            assert not result.isError
                            timings.append((time.perf_counter() - before) * 1000)
                        return {"protocol": initialized.protocolVersion, "tools": len(catalog.tools),
                                "startup_seconds": round(startup, 6), "discovery_ms": round(discovery * 1000, 3),
                                "warm_read_samples": len(timings), "warm_read_p50_ms": round(statistics.median(timings), 3),
                                "warm_read_p95_nearest_rank_ms": round(sorted(timings)[-1], 3)}

    disabled = await session_run("disabled", enabled=False)
    assert not vector_root.exists(), "Disabled worker initialized vector state"
    with connect() as conn:
        assert conn.execute("SELECT count(*) FROM graph_sync_outbox WHERE status='pending'").fetchone()[0] == len(keys)
    first = await session_run("first", enabled=True)
    pointer = json.loads((vector_root / "graph.current.json").read_text())
    assert pointer["count"] == len(keys)
    assert pointer["embedding"]["provider"] == provider
    with connect() as conn:
        assert conn.execute("SELECT count(*) FROM graph_nodes_v3 WHERE faiss_synced_at IS NOT NULL").fetchone()[0] == len(keys)
    assert sqlite_store.enqueue_full_resync() == len(keys)
    restart = await session_run("restart", enabled=True)
    assert json.loads((vector_root / "graph.current.json").read_text()) == pointer
    top = faiss_store.search("Database transactions", limit=1)
    assert top and top[0]["key"] == keys[0]
    return {"provider": provider, "offline": True, "owner_data_used": False,
            "python": platform.python_version(), "machine": platform.machine(), "logical_cpus": os.cpu_count(),
            "disabled": disabled, "first_start": first, "restart": restart,
            "canonical_nodes": len(keys), "vector_rows_after_resync": pointer["count"],
            "unchanged_generation_after_resync": True, "embedding": pointer["embedding"],
            "retrieval_exact_title_top1": "passed", "worker_started_by_mcp_lifespan": True,
            "limitations": "Three synthetic nodes and ten reads per session; no statistical performance guarantee, external effects or Neo4j. Shutdown is cooperative."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("numpy_tfidf", "sentence_transformers"), default="numpy_tfidf")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="xn-graph-worker-smoke-") as temporary:
        print(json.dumps(asyncio.run(check(Path(temporary), args.provider)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
