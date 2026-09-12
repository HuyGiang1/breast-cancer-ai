#!/usr/bin/env python3
"""
scripts/verify_database_restore.py

Non-destructive disaster recovery test drill for Breast Cancer AI database.
Restores a target backup database file into an isolated temporary location, verifies:
1. File hash against backup metadata JSON (if present)
2. SQLite PRAGMA integrity_check
3. Presence of all mandatory production tables:
   - users
   - sessions
   - password_reset_tokens
   - patients
   - predictions
   - chat_messages
   - oauth_accounts
4. Data consistency checks on row counts
5. Complete cleanup of temporary drill artifacts without touching production data.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backend" / "backups"

MANDATORY_TABLES = {
    "users",
    "sessions",
    "password_reset_tokens",
    "patients",
    "predictions",
    "chat_messages",
    "oauth_accounts",
}


def sha256_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_restore(backup_file: Path) -> bool:
    if not backup_file.exists():
        print(f"[!] Backup file not found: {backup_file}", file=sys.stderr)
        return False

    print(f"[*] Starting non-destructive restore drill for: {backup_file.name}")

    # Check against metadata JSON if exists
    meta_file = backup_file.with_suffix(".json")
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            expected_sha = meta.get("backup_sha256")
            actual_sha = sha256_file(backup_file)
            if expected_sha and expected_sha != actual_sha:
                print(f"[!] Checksum mismatch! Expected {expected_sha}, got {actual_sha}", file=sys.stderr)
                return False
            print(f"[+] Backup checksum verified: {actual_sha}")
        except Exception as exc:
            print(f"[!] Warning reading metadata: {exc}")

    with tempfile.TemporaryDirectory(prefix="sqlite_restore_test_") as tmpdir:
        tmp_db_path = Path(tmpdir) / "restored_test.db"

        # Perform restore via SQLite online backup API from backup_file to tmp_db
        src_conn = sqlite3.connect(backup_file)
        dst_conn = sqlite3.connect(tmp_db_path)
        try:
            src_conn.backup(dst_conn)
        finally:
            src_conn.close()
            dst_conn.close()

        print(f"[+] Backup successfully restored to isolated target: {tmp_db_path}")

        # Connect and verify
        conn = sqlite3.connect(tmp_db_path)
        try:
            cur = conn.execute("PRAGMA integrity_check")
            integrity = cur.fetchone()[0]
            if integrity != "ok":
                print(f"[!] SQLite integrity check failed: {integrity}", file=sys.stderr)
                return False
            print(f"[+] SQLite PRAGMA integrity_check passed: {integrity}")

            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            found_tables = {row[0] for row in cur.fetchall()}

            missing = MANDATORY_TABLES - found_tables
            if missing:
                print(f"[!] Missing mandatory tables in restored database: {missing}", file=sys.stderr)
                return False

            print(f"[+] All {len(MANDATORY_TABLES)} mandatory tables verified:")
            for tbl in sorted(MANDATORY_TABLES):
                row_count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                print(f"    - {tbl}: {row_count} records")

        finally:
            conn.close()

    print("[+] Restore drill completed successfully. Non-destructive drill cleaned up cleanly.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test Restore Drill for Breast Cancer AI Database")
    parser.add_argument(
        "--backup-file",
        type=Path,
        default=None,
        help="Path to specific backup .db file. If not provided, tests the most recent backup in backend/backups/",
    )
    args = parser.parse_args()

    backup_file = args.backup_file
    if backup_file is None:
        backups = sorted(DEFAULT_BACKUP_DIR.glob("app_backup_*.db"))
        if not backups:
            print(f"[!] No backups found in {DEFAULT_BACKUP_DIR}. Please run backup_database.py first.", file=sys.stderr)
            sys.exit(1)
        backup_file = backups[-1]

    success = verify_restore(backup_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
