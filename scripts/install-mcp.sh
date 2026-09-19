#!/usr/bin/env bash
# Xninetzy MCP installer (Linux + macOS).
#
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
#
# Windows PowerShell variant lives at scripts/install-mcp.ps1.
#
# Environment overrides:
#   XNINETZY_INSTALL_DIR     install path          (default: $HOME/xninetzy)
#   XNINETZY_BRANCH          git ref               (default: main)
#   XNINETZY_INSTALL_MODE    local | docker        (default: local)
#   XNINETZY_AI_API_KEY      pre-set bearer key    (default: random)
#   XNINETZY_OBSIDIAN_VAULT  vault path            (default: $HOME/Documents/xninetzy-vault)
#   XNINETZY_INSTALL_NEO4J   install Neo4j         (default: false; opt-in)
#
# Steps performed (local mode):
#   1. ensure git, uv, openssl (auto-install uv via brew or astral.sh)
#   2. clone repo at requested branch
#   3. install OS deps: tesseract, sqlite3, libatlas/lapack
#   4. uv sync --all-extras (Python deps: mcp, fastapi, faiss-cpu, torch CPU,
#      sentence-transformers, neo4j, opencv, langchain-core, etc.)
#   5. playwright install chromium --with-deps (HEBAT browser)
#   6. opt-in: Neo4j via official apt repo or brew
#   7. random AI_API_KEY, OBSIDIAN_VAULT_HOST_PATH
#   8. supervisor release-check

set -euo pipefail

REPOSITORY_URL="${XNINETZY_REPO_URL:-https://github.com/xninetzy-labs/xninetzy.git}"

detect_os() {
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux)  echo "linux" ;;
    Darwin) echo "macos" ;;
    *)      echo "unsupported" ;;
  esac
}

OS="$(detect_os)"
if [ "$OS" = "unsupported" ]; then
  echo "Unsupported OS. Use scripts/install-mcp.ps1 on Windows."
  exit 1
fi

INSTALL_DIR="${XNINETZY_INSTALL_DIR:-$HOME/xninetzy}"
BRANCH="${XNINETZY_BRANCH:-main}"
MODE="${XNINETZY_INSTALL_MODE:-local}"
AI_KEY="${XNINETZY_AI_API_KEY:-}"
VAULT_PATH="${XNINETZY_OBSIDIAN_VAULT:-$HOME/Documents/xninetzy-vault}"

usage() {
  cat <<'USAGE'
xninetzy-mcp installer (Linux/macOS)

Usage:
  curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash

Environment variables:
  XNINETZY_INSTALL_DIR    install path (default: ~/xninetzy)
  XNINETZY_BRANCH         git branch/tag (default: main)
  XNINETZY_INSTALL_MODE   local | docker  (default: local)
  XNINETZY_AI_API_KEY     bearer key for /api/chat (random if unset)
  XNINETZY_OBSIDIAN_VAULT vault path (default: ~/Documents/xninetzy-vault)
USAGE
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

fail() { echo "error: $*" >&2; exit 1; }

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  echo "uv not found; installing via official installer..."
  if [ "$OS" = "macos" ] && command -v brew >/dev/null 2>&1; then
    brew install uv
  else
    curl -fsSL https://astral.sh/uv/install.sh | sh
  fi
  command -v uv >/dev/null 2>&1 || fail "uv install failed; install manually: https://docs.astral.sh/uv/"
}

ensure_git() {
  command -v git >/dev/null 2>&1 || fail "git not found; install via your package manager"
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || fail "docker not found"
  docker compose version >/dev/null 2>&1 || fail "docker compose plugin missing"
}

ensure_openssl() {
  command -v openssl >/dev/null 2>&1 || fail "openssl not found"
}

if [ "$MODE" = "docker" ]; then
  ensure_git
  ensure_docker
  ensure_openssl
else
  ensure_git
  ensure_uv
  ensure_openssl
fi

if [ -f "./pyproject.toml" ] && [ -f "./xninetzy/interfaces/mcp_server.py" ]; then
  INSTALL_DIR="$(pwd)"
