#!/usr/bin/env python3
"""Gate A verification for the final manifest-driven CBIS-DDSM experiment."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = PROJECT_ROOT / "manifests" / "cbis_group_split_seed42.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify final DL dataset paths, images and split integrity.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "experiments" / "final" / "dataset_verification.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))

    groups_to_splits: defaultdict[str, set[str]] = defaultdict(set)
    groups_to_labels: defaultdict[str, set[str]] = defaultdict(set)
    counts: Counter[str] = Counter()
    missing_paths, corrupt_images, invalid_rows = [], [], []
    for row in records:
        split, label, group_id, image_set = row.get("split"), row.get("label"), row.get("group_id"), row.get("image_set")
        relative_path = row.get("relative_path")
        if split not in {"train", "val", "test"} or label not in {"benign", "malignant"} or not group_id or image_set not in {"images", "images_roi"} or not relative_path:
            invalid_rows.append(row)
            continue
        groups_to_splits[group_id].add(split)
        groups_to_labels[group_id].add(label)
        counts[f"{split}/{label}/{image_set}"] += 1
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            missing_paths.append(relative_path)
            continue
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:
            corrupt_images.append({"path": relative_path, "error": str(exc)})

    split_groups = {split: {group for group, splits in groups_to_splits.items() if split in splits} for split in ("train", "val", "test")}
    result = {
        "manifest": str(args.manifest),
        "total_records": len(records),
        "valid_records": len(records) - len(invalid_rows),
        "counts": dict(sorted(counts.items())),
        "missing_paths": len(missing_paths),
        "corrupt_images": len(corrupt_images),
        "invalid_rows": len(invalid_rows),
        "mixed_label_groups": sum(len(labels) > 1 for labels in groups_to_labels.values()),
        "train_val_group_overlap": len(split_groups["train"] & split_groups["val"]),
        "train_test_group_overlap": len(split_groups["train"] & split_groups["test"]),
        "val_test_group_overlap": len(split_groups["val"] & split_groups["test"]),
        "missing_path_examples": missing_paths[:10],
        "corrupt_image_examples": corrupt_images[:10],
    }
    passed = not any(
        result[key]
        for key in (
            "missing_paths", "corrupt_images", "invalid_rows", "mixed_label_groups",
            "train_val_group_overlap", "train_test_group_overlap", "val_test_group_overlap",
        )
    )
    result["status"] = "PASS" if passed else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
