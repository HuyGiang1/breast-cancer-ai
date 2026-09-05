#!/usr/bin/env python3
"""Safely restore a SQLite backup without silently replacing a destination."""

from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def integrity_check(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"SQLite integrity check failed for {path}: {result}")


def sqlite_copy(source: Path, destination: Path) -> None:
    with sqlite3.connect(source) as source_connection, sqlite3.connect(destination) as destination_connection:
        source_connection.backup(destination_connection)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--backup", required=True, type=Path, help="Existing SQLite backup to restore from.")
    command.add_argument("--database", required=True, type=Path, help="Destination SQLite database path.")
    command.add_argument(
        "--confirm-overwrite",
        action="store_true",
        help="Required when the destination database already exists.",
    )
    return command


def main() -> int:
    args = parser().parse_args()
    source = args.backup.expanduser().resolve()
    destination = args.database.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Backup source does not exist: {source}")
    integrity_check(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination_exists = destination.exists()
    if destination_exists and not args.confirm_overwrite:
        raise SystemExit("Destination exists; re-run with --confirm-overwrite after verifying the backup source.")

    pre_restore_backup: Path | None = None
    if destination_exists:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pre_restore_backup = destination.with_name(f"{destination.stem}.pre-restore-{timestamp}{destination.suffix}")
        sqlite_copy(destination, pre_restore_backup)
        integrity_check(pre_restore_backup)

    temporary = destination.with_name(f".{destination.name}.restore-tmp")
    if temporary.exists():
        raise SystemExit(f"Temporary restore path already exists: {temporary}")
    try:
        sqlite_copy(source, temporary)
        integrity_check(temporary)
        os.replace(temporary, destination)
        integrity_check(destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(f"RESTORE SUCCESS: {destination}")
    if pre_restore_backup is not None:
        print(f"PRE_RESTORE_BACKUP: {pre_restore_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