elif [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$INSTALL_DIR" checkout "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
else
  echo "Cloning $REPOSITORY_URL ($BRANCH) into $INSTALL_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPOSITORY_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [ ! -f ".env" ]; then
  cp .env.example .env
  chmod 600 .env
fi

if [ -z "$AI_KEY" ]; then
  AI_KEY="$(openssl rand -hex 32)"
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
  set_env AI_API_KEY "$AI_KEY"
fi

mkdir -p "$VAULT_PATH"
if grep -qE '^OBSIDIAN_VAULT_HOST_PATH=$' .env; then
  set_env OBSIDIAN_VAULT_HOST_PATH "$VAULT_PATH"
fi

if [ "$MODE" = "docker" ]; then
  echo "Starting Docker stack..."
  docker compose up -d --build
  docker compose ps
  echo
  echo "Running setup-mcp.sh to bootstrap .env..."
  bash scripts/setup-mcp.sh --no-validate || true
  echo
  echo "Xninetzy MCP running in Docker at $INSTALL_DIR"
  echo "Connect via stdio or http://127.0.0.1:8765/mcp (set XNINETZY_MCP_TRANSPORT=streamable-http)."
  exit 0
fi

echo "Running setup-mcp.sh to bootstrap .env and validate release gate..."
bash scripts/setup-mcp.sh

echo "Installing system dependencies (sqlite3, tesseract OCR, libatlas for FAISS)..."
case "$OS" in
  linux)
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y
      sudo apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng sqlite3 libatlas3-base liblapack3 \
        libgomp1 libxml2 libxslt1.1 libffi-dev libssl-dev
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y tesseract tesseract-langpack-eng sqlite \
        atlas lapack libgomp libxml2 libxslt openssl-devel
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -Sy --noconfirm tesseract tesseract-data-eng sqlite \
        atlas lapack libxml2 libxslt openssl
    else
      echo "no supported package manager detected; install tesseract+sqlite manually"
    fi
    ;;
  macos)
    if command -v brew >/dev/null 2>&1; then
      brew install tesseract sqlite
    else
      echo "Homebrew not found; install tesseract+sqlite manually"
    fi
    ;;
esac

echo "Installing Python deps (uv sync --all-extras)..."
uv sync --all-extras

echo "Installing Playwright Chromium (HEBAT browser)..."
uv run --no-project python -m playwright install chromium --with-deps || true

if [ "${XNINETZY_INSTALL_NEO4J:-false}" = "true" ]; then
  echo "Installing Neo4j (opt-in via XNINETZY_INSTALL_NEO4J=true)..."
  case "$OS" in
    linux)
      if command -v apt-get >/dev/null 2>&1; then
        curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/neo4j.gpg
        echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5" | sudo tee /etc/apt/sources.list.d/neo4j.list
        sudo apt-get update -y
        sudo apt-get install -y neo4j
      fi
      ;;
    macos)
      brew install neo4j
      ;;
  esac
  set_env NEO4J_ENABLED true
fi

echo "Running release gate..."
uv run --no-project python -m xninetzy.cli.supervisor release-check || true

echo
echo "Running smoke test (mcp_audit.py)..."
uv run --no-project python scripts/mcp_audit.py || true

echo
echo "================================================================"
echo "  Xninetzy MCP install summary"
echo "================================================================"
echo "  Install path : $INSTALL_DIR"
echo "  OS           : $OS"
echo "  Python       : $(uv run python -c 'import sys; print(sys.version.split()[0])' 2>/dev/null || echo 'unknown')"
echo
echo "  System deps installed:"
echo "    - sqlite3   : $(command -v sqlite3 >/dev/null && sqlite3 --version | head -1 || echo MISSING)"
echo "    - tesseract : $(command -v tesseract >/dev/null && tesseract --version 2>&1 | head -1 || echo MISSING)"
echo "    - openssl   : $(command -v openssl >/dev/null && openssl version || echo MISSING)"
if [ "${XNINETZY_INSTALL_NEO4J:-false}" = "true" ]; then
  echo "    - neo4j     : $(command -v neo4j >/dev/null && neo4j --version 2>&1 | head -1 || echo 'requested but missing')"
else
  echo "    - neo4j     : skipped (opt-in via XNINETZY_INSTALL_NEO4J=true)"
fi
echo "    - python deps: $(uv pip list 2>/dev/null | wc -l) packages installed"
echo
echo "  .env:"
echo "    - path          : $INSTALL_DIR/.env (mode 600)"
echo "    - AI_API_KEY    : $(grep -E '^AI_API_KEY=' .env | cut -d= -f2 | head -c 16)...$(grep -E '^AI_API_KEY=' .env | cut -d= -f2 | tail -c 5)"
echo "    - DATA_DIR      : $(grep -E '^DATA_DIR=' .env | cut -d= -f2)"
echo "    - OBSIDIAN_VAULT: $(grep -E '^OBSIDIAN_VAULT_HOST_PATH=' .env | cut -d= -f2)"
echo "    - LLM block     : $(grep -qE '^FLAZ_API_KEY=|^OPENAI_API_KEY=' .env && echo 'configured' || echo 'not configured (host supplies the model)')"
echo
echo "  Next:"
echo "    cd $INSTALL_DIR"
echo "    uv run python -m xninetzy.cli.supervisor start      # stdio MCP"
echo "    XNINETZY_MCP_TRANSPORT=streamable-http \\"
echo "      uv run python -m xninetzy.interfaces.mcp_server   # http://127.0.0.1:8765/mcp"
echo
echo "  Optional:"
echo "    XNINETZY_INSTALL_NEO4J=true bash scripts/install-mcp.sh   # add Neo4j"
echo "    uv run --no-project python scripts/mcp_audit.py --strict  # strict audit"
echo "================================================================"
