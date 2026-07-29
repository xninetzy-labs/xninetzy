from __future__ import annotations

import argparse
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = (
    SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else Path.cwd()
)
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


def read_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def update_env_values(env_path: Path, values: dict[str, str]) -> None:
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    elif ENV_EXAMPLE_PATH.exists():
        lines = ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines()
    else:
        raise RuntimeError(
            "Jalankan helper dari checkout host yang memiliki .env.example."
        )

    remaining = dict(values)
    updated: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in remaining:
            updated.append(f"{key}={remaining.pop(key)}")
        else:
            updated.append(line)
    if remaining:
        if updated and updated[-1]:
            updated.append("")
        updated.extend(f"{key}={value}" for key, value in remaining.items())

    temporary = env_path.with_name(f".{env_path.name}.tmp")
    try:
        temporary.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(env_path)
        env_path.chmod(0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(enable_cyber_campus: bool = False) -> None:
    example = read_values(ENV_EXAMPLE_PATH)
    current = read_values(ENV_PATH)
    updates = {
        key: value
        for key, value in example.items()
        if key not in current
    }
    if not current.get("AI_API_KEY"):
        updates["AI_API_KEY"] = secrets.token_urlsafe(48)
    mcp_key = (
        current.get("MCP_API_KEY")
        or current.get("WA_MCP_API_KEY")
        or secrets.token_urlsafe(48)
    )
    updates["MCP_API_KEY"] = mcp_key
    updates["WA_MCP_API_KEY"] = mcp_key
    admin_jid = current.get("ADMIN_JID") or current.get("HEBAT_NOTIFY_CHAT_ID")
    if admin_jid:
        updates["ADMIN_JID"] = admin_jid
    if enable_cyber_campus:
        required = {
            "HEBAT_USERNAME": current.get("HEBAT_USERNAME"),
            "HEBAT_PASSWORD": current.get("HEBAT_PASSWORD"),
            "ADMIN_JID": admin_jid,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Cyber Campus belum dapat diaktifkan. Lengkapi: "
                + ", ".join(missing)
            )
        updates["CYBER_CAMPUS_ENABLED"] = "true"
        updates["WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED"] = "true"
        if not current.get("WEB_ANALYSIS_ENCRYPTION_KEY"):
            updates["WEB_ANALYSIS_ENCRYPTION_KEY"] = Fernet.generate_key().decode(
                "ascii"
            )
    update_env_values(ENV_PATH, updates)
    print("Konfigurasi internal AI dan WA MCP tersimpan aman di .env.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-cyber-campus", action="store_true")
    args = parser.parse_args()
    main(enable_cyber_campus=args.enable_cyber_campus)
