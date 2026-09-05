#!/usr/bin/env python3
"""Package the frozen final research snapshot for deployment without experiments/."""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "experiments/final/FINAL_RESULTS_SNAPSHOT.json"
TARGET = ROOT / "backend/app/static/final_results_snapshot.json"

def main() -> None:
    payload = SOURCE.read_bytes()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(payload)
    if hashlib.sha256(TARGET.read_bytes()).digest() != hashlib.sha256(payload).digest():
        raise RuntimeError("Packaged runtime snapshot does not match frozen source.")
    print("Runtime metadata prepared")

if __name__ == "__main__": main()
