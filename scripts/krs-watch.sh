#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${KRS_WATCH_CONTAINER:-xninetzy-ai-1}"
DB_PATH="${KRS_WATCH_DB_PATH:-/app/data/xninetzy.sqlite3}"
OWNER_SCOPE="${KRS_WATCH_OWNER:-local-owner}"
DEFAULT_LOG="${KRS_WATCH_LOG_FILE:-$HOME/.xninetzy/logs/krs-watcher.log}"

WATCH_MODE=0
INTERVAL_SECONDS=7
LOG_FILE=""

usage() {
  printf 'Pemantau watcher KRS Xninetzy dari host.\n\n'
  printf 'Usage:\n'
  printf '  %s                    status sekali jalan\n' "$0"
  printf '  %s --watch [opsi]     pantau terus-menerus (log + perubahan)\n' "$0"
  printf '  %s --once             status sekali jalan\n' "$0"
  printf '\nOpsi:\n'
  printf '  --interval N   detik antar cek (default 7, min 5)\n'
  printf '  --log FILE     file log untuk mode watch\n'
  printf '  -h, --help     bantuan ini\n'
  printf '\nEnv override: KRS_WATCH_CONTAINER, KRS_WATCH_DB_PATH, KRS_WATCH_OWNER, KRS_WATCH_LOG_FILE\n'
}

fetch_kv() {
  docker exec -i "$CONTAINER" python - "$DB_PATH" "$OWNER_SCOPE" <<'PY'
import shlex
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
scope = sys.argv[2]

w = conn.execute(
    "SELECT enabled, interval_seconds, started_at, last_tick_at, last_status, "
    "       last_error, last_mk_count, session_expired_notified, last_announcement "
    "FROM krs_watcher_state WHERE owner_scope = ?",
    (scope,),
).fetchone()

war = conn.execute(
    "SELECT armed, plan_hash, last_run_window, last_status, last_summary "
    "FROM krs_war_state WHERE owner_scope = ?",
    (scope,),
).fetchone()

def emit(key, value):
    print(f"{key}={shlex.quote('' if value is None else str(value))}")

w_keys = [
    ("W_ENABLED", "enabled"),
    ("W_INTERVAL", "interval_seconds"),
    ("W_STARTED", "started_at"),
    ("W_TICK", "last_tick_at"),
    ("W_STATUS", "last_status"),
    ("W_ERROR", "last_error"),
    ("W_MK", "last_mk_count"),
    ("W_EXPIRED_NOTIFIED", "session_expired_notified"),
    ("W_ANNOUNCEMENT", "last_announcement"),
]
war_keys = [
    ("WAR_ARMED", "armed"),
    ("WAR_PLAN_HASH", "plan_hash"),
    ("WAR_LAST_WINDOW", "last_run_window"),
    ("WAR_STATUS", "last_status"),
    ("WAR_SUMMARY", "last_summary"),
]

if w is not None:
    for shell_key, col in w_keys:
        emit(shell_key, w[col])
if war is not None:
    for shell_key, col in war_keys:
        emit(shell_key, war[col])
PY
}

load_state() {
  source <(fetch_kv)
}

enabled_label() {
  case "$1" in
    1) printf 'AKTIF' ;;
    0) printf 'mati' ;;
    *) printf '%s' "$1" ;;
  esac
}

armed_label() {
  case "$1" in
    1) printf 'armed' ;;
    0) printf 'disarm' ;;
    *) printf '%s' "$1" ;;
  esac
}

print_once() {
  load_state
  printf '%s\n' "=========================================="
  printf '%s\n' "Watcher KRS  | $(enabled_label "$W_ENABLED")"
  printf '%s\n' "Interval     | ${W_INTERVAL:-?} detik"
  printf '%s\n' "Mulai        | ${W_STARTED:-}"
  printf '%s\n' "Tick terakhir| ${W_TICK:-}"
  printf '%s\n' "Status       | ${W_STATUS:-}"
  printf '%s\n' "MK terambil  | ${W_MK:-}"
  if [ -n "${W_ERROR:-}" ]; then
    printf '%s\n' "Error        | $W_ERROR"
  fi
  if [ -n "${W_ANNOUNCEMENT:-}" ]; then
    printf '%s\n' "Pengumuman   | $W_ANNOUNCEMENT"
  fi
  printf '%s\n' "Expired notified | ${W_EXPIRED_NOTIFIED:-}"
  printf '%s\n' "------------------------------------------"
  printf '%s\n' "KRS War      | $(armed_label "$WAR_ARMED")"
  printf '%s\n' "Plan hash    | ${WAR_PLAN_HASH:-}"
  printf '%s\n' "Window       | ${WAR_LAST_WINDOW:-}"
  printf '%s\n' "Status war   | ${WAR_STATUS:-}"
  printf '%s\n' "Ringkasan    | ${WAR_SUMMARY:-}"
  printf '%s\n' "=========================================="
}

