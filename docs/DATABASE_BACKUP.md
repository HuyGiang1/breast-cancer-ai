# SQLite Backup and Restore

This project uses SQLite only for the research/demo application state. Model artifacts and research outputs are not stored in the application database.

## Backup

Create a timestamped backup using SQLite's backup API:

```bash
python3 scripts/backup_database.py --database backend/data/app.db --output-dir backups
```

Store the resulting file outside the deployment host when practical. Backups can contain user-entered data and must not be committed to Git.

## Restore

Stop the API before restoring its live database. The restore command requires both an explicit source and destination and refuses to overwrite an existing database unless the operator explicitly confirms it:

```bash
python3 scripts/restore_database.py \
  --backup backups/app-YYYYMMDDTHHMMSSZ.db \
  --database backend/data/app.db \
  --confirm-overwrite
```

When replacing a destination, the script first writes an adjacent timestamped `*.pre-restore-*.db` backup, restores through a temporary SQLite file, atomically replaces the destination, and checks `PRAGMA integrity_check` after restoration.

## Rehearsal

On 2026-09-05 the workflow is rehearsed only against a temporary SQLite database: create a known row, make a backup, mutate the live temporary database, restore, confirm the known row is present again, and verify `PRAGMA integrity_check = ok`. The application database is never used for this rehearsal.
