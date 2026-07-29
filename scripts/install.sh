#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_URL="https://github.com/misbahul45/xninetzy.git"
INSTALL_DIR="${XNINETZY_INSTALL_DIR:-$HOME/xninetzy}"

command -v git >/dev/null 2>&1 || { echo "Git belum terpasang."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker belum terpasang."; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "OpenSSL belum terpasang."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose plugin belum tersedia."; exit 1; }

if [ -f "./docker-compose.yml" ] && [ -f "./.env.example" ]; then
  INSTALL_DIR="$(pwd)"
elif [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  git clone "$REPOSITORY_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
cp -n .env.example .env
chmod 600 .env

set_env() {
  local key="$1"
  local value="$2"
  local value_file
  local output_file
  value_file="$(mktemp)"
  output_file="$(mktemp)"
  chmod 600 "$value_file" "$output_file"
  printf '%s' "$value" > "$value_file"
  awk -v key="$key" -v value_file="$value_file" '
    BEGIN { getline value < value_file; close(value_file); found = 0 }
    index($0, key "=") == 1 { print key "=" value; found = 1; next }
    { print }
    END { if (!found) print key "=" value }
  ' .env > "$output_file"
  mv "$output_file" .env
  rm -f "$value_file"
  chmod 600 .env
}

default_vault="$HOME/Documents/Xninetzy Vault"
printf 'Lokasi Obsidian vault [%s]: ' "$default_vault"
read -r vault_path </dev/tty
vault_path="${vault_path:-$default_vault}"
mkdir -p "$vault_path"

printf 'Nomor WhatsApp admin (contoh 62812...): '
read -r admin_number </dev/tty
admin_number="${admin_number%%@*}"
[ -n "$admin_number" ] || { echo "Nomor WhatsApp admin wajib diisi."; exit 1; }

printf 'Masukkan FLAZ API Key: '
read -rs flaz_key </dev/tty
printf '\n'
[ -n "$flaz_key" ] || { echo "FLAZ API Key wajib diisi."; exit 1; }

ai_key="$(openssl rand -hex 32)"
mcp_key="$(openssl rand -hex 32)"
fernet_key="$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n')"

set_env HOST_UID "$(id -u)"
set_env HOST_GID "$(id -g)"
set_env OBSIDIAN_VAULT_HOST_PATH "$vault_path"
set_env ADMIN_JID "$admin_number@s.whatsapp.net"
set_env FLAZ_API_KEY "$flaz_key"
set_env AI_API_KEY "$ai_key"
set_env MCP_API_KEY "$mcp_key"
set_env WA_MCP_API_KEY "$mcp_key"
set_env WEB_ANALYSIS_ENCRYPTION_KEY "$fernet_key"
set_env WA_LOGIN_MODE qr

flaz_key=""
ai_key=""
mcp_key=""
fernet_key=""

docker compose config -q
docker compose up --build -d ai wa-enggine
docker compose ps

echo
echo "Xninetzy terpasang di $INSTALL_DIR"
echo "Buka log untuk scan QR:"
echo "cd \"$INSTALL_DIR\" && docker compose logs -f wa-enggine"