log_line() {
  local ts
  ts=$(date -Iseconds)
  printf '[%s] %s\n' "$ts" "$1" >> "$LOG_FILE"
}

run_watch() {
  LOG_FILE="${LOG_FILE:-$DEFAULT_LOG}"
  if [ "$LOG_FILE" = "NONE" ]; then
    LOG_FILE="/dev/null"
  else
    mkdir -p "$(dirname "$LOG_FILE")"
  fi
  printf 'Memantau watcher KRS tiap %s detik (Ctrl+C untuk stop). Log: %s\n' "$INTERVAL_SECONDS" "$LOG_FILE"
  print_once
  log_line "monitor_start interval=${INTERVAL_SECONDS}s"
  local prev_status="" prev_mk="" prev_error="" prev_armed=""
  while true; do
    sleep "$INTERVAL_SECONDS"
    if ! load_state; then
      printf '[%s] GAGAL ambil state dari container %s\n' "$(date -Iseconds)" "$CONTAINER"
      continue
    fi
    local ts
    ts=$(date -Iseconds)
    printf '[%s] status=%s mk=%s tick=%s error=%s\n' \
      "$ts" "${W_STATUS:-}" "${W_MK:-}" "${W_TICK:-}" "${W_ERROR:-}"
    log_line "tick status=${W_STATUS:-} mk=${W_MK:-} tick=${W_TICK:-} error=${W_ERROR:-}"
    if [ "${W_STATUS:-}" != "$prev_status" ] && [ -n "$prev_status" ]; then
      log_line "STATUS_CHANGE ${prev_status:-} -> ${W_STATUS:-}"
      printf '  [CHANGE] status: %s -> %s\n' "${prev_status:-}" "${W_STATUS:-}"
    fi
    if [ "${W_MK:-}" != "$prev_mk" ] && [ -n "$prev_mk" ]; then
      log_line "MK_CHANGE ${prev_mk:-} -> ${W_MK:-}"
      printf '  [CHANGE] MK terambil: %s -> %s\n' "${prev_mk:-}" "${W_MK:-}"
    fi
    if [ "${W_ERROR:-}" != "$prev_error" ] && [ -n "${W_ERROR:-}" ]; then
      log_line "ERROR_SET ${W_ERROR:-}"
      printf '  [CHANGE] error baru: %s\n' "${W_ERROR:-}"
    fi
    if [ "${WAR_ARMED:-}" != "$prev_armed" ] && [ -n "$prev_armed" ]; then
      log_line "WAR_ARMED_CHANGE ${prev_armed:-} -> ${WAR_ARMED:-}"
      printf '  [CHANGE] KRS War: %s -> %s\n' "${prev_armed:-}" "${WAR_ARMED:-}"
    fi
    prev_status="${W_STATUS:-}"
    prev_mk="${W_MK:-}"
    prev_error="${W_ERROR:-}"
    prev_armed="${WAR_ARMED:-}"
  done
}

if [ $# -eq 0 ]; then
  print_once
  exit 0
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --watch)
      WATCH_MODE=1
      shift
      ;;
    --once)
      WATCH_MODE=0
      shift
      ;;
    --interval)
      INTERVAL_SECONDS="$2"
      shift 2
      ;;
    --interval=*)
      INTERVAL_SECONDS="${1#*=}"
      shift
      ;;
    --log)
      LOG_FILE="$2"
      shift 2
      ;;
    --log=*)
      LOG_FILE="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Argumen tidak dikenal: %s\n' "$1"
      usage
      exit 1
      ;;
  esac
done

if ! [[ "$INTERVAL_SECONDS" =~ ^[0-9]+$ ]] || [ "$INTERVAL_SECONDS" -lt 5 ]; then
  printf 'Interval harus angka >= 5 detik.\n'
  exit 1
fi

if [ "$WATCH_MODE" -eq 1 ]; then
  run_watch
else
  print_once
fi
