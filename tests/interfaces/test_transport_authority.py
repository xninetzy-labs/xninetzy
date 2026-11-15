from __future__ import annotations

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("transport", ["invalid-transport", "streamable-http"])
def test_invalid_or_unauthenticated_transport_cannot_initialize_state(tmp_path, transport):
    database = tmp_path / "must-not-create.sqlite3"
    env = {**os.environ, "MCP_RUNTIME_MODE": "container", "SQLITE_PATH": str(database),
           "DATA_DIR": str(tmp_path), "XNINETZY_MCP_TRANSPORT": transport,
           "XNINETZY_MCP_HTTP_HOST": "127.0.0.1"}
    result = subprocess.run([sys.executable, "-c", "import xninetzy.interfaces.mcp_server"],
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert not database.exists(), "Transport validation must precede initialization/migrations"
    if transport == "streamable-http":
        assert "authenticated_http_unavailable" in result.stderr
