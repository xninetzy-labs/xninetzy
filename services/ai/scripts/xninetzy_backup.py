from __future__ import annotations

import argparse
import json

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.backup.service import (
    create_backup,
    list_backups,
    restore_backup,
    verify_backup,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup or restore Xninetzy state")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create")
    subparsers.add_parser("list")
    verify = subparsers.add_parser("verify")
    verify.add_argument("name")
    restore = subparsers.add_parser("restore")
    restore.add_argument("name")
    restore.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    settings = get_settings()

    if args.command == "create":
        result = create_backup(
            settings.SQLITE_PATH,
            settings.VECTOR_DATA_DIR,
            settings.BACKUP_DIR,
            retention=settings.BACKUP_RETENTION,
        )
    elif args.command == "list":
        result = list_backups(settings.BACKUP_DIR)
    elif args.command == "verify":
        result = verify_backup(settings.BACKUP_DIR, args.name)
    else:
        result = restore_backup(
            settings.BACKUP_DIR,
            args.name,
            settings.SQLITE_PATH,
            settings.VECTOR_DATA_DIR,
            confirmed=args.confirm,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
