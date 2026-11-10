from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_without_optional_packages(tmp_path: Path, code: str) -> subprocess.CompletedProcess:
    script = """
import importlib.abc
import sys

class BlockOptionalPackages(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
            'langchain_anthropic', 'langchain_openai', 'cv2', 'numpy', 'PIL',
            'sentence_transformers', 'faiss', 'neo4j', 'playwright',
            'openpyxl', 'docx', 'pptx', 'pypdf', 'pdfplumber', 'pypdfium2',
        }:
            raise ModuleNotFoundError('Optional dependency blocked by test: ' + fullname)

sys.meta_path.insert(0, BlockOptionalPackages())
from xninetzy.core.config import Settings, get_settings
Settings.model_config['env_file'] = None
get_settings.cache_clear()
"""
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script) + textwrap.dedent(code)],
        cwd=ROOT,
        env={
            **os.environ,
            "MCP_RUNTIME_MODE": "container",
            "SQLITE_PATH": str(tmp_path / "minimal.sqlite3"),
            "DATA_DIR": str(tmp_path),
            "LIGHTNING_ENABLED": "false",
            "GRAPHRAG_V3_ENABLED": "false",
            "FLAZ_API_KEY": "test-synthetic-key",
            "LLM_ENABLED_PROVIDERS": "flaz",
            "LLM_DEFAULT_PROVIDER": "flaz",
        },
        capture_output=True,
        text=True,
        timeout=45,
    )


def test_tool_adapter_dependency_is_declared_in_base_install():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert any(item.startswith("langchain-core>=") for item in project["dependencies"])
    assert not any(item.startswith("langchain-core") for item in project["optional-dependencies"]["ai"])


def test_llm_module_imports_without_optional_provider_packages(tmp_path):
    result = _run_without_optional_packages(tmp_path, "import xninetzy.core.llm\n")

    assert result.returncode == 0, result.stderr


def test_registry_and_basic_tool_work_without_optional_packages(tmp_path):
    result = _run_without_optional_packages(tmp_path, """
from xninetzy.tools.registry import get_all_tools
tools = {tool.name: tool for tool in get_all_tools()}
assert tools['datetime_now'].invoke({})
assert 'image_inspect' in tools
""")

    assert result.returncode == 0, result.stderr


def test_missing_selected_provider_has_actionable_error(tmp_path):
    result = _run_without_optional_packages(tmp_path, """
from xninetzy.core.llm import get_llm_flash
get_settings.cache_clear()
try:
    get_llm_flash()
except RuntimeError as exc:
    assert 'xninetzy-mcp[ai]' in str(exc), str(exc)
else:
    raise AssertionError('missing provider package must not appear available')
""")

    assert result.returncode == 0, result.stderr


def test_optional_image_operation_has_actionable_error(tmp_path):
    result = _run_without_optional_packages(tmp_path, """
from pathlib import Path
import os
from xninetzy.tools.ecosystem.vision_tools import image_inspect
source = Path(os.environ['DATA_DIR']) / 'synthetic.png'
source.write_bytes(b'synthetic fixture')
try:
    image_inspect.invoke({'path': str(source)})
except RuntimeError as exc:
    assert 'xninetzy-mcp[browser]' in str(exc), str(exc)
else:
    raise AssertionError('missing image dependencies must not appear available')
""")

    assert result.returncode == 0, result.stderr


def test_csv_stays_available_without_spreadsheet_dependency(tmp_path):
    result = _run_without_optional_packages(tmp_path, """
from pathlib import Path
import os
from xninetzy.context.data_analysis.profiling import profile_csv, profile_xlsx
source = Path(os.environ['DATA_DIR']) / 'synthetic.csv'
source.write_text('name,value\\nfixture,2\\n')
assert profile_csv(source).row_count == 1
try:
    profile_xlsx(source.with_suffix('.xlsx'))
except RuntimeError as exc:
    assert 'xninetzy-mcp[documents]' in str(exc), str(exc)
else:
    raise AssertionError('missing spreadsheet dependency must not appear available')
""")

    assert result.returncode == 0, result.stderr
