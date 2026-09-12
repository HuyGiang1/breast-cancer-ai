"""
tests/test_database_concurrency.py

Unit tests for database pragmas, WAL mode, online hot backup,
and non-destructive restore verification.
"""

from pathlib import Path
import sqlite3
import tempfile
from app.core.database import Database
from scripts.backup_database import backup_database
from scripts.verify_database_restore import verify_restore


def test_database_pragmas_and_wal():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_app.db"
        test_db = Database(test_db_path)
        test_db.init()

        with test_db.connect() as conn:
            # Check journal_mode
            cur = conn.execute("PRAGMA journal_mode")
            journal_mode = cur.fetchone()[0].lower()
            assert journal_mode == "wal", f"Expected WAL mode, got {journal_mode}"

            # Check foreign_keys
            cur = conn.execute("PRAGMA foreign_keys")
            assert cur.fetchone()[0] == 1

            # Check busy_timeout
            cur = conn.execute("PRAGMA busy_timeout")
            assert cur.fetchone()[0] == 5000


def test_backup_and_restore_cycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_db_path = tmp_path / "source.db"
        backup_dir = tmp_path / "backups"

        # Initialize and populate sample records
        db_inst = Database(test_db_path)
        db_inst.init()
        db_inst.execute(
            "INSERT INTO users (email, full_name, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("test@test.local", "Test User", "hash123", "user", "2026-09-12T00:00:00Z", "2026-09-12T00:00:00Z"),
        )

        # Run online backup
        metadata = backup_database(test_db_path, backup_dir, keep=5)
        assert metadata["integrity_status"] == "ok"
        assert metadata["table_counts"]["users"] == 1

        backup_file = Path(metadata["backup_path"])
        assert backup_file.exists()

        # Run non-destructive restore drill
        assert verify_restore(backup_file) is True
