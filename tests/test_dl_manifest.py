from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from dl_manifest import load_manifest_records, split_records


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "cbis_group_split_seed42.csv"


def test_final_manifest_is_group_safe_and_deterministic():
    records = load_manifest_records(MANIFEST, image_set="images")
    splits = split_records(records)

    assert len(records) == 2559
    assert {name: len(rows) for name, rows in splits.items()} == {
        "train": 1777,
        "val": 390,
        "test": 392,
    }
    group_splits = {}
    for record in records:
        assert group_splits.setdefault(record.group_id, record.split) == record.split


def test_roi_manifest_has_matching_sample_count():
    records = load_manifest_records(MANIFEST, image_set="images_roi")
    assert len(records) == 2559
