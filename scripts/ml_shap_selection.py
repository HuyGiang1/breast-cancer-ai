"""Dependency-light deterministic selection for frozen ML SHAP case exports."""

from __future__ import annotations

from statistics import median


def select_cases(rows: list[dict]) -> list[dict]:
    """Select median-confidence TP/TN, the FP, and every FN deterministically."""
    selected = []
    for wanted in ("TP", "TN"):
        candidates = [row for row in rows if row["outcome"] == wanted]
        distances = [row["confidence_distance_from_threshold"] for row in candidates]
        middle = float(median(distances))
        selected.append(dict(min(candidates, key=lambda row: (abs(row["confidence_distance_from_threshold"] - middle), row["sample_index"])), selection_reason="median confidence: nearest median absolute distance from frozen threshold"))
    false_positives = [row for row in rows if row["outcome"] == "FP"]
    if len(false_positives) != 1:
        raise RuntimeError(f"Expected one frozen LR false positive, found {len(false_positives)}.")
    selected.append(dict(false_positives[0], selection_reason="all false positives: only frozen LR false positive"))
    for row in sorted((row for row in rows if row["outcome"] == "FN"), key=lambda row: row["sample_index"]):
        selected.append(dict(row, selection_reason="all false negatives: frozen LR final test has two false negatives"))
    return selected
