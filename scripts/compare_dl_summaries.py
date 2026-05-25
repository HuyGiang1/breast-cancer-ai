#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DL_DIR = PROJECT_ROOT / "models" / "deep_learning"


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def metric_value(payload: dict, *keys: str):
    for key in keys:
        if key in payload:
            return payload.get(key)
    return None


def main():
    print("DL summary comparison")
    summary_paths = sorted(DL_DIR.glob("*_summary.json"))
    if not summary_paths:
        print("- no summary files found")
        return

    for path in summary_paths:
        payload = load_json(path)
        name = path.stem.removesuffix("_summary")
        if payload is None:
            print(f"- {name}: unreadable")
            continue

        val_auc = metric_value(payload, "val_auc")
        test_auc = metric_value(payload, "test_tta_auc", "test_auc")
        val_acc = metric_value(payload, "val_accuracy", "val_acc", "validation_accuracy")
        test_acc = metric_value(payload, "test_accuracy", "test_tta_accuracy", "test_acc")
        print(
            f"- {name}: "
            f"val_auc={val_auc} "
            f"test_auc={test_auc} "
            f"val_acc={val_acc} "
            f"test_acc={test_acc}"
        )


if __name__ == "__main__":
    main()
