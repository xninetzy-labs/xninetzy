#!/usr/bin/env bash
# Xninetzy MCP setup (Linux + macOS).
#
# Idempotent. Runs after install-mcp.{sh,ps1} (or directly on an existing
# clone) to: copy .env.example -> .env, generate AI_API_KEY, set
# OBSIDIAN_VAULT_HOST_PATH, ensure DATA_DIR exists, validate the release
# gate, and print the connection summary.
#
# Usage:
#   bash scripts/setup-mcp.sh                # use defaults
#   AI_API_KEY=... bash scripts/setup-mcp.sh # pre-set bearer
#   XNINETZY_OBSIDIAN_VAULT=... bash scripts/setup-mcp.sh
#   bash scripts/setup-mcp.sh --no-validate  # skip release-check

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKIP_VALIDATE=0
for arg in "$@"; do
  case "$arg" in
    --no-validate) SKIP_VALIDATE=1 ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
  esac
done

if [ ! -f "pyproject.toml" ]; then
  echo "error: pyproject.toml not found at $REPO_ROOT" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found; run install-mcp.sh first or install from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "creating .env from .env.example"
  cp .env.example .env
  chmod 600 .env
fi

AI_KEY="${AI_API_KEY:-}"
if [ -z "$AI_KEY" ]; then
  if command -v openssl >/dev/null 2>&1; then
    AI_KEY="$(openssl rand -hex 32)"
  else
    AI_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  fi
fi

set_env() {
  local key="$1"
  local value="$2"
  awk -v key="$key" -v value="$value" '
    BEGIN { found = 0 }
    index($0, key "=") == 1 { print key "=" value; found = 1; next }
    { print }
    END { if (!found) print key "=" value }
  ' .env > .env.tmp
  mv .env.tmp .env
  chmod 600 .env
}

if grep -qE '^AI_API_KEY=$' .env; then
  echo "writing AI_API_KEY"
  set_env AI_API_KEY "$AI_KEY"
fi

VAULT_PATH="${XNINETZY_OBSIDIAN_VAULT:-${OBSIDIAN_VAULT_HOST_PATH:-$HOME/Documents/xninetzy-vault}}"
if grep -qE '^OBSIDIAN_VAULT_HOST_PATH=$' .env; then
  echo "writing OBSIDIAN_VAULT_HOST_PATH=$VAULT_PATH"
  set_env OBSIDIAN_VAULT_HOST_PATH "$VAULT_PATH"
fi
mkdir -p "$VAULT_PATH"

DATA_DIR="${DATA_DIR:-$HOME/.local/share/xninetzy}"
mkdir -p "$DATA_DIR" "$DATA_DIR/hebat" "$DATA_DIR/external-mcp.d"
if grep -qE '^DATA_DIR=$' .env; then
  set_env DATA_DIR "$DATA_DIR"
fi

OUTPUT_DIR="${OUTPUT_DIR:-$HOME/Documents/xninetzy/output}"
mkdir -p "$OUTPUT_DIR" "$HOME/Documents/xninetzy/generated/research"
if grep -qE '^OUTPUT_DIR=$' .env; then
  set_env OUTPUT_DIR "$OUTPUT_DIR"
fi

echo "syncing Python deps"
uv sync --all-extras

if [ "$SKIP_VALIDATE" -eq 0 ]; then
  echo "running release gate"
  uv run --no-project python -m xninetzy.cli.supervisor release-check
fi

cat <<EOF

==============================================================
  Xninetzy MCP ready
==============================================================
  Install path : $REPO_ROOT
  Data dir     : $DATA_DIR
  Vault path   : $VAULT_PATH
  Output dir   : $OUTPUT_DIR

  Start stdio MCP (primary):
    uv run python -m xninetzy.cli.supervisor start

  Start Streamable HTTP MCP (loopback):
    XNINETZY_MCP_TRANSPORT=streamable-http \\
      uv run python -m xninetzy.interfaces.mcp_server

  Connect from Claude Code:
    claude mcp add --scope user xninetzy -- \\
      $(command -v uv) run --directory $REPO_ROOT \\
      python -m xninetzy.interfaces.mcp_server
==============================================================
EOF
