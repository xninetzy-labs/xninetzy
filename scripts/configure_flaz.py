from __future__ import annotations

import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


def update_env_values(env_path: Path, values: dict[str, str]) -> None:
    """Atomically update selected .env keys without printing their values."""
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    elif ENV_EXAMPLE_PATH.exists():
        lines = ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

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


def main() -> None:
    api_key = getpass.getpass("Masukkan FLAZ API Key: ").strip()
    if not api_key:
        raise SystemExit("FLAZ API Key tidak boleh kosong.")

    update_env_values(
        ENV_PATH,
        {
            "FLAZ_API_KEY": api_key,
            "FLAZ_BASE_URL": "https://ai.flaz.id/v1",
            "FLAZ_MODEL": "deepseek-v4-pro",
        },
    )
    print("Konfigurasi Flaz tersimpan aman di .env (permission 600).")


if __name__ == "__main__":
    main()
