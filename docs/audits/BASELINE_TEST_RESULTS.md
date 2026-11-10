# Baseline and candidate verification

Date: 2026-11-10. Existing environment: Python 3.14.5, pytest 9.1.1, MCP 1.30.0, Pydantic 2.13.4, LangChain Core 1.6.3. Repository HEAD at start: `2d0f13f`. Hardware/configuration: [performance baseline](../evaluation/PERFORMANCE_BASELINE.md).

## Isolation and reproducibility

Tests were executed in-process after setting `MCP_RUNTIME_MODE=container`, pointing SQLite/data/output/vault/index paths at fresh `/tmp/xn-*` directories, disabling automatic memory/graph/improvement and optional services, and setting `Settings.model_config['env_file']=None` before clearing the settings cache. This prevents deployment `.env` settings from controlling test paths. Root-layout tests pass explicit fixture mappings; secret tests contain synthetic sentinels only. The existing `.venv` was not reinstalled.

Representative in-process invocation (set all writable paths for tests that exercise those paths):

```python
import os, tempfile
from pathlib import Path
root = Path(tempfile.mkdtemp(prefix="xn-check-"))
os.environ.update(MCP_RUNTIME_MODE="container", SQLITE_PATH=str(root / "tests.sqlite3"),
                  DATA_DIR=str(root), AUTO_MEMORY_ENABLED="false",
                  AUTO_GRAPH_ENABLED="false", AUTO_IMPROVE_ENABLED="false")
from xninetzy.core.config import Settings, get_settings
Settings.model_config["env_file"] = None
get_settings.cache_clear()
import pytest
raise SystemExit(pytest.main(["-q", "tests/db/test_idempotency_store.py"]))
```

## Executed checks

| Check | Before | Candidate / interpretation |
|---|---|---|
| Initial selected suite: tools, idempotency, policy, MCP mapping/adapter, skill frontmatter | 146 passed, 1 xfailed in 22.63s | Xfail masked two invalid legacy names, not damaged YAML |
| Idempotency new concurrency/interruption regressions | 2 failed | 9 total idempotency tests passed after fix |
| Runtime root regression | 4 failed, 5 passed | 17 passed after root correction and ambiguity guard |
| Synthetic Lightning credential tests | 14 failed, 1 passed | 39 combined Lightning/core-redaction tests passed |
| Audit tooling regression | 6 failed | 25 audit/manifest/registry tests passed |
| Canonical prompt integrity entrypoint | Failed: validator missing | 10 prompt contract tests added, including unsafe edits, missing files, traversal, symlink, hash drift and read-only installed comparison |
| Skill governance/health | Broad xfail attribution | 14 passed, 0 xfail; 2 historical rejected mirrors explicitly identified |
| Combined candidate suite A | NOT_MEASURED as identical pre-change suite | 222 passed in 19.65s; see selection below |
| Broader suite B | NOT_MEASURED as identical pre-change suite | 124 passed in 62.65s; see selection below |
| Full collection at intermediate candidate snapshot | Historical collection failures not assumed current | 2538 tests collected, exit 0, 10.06s; collection is not execution |
| Full repository Ruff | No claimed clean baseline | 125 findings outside the focused passing change set; no mass formatting/fix applied |
| STDIO smoke | NOT_MEASURED before | Actual initialize/list and ten safe read calls succeeded |
| Minimal base wheel | Frozen install: 49 packages | Initial startup failed `ModuleNotFoundError: langchain_core`; follow-up recorded in implementation report |

Suite A: `tests/tools tests/db tests/policy tests/interfaces/test_mcp_runtime.py tests/interfaces/test_mcp_tool_adapter.py tests/interfaces/test_trust_injection.py tests/governance/test_skill_frontmatter.py tests/governance/test_prompt_contract.py tests/os/skills/test_skills.py tests/os/lightning/test_input_redaction.py tests/os/lightning/test_lightning_rl.py tests/core/test_secret_redaction.py`.

Suite B: `tests/invocation tests/orchestrator tests/workflow tests/os/policy tests/os/hitl tests/security tests/os/knowledge/test_evaluation.py tests/os/knowledge/test_retrieval.py tests/os/memory tests/architecture tests/cli`.

These selections are disjoint: 346 executed candidate tests at that checkpoint, not 346 end-to-end user scenarios. Later additions and final combined results are recorded in the phase report. No failures were skipped to obtain those results. Existing tests can still encode weak guarantees (for example approval presence); passing them does not prove secure approval consumption.

One attempted combined command referenced nonexistent `test_rl.py` / `test_security_redaction.py`; pytest exited 4 with no tests run. Paths were corrected to the existing files above and the actual successful run is reported. This command error is not a product failure.

## Remaining verification

## Final regression checkpoint

After the additional workflow/projection changes, the final combined run yielded **476 passed, 1 warning in 162.36s**, with no failed/skipped/xfail reported. It includes suite A and B plus `tests/reasoning/test_reasoning_depth.py`, `tests/core/test_llm_providers.py`, `tests/core/test_flaz_llm.py`, `tests/os/graph`, `tests/ecosystem/test_vision_tools.py`, `tests/data_analysis/test_profiling.py` and `tests/data_analysis/test_table_artifact.py`. All checks ran with the temporary-state isolation described above.

The warning is `FutureWarning` in `knowledge/embeddings.py:106`: `get_sentence_embedding_dimension` renamed to `get_embedding_dimension`. It was reported, not suppressed. This result supersedes earlier candidate execution totals; do not add overlapping runs. It remains a selected regression suite, not the entire collected repository suite or 476 end-to-end user tasks.

Final focused Ruff on every changed Python file passes; `git diff --check`, shell syntax, CI YAML parsing and relative documentation links pass. Full repository Ruff still reports **125 findings**. The exact CI minimal-wheel smoke body was executed locally with the isolated installed interpreter from `/tmp`: **571 tools; safe read passed**. Remote CI execution is not verified.

## Outstanding verification

Full execution of all collected tests, clean Python 3.11 installation, container build, backup/restore, advisory scan, real network/provider failure tests, academic portal actions, native Codex/Claude/OpenCode parity, and 50 curated outcome tasks were not completed. No historic 811/29 or 828/29 result is reused as today's baseline. Release readiness remains NOT_READY.
