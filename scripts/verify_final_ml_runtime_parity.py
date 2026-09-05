"""Verify frozen test predictions can be reproduced by the runtime contract."""

from __future__ import annotations

import csv
from pathlib import Path

from sklearn.datasets import load_breast_cancer

from app.services.final_ml_runtime import API_TO_WDBC_FEATURE, FinalMLRuntimeService


ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "experiments" / "final" / "ml_runs" / "logistic_regression" / "test_predictions.csv"
TOLERANCE = 1e-10


class RequestPayload:
    def __init__(self, values: dict[str, float]):
        self._values = values

    def model_dump(self) -> dict[str, float]:
        return self._values


def _select_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_outcome: dict[str, dict[str, str]] = {}
    for row in rows:
        actual = int(row["true_label"])
        predicted = int(row["prediction"])
        by_outcome.setdefault({(1, 1): "TP", (0, 0): "TN", (1, 0): "FN", (0, 1): "FP"}[actual, predicted], row)
    required = ["TP", "TN"]
    selected = [by_outcome[name] for name in required]
    for optional in ("FN", "FP"):
        if optional in by_outcome:
            selected.append(by_outcome[optional])
            break
    return selected


def main() -> int:
    service = FinalMLRuntimeService()
    if service.model is None:
        print(f"FAIL: final ML runtime is unavailable: {service.health_error}")
        return 1

    with PREDICTIONS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    data = load_breast_cancer().data
    api_fields = tuple(API_TO_WDBC_FEATURE)
    max_delta = 0.0
    selected = _select_rows(rows)
    for row in selected:
        sample_index = int(row["sample_index"])
        payload = {name: float(data[sample_index, idx]) for idx, name in enumerate(api_fields)}
        result = service.predict(RequestPayload(payload))
        expected_probability = float(row["raw_probability"])
        delta = abs(result["raw_probability"] - expected_probability)
        max_delta = max(max_delta, delta)
        if delta > TOLERANCE or result["prediction"] != int(row["prediction"]):
            print(
                "FAIL: sample_index="
                f"{sample_index} delta={delta:.3e} expected_prediction={row['prediction']} "
                f"runtime_prediction={result['prediction']}"
            )
            return 1

    kinds = ", ".join(
        f"{int(row['sample_index'])}:{'TP' if row['true_label'] == '1' and row['prediction'] == '1' else 'TN' if row['true_label'] == '0' and row['prediction'] == '0' else 'FN' if row['true_label'] == '1' else 'FP'}"
        for row in selected
    )
    print(f"PASS: {len(selected)} samples checked ({kinds}); max probability delta={max_delta:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
