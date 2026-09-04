"""Manifest parsing and integrity checks shared by final DL scripts."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


VALID_SPLITS = {"train", "val", "test"}
VALID_LABELS = {"benign": 0, "malignant": 1}
VALID_IMAGE_SETS = {"images", "images_roi"}


@dataclass(frozen=True)
class ManifestRecord:
    split: str
    label: int
    label_name: str
    group_id: str
    image_set: str
    relative_path: str


def load_manifest_records(manifest_path: Path, image_set: str = "images") -> list[ManifestRecord]:
    if image_set not in VALID_IMAGE_SETS:
        raise ValueError(f"Unsupported image set: {image_set}")
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"split", "label", "group_id", "image_set", "relative_path"}
    missing = required - set(rows[0] if rows else {})
    if missing:
        raise ValueError(f"Manifest missing columns: {sorted(missing)}")

    records: list[ManifestRecord] = []
    groups_to_split: dict[str, str] = {}
    groups_to_labels: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        split, label, group_id = row["split"], row["label"], row["group_id"]
        if split not in VALID_SPLITS or label not in VALID_LABELS or not group_id:
            raise ValueError(f"Invalid manifest row: {row}")
        previous_split = groups_to_split.setdefault(group_id, split)
        if previous_split != split:
            raise ValueError(f"Group {group_id} appears in both {previous_split} and {split}")
        groups_to_labels[group_id].add(label)
        if row["image_set"] == image_set:
            records.append(
                ManifestRecord(split, VALID_LABELS[label], label, group_id, image_set, row["relative_path"])
            )

    mixed_labels = [group_id for group_id, labels in groups_to_labels.items() if len(labels) != 1]
    if mixed_labels:
        raise ValueError(f"Manifest contains mixed-label groups: {mixed_labels[:5]}")
    counts = Counter(record.split for record in records)
    if not records or any(counts[split] == 0 for split in VALID_SPLITS):
        raise ValueError(f"Manifest has no usable records for every split in {image_set}: {dict(counts)}")
    return records


def split_records(records: list[ManifestRecord]) -> dict[str, list[ManifestRecord]]:
    result = {split: [] for split in sorted(VALID_SPLITS)}
    for record in records:
        result[record.split].append(record)
    return result
