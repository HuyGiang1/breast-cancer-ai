#!/usr/bin/env python3
"""Audit CBIS-DDSM processed image splits for cross-split study leakage.

The processed filenames in this project use a stable prefix before "__". That
prefix is treated as a study-level identifier for a conservative leakage check.
This script does not move or delete files.
"""

from __future__ import annotations

import argparse
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


def main() -> int:
    args = parse_args()
    result = audit(args.data_root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Data root: {result['data_root']}")
        print(f"Total images: {result['total_images']}")
        print(f"Unique study prefixes: {result['unique_study_prefixes']}")
        print("Class counts:")
        for key, count in result["class_counts"].items():
            print(f"- {key}: {count}")
        print(f"Cross-split duplicate prefixes: {result['cross_split_duplicate_prefix_count']}")
        print(f"Leakage risk: {result['leakage_risk']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
