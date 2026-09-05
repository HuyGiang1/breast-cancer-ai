#!/usr/bin/env python3
"""Create a timestamped SQLite backup using SQLite's safe backup API."""
from __future__ import annotations
import argparse, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--database", type=Path, default=ROOT / "backend/data/app.db")
parser.add_argument("--output-dir", type=Path, default=ROOT / "backups")
args = parser.parse_args()
if not args.database.is_file(): raise SystemExit("Database does not exist.")
args.output_dir.mkdir(parents=True, exist_ok=True)
target = args.output_dir / f"app-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.db"
with sqlite3.connect(args.database) as source, sqlite3.connect(target) as destination: source.backup(destination)
if not target.is_file() or target.stat().st_size == 0: raise SystemExit("Backup validation failed.")
print(target)
