# Production SQLite Backup and Disaster Recovery Runbook

This document details the production backup, integrity validation, and disaster recovery procedures for the Breast Cancer AI SQLite database (`backend/data/app.db`).

---

## 1. Architectural Overview

The Breast Cancer AI application uses SQLite in **WAL (Write-Ahead Logging)** mode with busy timeout handling:
- **Journal Mode**: `PRAGMA journal_mode = WAL`
- **Synchronous Mode**: `PRAGMA synchronous = NORMAL`
- **Busy Timeout**: `PRAGMA busy_timeout = 5000` (5.0s wait on locks)
- **Connection Timeout**: 30.0s

### Zero-Downtime Hot Backups
Backups are created using the official Python SQLite Online Backup API (`source_conn.backup(dest_conn)`). This reads pages sequentially under SQLite's internal lock coordination without blocking concurrent reads or writes, and without requiring container or server restarts.

---

## 2. Automated Hot Backup Execution

### Command
```bash
python3 scripts/backup_database.py \
  --database backend/data/app.db \
  --output-dir backend/backups \
  --keep 14
```

### Outputs
For each backup run:
1. `backend/backups/app_backup_YYYYMMDD_HHMMSSZ.db`: The verified SQLite database file.
2. `backend/backups/app_backup_YYYYMMDD_HHMMSSZ.json`: Metadata summary including:
   - `timestamp_utc`
   - `source_path`
   - `backup_sha256`
   - `backup_size_bytes`
   - `integrity_status`
   - `table_counts` (row counts for `users`, `sessions`, `patients`, `predictions`, etc.)

### Retention Policy
The `--keep 14` flag automatically retains the 14 most recent backup snapshots and purges older pairs (`.db` and `.json`) to manage disk space.

### Production Cron Configuration
Schedule daily backups at 02:00 UTC via crontab:
```cron
# Daily online SQLite database backup at 02:00 UTC (14-day retention)
0 2 * * * cd /opt/breast-cancer-ai && /usr/bin/python3 scripts/backup_database.py --keep 14 >> /var/log/bcai_backup.log 2>&1
```

---

## 3. Non-Destructive Restore Drill

Operators should regularly test backup recoverability without affecting live data using the automated non-destructive restore drill:

```bash
# Verify the latest backup automatically in an isolated temporary location
python3 scripts/verify_database_restore.py

# Or verify a specific historical backup
python3 scripts/verify_database_restore.py --backup-file backend/backups/app_backup_20260912_042039Z.db
```

The drill performs:
1. Checksum comparison against the `.json` manifest.
2. Isolated database extraction into a secure temporary directory.
3. `PRAGMA integrity_check` validation.
4. Mandatory table presence checks (`users`, `sessions`, `patients`, `predictions`, `chat_messages`, `oauth_accounts`, `password_reset_tokens`).
5. Safe teardown of temporary drill resources.

---

## 4. Emergency Production Disaster Recovery Procedure

When restoring a backup to replace a corrupted or compromised production database:

> [!WARNING]
> Stop the API container before restoring a live production database to prevent in-flight writes during atomic replacement.

### Step 1: Stop API Service
```bash
docker compose -f docker-compose.production.yml stop api
```

### Step 2: Perform Verified Atomic Restore
```bash
python3 scripts/restore_database.py \
  --backup backend/backups/app_backup_20260912_042039Z.db \
  --database backend/data/app.db \
  --confirm-overwrite
```

Safety mechanisms executed by `restore_database.py`:
- Validates the source backup integrity via `PRAGMA integrity_check` before proceeding.
- Creates an automatic emergency safety snapshot of the destination: `app.pre-restore-<timestamp>.db`.
- Restores to a temporary file (`.app.db.restore-tmp`).
- Validates the temporary file's integrity.
- Atomically moves the temporary file to `app.db` via `os.replace()`.
- Validates the final destination integrity.

### Step 3: Verify and Restart API Service
```bash
# Verify tables and integrity
python3 -c "import sqlite3; c = sqlite3.connect('backend/data/app.db'); print('Integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])"

# Start the API container
docker compose -f docker-compose.production.yml start api

# Check container health probes
curl -f http://localhost:8000/readyz
```

---

## 5. Security and Data Confidentiality

- **Confidentiality**: Backups contain user account identifiers, password hashes, and research patient records. Backups must **never** be committed to Git or exposed via the web server.
- **Offsite Archival**: Operators should sync `backend/backups/` to an encrypted, access-restricted S3/GCS bucket with SSE-KMS (Server-Side Encryption) and lifecycle deletion rules.
- **Permissions**: Ensure file mode `0600` on production database and backup files so only the application user can read them.
