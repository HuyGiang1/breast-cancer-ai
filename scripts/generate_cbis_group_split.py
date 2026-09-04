#!/usr/bin/env python3
"""Generate a deterministic group-level CBIS-DDSM split manifest.

The processed filenames in this repository use a stable prefix before "__".
Because no patient/case metadata is available locally, this prefix is used as
the strongest available study-like group identifier. The script writes a CSV
manifest and JSON summary; it does not move, copy, or delete image files.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


VALID_SPLITS = ("train", "val", "test")
VALID_LABELS = ("benign", "malignant")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CBIS-DDSM group split manifest")
    parser.add_argument(
        "--image-root",
        type=Path,
        default=Path("data/cbis_ddsm/processed/images"),
        help="Processed full-image root with train/val/test label folders.",
    )
    parser.add_argument(
        "--roi-root",
        type=Path,
        default=Path("data/cbis_ddsm/processed/images_roi"),
        help="Processed ROI-image root with train/val/test label folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cbis_ddsm/processed/splits/cbis_group_split_seed42.csv"),
        help="Output CSV manifest path.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/cbis_ddsm/processed/splits/cbis_group_split_seed42_summary.json"),
        help="Output JSON summary path.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Deterministic shuffle seed.")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Validation group ratio per class.")
    parser.add_argument("--test-ratio", type=float, default=0.15, help="Test group ratio per class.")
    return parser.parse_args()


def iter_images(root: Path, image_set: str) -> Iterable[dict[str, str]]:
    for suffix in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for path in sorted(root.glob(f"*/*/{suffix}")):
            original_split = path.parts[-3]
            label = path.parts[-2]
            if original_split not in VALID_SPLITS or label not in VALID_LABELS:
                continue
            yield {
                "image_set": image_set,
                "original_split": original_split,
                "label": label,
                "group_id": path.name.split("__", 1)[0],
                "relative_path": path.as_posix(),
            }


def allocate_groups(groups_by_label: dict[str, list[str]], seed: int, val_ratio: float, test_ratio: float) -> dict[str, str]:
    if val_ratio < 0 or test_ratio < 0 or val_ratio + test_ratio >= 1:
        raise ValueError("val-ratio and test-ratio must be non-negative and sum to less than 1.")

    assignments: dict[str, str] = {}
    rng = random.Random(seed)

    for label, groups in sorted(groups_by_label.items()):
        shuffled = sorted(groups)
        rng.shuffle(shuffled)

        n_total = len(shuffled)
        n_test = round(n_total * test_ratio)
        n_val = round(n_total * val_ratio)

        test_groups = set(shuffled[:n_test])
        val_groups = set(shuffled[n_test : n_test + n_val])

        for group_id in shuffled:
            if group_id in test_groups:
                assignments[group_id] = "test"
            elif group_id in val_groups:
                assignments[group_id] = "val"
            else:
                assignments[group_id] = "train"

    return assignments


def overlap_counts(assignments: dict[str, str]) -> dict[str, int]:
    split_to_groups: dict[str, set[str]] = defaultdict(set)
    for group_id, split in assignments.items():
        split_to_groups[split].add(group_id)

    return {
        "train_val": len(split_to_groups["train"] & split_to_groups["val"]),
        "train_test": len(split_to_groups["train"] & split_to_groups["test"]),
        "val_test": len(split_to_groups["val"] & split_to_groups["test"]),
    }


def main() -> int:
    args = parse_args()
    rows = list(iter_images(args.image_root, "images"))
    if args.roi_root.exists():
        rows.extend(iter_images(args.roi_root, "images_roi"))

    if not rows:
        raise SystemExit(f"No processed images found under {args.image_root} or {args.roi_root}")

    labels_by_group: dict[str, set[str]] = defaultdict(set)
    original_splits_by_group: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        labels_by_group[row["group_id"]].add(row["label"])
        original_splits_by_group[row["group_id"]].add(row["original_split"])

    mixed_label_groups = {group_id: sorted(labels) for group_id, labels in labels_by_group.items() if len(labels) > 1}
    if mixed_label_groups:
        preview = dict(list(sorted(mixed_label_groups.items()))[:10])
        raise SystemExit(f"Found groups with multiple labels; cannot split safely: {preview}")

    groups_by_label: dict[str, list[str]] = defaultdict(list)
    for group_id, labels in labels_by_group.items():
        groups_by_label[next(iter(labels))].append(group_id)

    assignments = allocate_groups(groups_by_label, args.seed, args.val_ratio, args.test_ratio)
    overlaps = overlap_counts(assignments)
    if any(overlaps.values()):
        raise SystemExit(f"Generated split has group overlap: {overlaps}")

    manifest_rows = []
    for row in sorted(rows, key=lambda item: (assignments[item["group_id"]], item["label"], item["group_id"], item["relative_path"])):
        manifest_rows.append(
            {
                "split": assignments[row["group_id"]],
                "label": row["label"],
                "group_id": row["group_id"],
                "image_set": row["image_set"],
                "original_split": row["original_split"],
                "relative_path": row["relative_path"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "label", "group_id", "image_set", "original_split", "relative_path"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    group_counts = Counter()
    for group_id, split in assignments.items():
        label = next(iter(labels_by_group[group_id]))
        group_counts[f"{split}/{label}"] += 1

    image_counts = Counter(f"{row['split']}/{row['label']}/{row['image_set']}" for row in manifest_rows)
    original_cross_split_groups = {
        group_id: sorted(splits)
        for group_id, splits in original_splits_by_group.items()
        if len(splits) > 1
    }

    summary = {
        "image_root": args.image_root.as_posix(),
        "roi_root": args.roi_root.as_posix(),
        "output": args.output.as_posix(),
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "test_ratio": args.test_ratio,
        "independent_unit": "filename_prefix_before_double_underscore",
        "independent_unit_limitation": "No patient/case metadata was available in the local processed dataset.",
        "total_rows": len(manifest_rows),
        "total_groups": len(assignments),
        "group_counts": dict(sorted(group_counts.items())),
        "image_counts": dict(sorted(image_counts.items())),
        "overlap_counts": overlaps,
        "original_cross_split_group_count": len(original_cross_split_groups),
        "original_cross_split_examples": dict(list(sorted(original_cross_split_groups.items()))[:25]),
    }

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
