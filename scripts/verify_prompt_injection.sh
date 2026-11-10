#!/usr/bin/env bash
# Read-only prompt integrity check. Default retains installed-file inspection.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--canonical" ]]; then
  shift
  exec "${PYTHON:-python3}" "$SCRIPT_DIR/validate_prompt_contract.py" "$@"
fi
exec "${PYTHON:-python3}" "$SCRIPT_DIR/validate_prompt_contract.py" --installed "$@"
