#!/usr/bin/env python3
"""Reproduce selected frozen EfficientNet test predictions through final runtime."""

from __future__ import annotations

import csv
from pathlib import Path

from app.services.final_dl_runtime import FinalDLRuntimeService
from dl_manifest import load_manifest_records, split_records

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "experiments" / "final" / "runs" / "efficientnet_b0_full"
CALIBRATED = ROOT / "experiments" / "final" / "dl_calibration" / "efficientnet_b0_test_calibrated_predictions.csv"
MANIFEST = ROOT / "manifests" / "cbis_group_split_seed42.csv"
RAW_TOLERANCE = 1e-6
CALIBRATED_TOLERANCE = 1e-6


def main() -> int:
    service = FinalDLRuntimeService()
    if service.model is None:
        print(f"FAIL: final DL runtime unavailable: {service.error}")
        return 1
    with (RUN / "test_predictions.csv").open(newline="", encoding="utf-8") as handle:
        predictions = list(csv.DictReader(handle))
    with CALIBRATED.open(newline="", encoding="utf-8") as handle:
        calibrated = {int(row["sample_index"]): row for row in csv.DictReader(handle)}
    records = split_records(load_manifest_records(MANIFEST, image_set="images"))["test"]
    if len(records) != len(predictions):
        raise RuntimeError("Frozen test manifest order does not match prediction export length.")
    selected = {}
    for row in predictions:
        label, prediction = int(row["label"]), int(row["prediction"])
        kind = "TP" if (label, prediction) == (1, 1) else "TN" if (label, prediction) == (0, 0) else "FP" if prediction else "FN"
        selected.setdefault(kind, int(row["index"]))
    required = ("TP", "TN", "FP", "FN")
    if any(kind not in selected for kind in required):
        raise RuntimeError(f"Missing required deterministic test cases: {selected}")
    max_raw = max_calibrated = 0.0
    for kind in required:
        index = selected[kind]
        result = service.predict((ROOT / records[index].relative_path).read_bytes())
        expected = predictions[index]
        expected_calibrated = calibrated[index]
        raw_delta = abs(result["raw_probability"] - float(expected["malignant_probability"]))
        calibrated_delta = abs(result["calibrated_probability"] - float(expected_calibrated["calibrated_probability"]))
        max_raw, max_calibrated = max(max_raw, raw_delta), max(max_calibrated, calibrated_delta)
        if raw_delta > RAW_TOLERANCE or calibrated_delta > CALIBRATED_TOLERANCE or result["prediction"] != int(expected["prediction"]):
            print(f"FAIL: {kind} index={index} raw_delta={raw_delta:.3e} calibrated_delta={calibrated_delta:.3e}")
            return 1
    print(f"PASS: {len(required)} samples ({', '.join(f'{kind}:{selected[kind]}' for kind in required)}); max_raw_delta={max_raw:.3e}; max_calibrated_delta={max_calibrated:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
