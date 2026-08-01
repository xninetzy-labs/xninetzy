#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_DIR="${XNINETZY_REPOSITORY_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export MCP_RUNTIME_MODE=host
export CODING_AGENT_EXECUTION_MODE=local

cd "$REPOSITORY_DIR"
exec uv run --directory "$REPOSITORY_DIR/services/ai" --no-dev \
  python -m app.xninetzy.interfaces.host_agent_bridge
