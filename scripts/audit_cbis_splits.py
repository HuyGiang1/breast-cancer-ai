#!/usr/bin/env python3
"""Audit CBIS-DDSM processed image splits for cross-split study leakage.

The processed filenames in this project use a stable prefix before "__". That
prefix is treated as a study-level identifier for a conservative leakage check.
This script does not move or delete files.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit processed CBIS-DDSM image splits")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/cbis_ddsm/processed/images"),
        help="Directory containing train/val/test class folders.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional generated split manifest CSV to audit instead of folder layout.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def image_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for suffix in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        files.extend(root.glob(f"*/*/{suffix}"))
    return sorted(files)


def study_prefix(path: Path) -> str:
    return path.name.split("__", 1)[0]


def audit(data_root: Path) -> dict:
    files = image_files(data_root)
    class_counts: dict[str, int] = defaultdict(int)
    prefix_counts: dict[str, int] = defaultdict(int)
    prefix_to_splits: dict[str, set[str]] = defaultdict(set)

    for path in files:
        split = path.parts[-3]
        label = path.parts[-2]
        prefix = study_prefix(path)
        class_counts[f"{split}/{label}"] += 1
        prefix_counts[prefix] += 1
        prefix_to_splits[prefix].add(split)

    cross_split = {
        prefix: sorted(splits)
        for prefix, splits in prefix_to_splits.items()
        if len(splits) > 1
    }

    return {
        "data_root": str(data_root),
        "total_images": len(files),
        "unique_study_prefixes": len(prefix_to_splits),
        "class_counts": dict(sorted(class_counts.items())),
        "duplicated_prefixes_anywhere": sum(1 for count in prefix_counts.values() if count > 1),
        "cross_split_duplicate_prefix_count": len(cross_split),
        "cross_split_examples": dict(list(sorted(cross_split.items()))[:25]),
        "leakage_risk": "CRITICAL" if cross_split else "not_detected_by_prefix_audit",
    }


def audit_manifest(manifest_path: Path) -> dict:
    split_to_groups: dict[str, set[str]] = defaultdict(set)
    class_counts: dict[str, int] = defaultdict(int)
    group_labels: dict[str, set[str]] = defaultdict(set)
    original_splits: dict[str, set[str]] = defaultdict(set)
    total_rows = 0

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"split", "label", "group_id", "original_split"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing required columns: {sorted(missing)}")

        for row in reader:
            total_rows += 1
            split = row["split"]
            label = row["label"]
            group_id = row["group_id"]
            split_to_groups[split].add(group_id)
            group_labels[group_id].add(label)
            original_splits[group_id].add(row["original_split"])
            class_counts[f"{split}/{label}"] += 1

    overlaps = {
        "train_val": len(split_to_groups["train"] & split_to_groups["val"]),
        "train_test": len(split_to_groups["train"] & split_to_groups["test"]),
        "val_test": len(split_to_groups["val"] & split_to_groups["test"]),
    }
    mixed_label_groups = {
        group_id: sorted(labels)
        for group_id, labels in group_labels.items()
        if len(labels) > 1
    }
    original_cross_split = {
        group_id: sorted(splits)
        for group_id, splits in original_splits.items()
        if len(splits) > 1
    }

    return {
        "manifest": str(manifest_path),
        "total_rows": total_rows,
        "unique_groups": len(group_labels),
        "class_counts": dict(sorted(class_counts.items())),
        "overlap_counts": overlaps,
        "mixed_label_group_count": len(mixed_label_groups),
        "mixed_label_group_examples": dict(list(sorted(mixed_label_groups.items()))[:25]),
        "original_cross_split_group_count": len(original_cross_split),
        "original_cross_split_examples": dict(list(sorted(original_cross_split.items()))[:25]),
        "leakage_risk": "not_detected_by_manifest_audit" if not any(overlaps.values()) else "CRITICAL",
    }


def main() -> int:
    args = parse_args()
    result = audit_manifest(args.manifest) if args.manifest else audit(args.data_root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if args.manifest:
            print(f"Manifest: {result['manifest']}")
            print(f"Total rows: {result['total_rows']}")
            print(f"Unique groups: {result['unique_groups']}")
            print(f"Overlap counts: {result['overlap_counts']}")
            print(f"Mixed-label groups: {result['mixed_label_group_count']}")
        else:
            print(f"Data root: {result['data_root']}")
            print(f"Total images: {result['total_images']}")
            print(f"Unique study prefixes: {result['unique_study_prefixes']}")
            print(f"Cross-split duplicate prefixes: {result['cross_split_duplicate_prefix_count']}")
        print("Class counts:")
        for key, count in result["class_counts"].items():
            print(f"- {key}: {count}")
        print(f"Leakage risk: {result['leakage_risk']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
