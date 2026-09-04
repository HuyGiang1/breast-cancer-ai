#!/usr/bin/env python3
"""Create final dataset statistics from the committed CBIS split manifest.

This script deliberately reads the manifest, not legacy image folders. It can
run without the large CBIS-DDSM files being present, which keeps the dataset
contract reviewable in CI and on fresh research checkouts.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from sklearn.datasets import load_breast_cancer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = PROJECT_ROOT / "manifests" / "cbis_group_split_seed42.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "manifests" / "cbis_group_split_seed42_summary.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "final"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final WDBC and CBIS dataset statistics.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_manifest(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"split", "label", "group_id", "image_set", "relative_path"}
    missing = required - set(rows[0] if rows else {})
    if missing:
        raise ValueError(f"Manifest is missing columns: {sorted(missing)}")
    return rows


def build_statistics(rows: list[dict[str, str]], summary: dict) -> dict:
    split_order = ("train", "val", "test")
    label_order = ("benign", "malignant")
    image_set_order = ("images", "images_roi")
    image_counts = Counter((row["split"], row["label"], row["image_set"]) for row in rows)
    groups_by_split = {split: set() for split in split_order}
    groups_by_label = {label: set() for label in label_order}
    for row in rows:
        groups_by_split[row["split"]].add(row["group_id"])
        groups_by_label[row["label"]].add(row["group_id"])

    x, y = load_breast_cancer(return_X_y=True)
    # sklearn uses 0=malignant and 1=benign; project convention is inverse.
    wdbc = {
        "total_samples": int(len(y)),
        "benign": int((y == 1).sum()),
        "malignant": int((y == 0).sum()),
        "features": int(x.shape[1]),
        "split_strategy": "stratified_train_test_split; seed 42; final evaluation protocol to lock validation threshold before test",
        "seed": 42,
    }

    return {
        "schema_version": 1,
        "wdbc": wdbc,
        "cbis_ddsm": {
            "manifest": str(DEFAULT_MANIFEST.relative_to(PROJECT_ROOT)),
            "manifest_rows": len(rows),
            "original_processed_images": sum(image_counts[(s, l, "images")] for s in split_order for l in label_order),
            "roi_images": sum(image_counts[(s, l, "images_roi")] for s in split_order for l in label_order),
            "unique_source_image_identities": len({row["relative_path"].replace("images_roi", "images") for row in rows if row["image_set"] == "images"}),
            "group_count": len({row["group_id"] for row in rows}),
            "class_group_counts": {label: len(groups_by_label[label]) for label in label_order},
            "split_group_counts": {split: len(groups_by_split[split]) for split in split_order},
            "image_counts": {
                split: {
                    label: {image_set: image_counts[(split, label, image_set)] for image_set in image_set_order}
                    for label in label_order
                }
                for split in split_order
            },
            "overlap_counts": summary["overlap_counts"],
            "group_strategy": summary["independent_unit"],
            "limitation": summary["independent_unit_limitation"],
            "seed": summary["seed"],
        },
    }


def flatten_for_csv(statistics: dict) -> list[dict[str, object]]:
    rows = []
    for key, value in statistics["wdbc"].items():
        rows.append({"dataset": "WDBC", "scope": "overall", "metric": key, "value": value})
    cbis = statistics["cbis_ddsm"]
    for key in ("manifest_rows", "original_processed_images", "roi_images", "unique_source_image_identities", "group_count", "group_strategy", "limitation", "seed"):
        rows.append({"dataset": "CBIS-DDSM", "scope": "overall", "metric": key, "value": cbis[key]})
    for label, value in cbis["class_group_counts"].items():
        rows.append({"dataset": "CBIS-DDSM", "scope": label, "metric": "group_count", "value": value})
    for split, value in cbis["split_group_counts"].items():
        rows.append({"dataset": "CBIS-DDSM", "scope": split, "metric": "group_count", "value": value})
    for split, labels in cbis["image_counts"].items():
        for label, image_sets in labels.items():
            for image_set, value in image_sets.items():
                rows.append({"dataset": "CBIS-DDSM", "scope": f"{split}/{label}/{image_set}", "metric": "image_count", "value": value})
    for pair, value in cbis["overlap_counts"].items():
        rows.append({"dataset": "CBIS-DDSM", "scope": pair, "metric": "group_overlap_count", "value": value})
    return rows


def main() -> int:
    args = parse_args()
    rows = read_manifest(args.manifest)
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    statistics = build_statistics(rows, summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dataset_statistics.json").write_text(
        json.dumps(statistics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "dataset_statistics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "scope", "metric", "value"])
        writer.writeheader()
        writer.writerows(flatten_for_csv(statistics))
    print(json.dumps(statistics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
