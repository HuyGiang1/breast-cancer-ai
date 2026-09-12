#!/usr/bin/env python3
"""
scripts/backup_database.py

Online SQLite backup utility for Breast Cancer AI production database.
Uses Python sqlite3 online backup API (source_conn.backup(dest_conn)) to safely
create consistent hot backups even while writes and reads occur concurrently.

Features:
- Online hot backup (no downtime required, safe with WAL mode)
- SHA-256 checksum generation for backup integrity verification
- Target database PRAGMA integrity_check verification
- JSON metadata summary output
- Optional retention rotation (--keep N)
"""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "data" / "app.db"
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backend" / "backups"


def sha256_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cursor.fetchone()[0])


def backup_database(
    source_path: Path,
    backup_dir: Path,
    keep: int = 14,
) -> dict:
    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found at {source_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    backup_file = backup_dir / f"app_backup_{timestamp}.db"

    print(f"[*] Starting online backup of {source_path} -> {backup_file}...")

    # Connect to source with WAL support and timeout
    src_conn = sqlite3.connect(source_path, timeout=30.0)
    dst_conn = sqlite3.connect(backup_file)

    try:
        # Online SQLite hot backup
        src_conn.backup(dst_conn, pages=100, sleep=0.01)
        dst_conn.close()
    finally:
        src_conn.close()

    print("[*] Hot backup completed. Running post-backup integrity validation...")

    # Verify backup database integrity
    verify_conn = sqlite3.connect(backup_file)
    try:
        cur = verify_conn.execute("PRAGMA integrity_check")
        status = cur.fetchone()[0]
        if status != "ok":
            raise RuntimeError(f"Integrity check failed on backup: {status}")

        # Gather table stats
        tables = [
            row[0]
            for row in verify_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        table_counts = {t: count_rows(verify_conn, t) for t in tables}
    finally:
        verify_conn.close()

    backup_hash = sha256_file(backup_file)
    backup_size = backup_file.stat().st_size

    metadata = {
        "timestamp_utc": timestamp,
        "source_path": str(source_path.resolve()),
        "backup_path": str(backup_file.resolve()),
        "backup_sha256": backup_hash,
        "backup_size_bytes": backup_size,
        "integrity_status": "ok",
        "table_counts": table_counts,
    }

    meta_file = backup_file.with_suffix(".json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[+] Backup successfully verified: {backup_file.name}")
    print(f"    SHA-256: {backup_hash}")
    print(f"    Size: {backup_size:,} bytes")
    print(f"    Tables: {table_counts}")

    # Rotate old backups if keep > 0
    if keep > 0:
        backups = sorted(backup_dir.glob("app_backup_*.db"))
        if len(backups) > keep:
            to_remove = backups[:-keep]
            for old_backup in to_remove:
                old_meta = old_backup.with_suffix(".json")
                print(f"[*] Removing old backup beyond retention limit ({keep}): {old_backup.name}")
                old_backup.unlink(missing_ok=True)
                old_meta.unlink(missing_ok=True)

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Backup Breast Cancer AI SQLite Database")
    parser.add_argument(
        "--db-path",
        "--database",
        dest="db_path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to source SQLite database (default: backend/data/app.db)",
    )
    parser.add_argument(
        "--backup-dir",
        "--output-dir",
        dest="backup_dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Directory to store backups (default: backend/backups)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=14,
        help="Number of backups to keep (default: 14, 0 = keep all)",
    )

    args = parser.parse_args()
    try:
        backup_database(args.db_path, args.backup_dir, args.keep)
    except Exception as exc:
        print(f"[!] Backup failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
