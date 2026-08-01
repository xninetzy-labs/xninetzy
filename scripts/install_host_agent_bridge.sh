#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_DIR="${XNINETZY_REPOSITORY_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
UV_BIN="$(command -v uv || true)"

if [ -z "$UV_BIN" ]; then
  printf '%s\n' "uv belum terpasang. Install uv lalu jalankan ulang script ini."
  exit 1
fi
if ! command -v openssl >/dev/null 2>&1; then
  printf '%s\n' "openssl belum terpasang dan diperlukan untuk token bridge."
  exit 1
fi
if ! command -v systemctl >/dev/null 2>&1; then
  printf '%s\n' "systemd user service tidak tersedia pada host ini."
  exit 1
fi

set_env() {
  local key="$1"
  local value="$2"
  local temporary
  temporary="$(mktemp)"
  awk -v key="$key" -v value="$value" '
    index($0, key "=") == 1 { print key "=" value; found = 1; next }
    { print }
    END { if (!found) print key "=" value }
  ' "$REPOSITORY_DIR/.env" > "$temporary"
  mv "$temporary" "$REPOSITORY_DIR/.env"
  chmod 600 "$REPOSITORY_DIR/.env"
}

if [ ! -f "$REPOSITORY_DIR/.env" ]; then
  cp "$REPOSITORY_DIR/.env.example" "$REPOSITORY_DIR/.env"
  chmod 600 "$REPOSITORY_DIR/.env"
fi

bridge_token="$(awk -F= '$1 == "CODING_AGENT_HOST_BRIDGE_TOKEN" { print substr($0, index($0, "=") + 1) }' "$REPOSITORY_DIR/.env")"
if [ -z "$bridge_token" ]; then
  bridge_token="$(openssl rand -hex 32)"
  set_env CODING_AGENT_HOST_BRIDGE_TOKEN "$bridge_token"
fi
set_env CODING_AGENT_ENABLED true
set_env CODING_AGENT_DEFAULT opencode
set_env CODING_AGENT_EXECUTION_MODE host_bridge
set_env CODING_AGENT_HOST_BRIDGE_URL http://host.docker.internal:8765
for runtime_binary in codex claude opencode; do
  binary_path="$(command -v "$runtime_binary" || true)"
  if [ -n "$binary_path" ]; then
    case "$runtime_binary" in
      codex) set_env CODEX_BIN "$binary_path" ;;
      claude) set_env CLAUDE_CODE_BIN "$binary_path" ;;
      opencode) set_env OPENCODE_BIN "$binary_path" ;;
    esac
  fi
done

unit_dir="$HOME/.config/systemd/user"
unit_path="$unit_dir/xninetzy-host-agent-bridge.service"
mkdir -p "$unit_dir"
temporary_unit="$(mktemp)"
cat > "$temporary_unit" <<UNIT
[Unit]
Description=Xninetzy host coding-agent bridge
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$REPOSITORY_DIR
EnvironmentFile=$REPOSITORY_DIR/.env
Environment=PATH=$PATH
Environment=MCP_RUNTIME_MODE=host
Environment=CODING_AGENT_EXECUTION_MODE=local
Environment=CODING_AGENT_HOST_WORKSPACE=$REPOSITORY_DIR
Environment=CODING_AGENT_HOST_ALLOWED_ROOT=$REPOSITORY_DIR
ExecStart=$UV_BIN run --directory $REPOSITORY_DIR/services/ai --no-dev python -m app.xninetzy.interfaces.host_agent_bridge
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
UNIT
mv "$temporary_unit" "$unit_path"
chmod 600 "$unit_path"

if command -v loginctl >/dev/null 2>&1; then
  loginctl enable-linger "$USER" >/dev/null 2>&1 || true
fi
systemctl --user daemon-reload
systemctl --user enable --now xninetzy-host-agent-bridge.service
printf '%s\n' "Host coding-agent bridge aktif pada 127.0.0.1:8765."
printf '%s\n' "Status: systemctl --user status xninetzy-host-agent-bridge"
