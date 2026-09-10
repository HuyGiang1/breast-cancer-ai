#!/usr/bin/env python3
"""Build WDBC feature reference artifact using ONLY the 455 development samples.

Source of Truth:
- Dataset: sklearn.datasets.load_breast_cancer (WDBC 569 samples, 30 features)
- Split: experiments/final/ml_split_seed42.csv (seed 42 stratified outer split)
  * 455 development samples (reference scope: development_only)
  * 114 held-out test samples (strictly EXCLUDED)

Terminology Notice:
These are image-derived FNA nuclear morphology measurements.
They must NEVER be described as 'normal clinical ranges', 'healthy ranges',
or 'blood test values'.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
from sklearn.datasets import load_breast_cancer

ROOT = Path(__file__).resolve().parent.parent
SPLIT_CSV = ROOT / "experiments" / "final" / "ml_split_seed42.csv"
OUTPUT_EXP = ROOT / "experiments" / "final" / "wdbc_feature_reference.json"
OUTPUT_FE = ROOT / "frontend" / "content" / "wdbc_feature_reference.json"

FEATURE_DEFINITIONS: dict[str, dict[str, str]] = {
    "mean_radius": {
        "display_name": "Mean Radius",
        "group": "Mean",
        "description": "Mean distance from center to points on cell nucleus perimeter.",
    },
    "mean_texture": {
        "display_name": "Mean Texture",
        "group": "Mean",
        "description": "Standard deviation of gray-scale values across the cell nucleus.",
    },
    "mean_perimeter": {
        "display_name": "Mean Perimeter",
        "group": "Mean",
        "description": "Mean perimeter length of the cell nucleus contour.",
    },
    "mean_area": {
        "display_name": "Mean Area",
        "group": "Mean",
        "description": "Mean area enclosed within the nuclear boundary.",
    },
    "mean_smoothness": {
        "display_name": "Mean Smoothness",
        "group": "Mean",
        "description": "Mean of local variation in radius lengths.",
    },
    "mean_compactness": {
        "display_name": "Mean Compactness",
        "group": "Mean",
        "description": "Perimeter^2 / area - 1.0 (mean across sampled nuclei).",
    },
    "mean_concavity": {
        "display_name": "Mean Concavity",
        "group": "Mean",
        "description": "Mean severity of concave portions of the nucleus contour.",
    },
    "mean_concave_points": {
        "display_name": "Mean Concave Points",
        "group": "Mean",
        "description": "Mean number of concave portions of the nucleus contour.",
    },
    "mean_symmetry": {
        "display_name": "Mean Symmetry",
        "group": "Mean",
        "description": "Mean nuclear symmetry across sampled nuclei.",
    },
    "mean_fractal_dimension": {
        "display_name": "Mean Fractal Dimension",
        "group": "Mean",
        "description": "Coastline approximation - 1 (mean across sampled nuclei).",
    },
    "radius_error": {
        "display_name": "Radius SE",
        "group": "Standard Error",
        "description": "Standard error of distance from center to points on perimeter.",
    },
    "texture_error": {
        "display_name": "Texture SE",
        "group": "Standard Error",
        "description": "Standard error of gray-scale values across the nucleus.",
    },
    "perimeter_error": {
        "display_name": "Perimeter SE",
        "group": "Standard Error",
        "description": "Standard error of perimeter length for the nucleus.",
    },
    "area_error": {
        "display_name": "Area SE",
        "group": "Standard Error",
        "description": "Standard error of area enclosed within the nuclear boundary.",
    },
    "smoothness_error": {
        "display_name": "Smoothness SE",
        "group": "Standard Error",
        "description": "Standard error of local variation in radius lengths.",
    },
    "compactness_error": {
        "display_name": "Compactness SE",
        "group": "Standard Error",
        "description": "Standard error of perimeter^2 / area - 1.0.",
    },
    "concavity_error": {
        "display_name": "Concavity SE",
        "group": "Standard Error",
        "description": "Standard error of severity of contour concavities.",
    },
    "concave_points_error": {
        "display_name": "Concave Points SE",
        "group": "Standard Error",
        "description": "Standard error of number of contour concave portions.",
    },
    "symmetry_error": {
        "display_name": "Symmetry SE",
        "group": "Standard Error",
        "description": "Standard error of nuclear symmetry across sampled nuclei.",
    },
    "fractal_dimension_error": {
        "display_name": "Fractal Dimension SE",
        "group": "Standard Error",
        "description": "Standard error of coastline approximation - 1.",
    },
    "worst_radius": {
        "display_name": "Worst Radius",
        "group": "Worst",
        "description": "Mean of the three largest nuclear radius values.",
    },
    "worst_texture": {
        "display_name": "Worst Texture",
        "group": "Worst",
        "description": "Mean of the three largest nuclear texture values.",
    },
    "worst_perimeter": {
        "display_name": "Worst Perimeter",
        "group": "Worst",
        "description": "Mean of the three largest nuclear perimeter values.",
    },
    "worst_area": {
        "display_name": "Worst Area",
        "group": "Worst",
        "description": "Mean of the three largest nuclear area values.",
    },
    "worst_smoothness": {
        "display_name": "Worst Smoothness",
        "group": "Worst",
        "description": "Mean of the three largest nuclear smoothness values.",
    },
    "worst_compactness": {
        "display_name": "Worst Compactness",
        "group": "Worst",
        "description": "Mean of the three largest nuclear compactness values.",
    },
    "worst_concavity": {
        "display_name": "Worst Concavity",
        "group": "Worst",
        "description": "Mean of the three largest nuclear concavity values.",
    },
    "worst_concave_points": {
        "display_name": "Worst Concave Points",
        "group": "Worst",
        "description": "Mean of the three largest nuclear concave points values.",
    },
    "worst_symmetry": {
        "display_name": "Worst Symmetry",
        "group": "Worst",
        "description": "Mean of the three largest nuclear symmetry values.",
    },
    "worst_fractal_dimension": {
        "display_name": "Worst Fractal Dimension",
        "group": "Worst",
        "description": "Mean of the three largest nuclear fractal dimension values.",
    },
}

API_FEATURE_ORDER = list(FEATURE_DEFINITIONS.keys())


def load_development_indices() -> tuple[list[int], list[int]]:
    if not SPLIT_CSV.is_file():
        raise FileNotFoundError(f"Missing split CSV at {SPLIT_CSV}")

    dev_indices: list[int] = []
    test_indices: list[int] = []

    with open(SPLIT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row["sample_index"])
            split = row["split"].strip().lower()
            if split == "development":
                dev_indices.append(idx)
            elif split == "test":
                test_indices.append(idx)

    if len(dev_indices) != 455 or len(test_indices) != 114:
        raise ValueError(
            f"Expected 455 development and 114 test samples, got {len(dev_indices)} dev and {len(test_indices)} test"
        )
    return dev_indices, test_indices


def generate_reference_data() -> dict:
    dataset = load_breast_cancer()
    dev_idx, test_idx = load_development_indices()

    dev_set = set(dev_idx)
    test_set = set(test_idx)
    if dev_set.intersection(test_set):
        raise ValueError("Data leakage detected: development and test indices overlap!")

    x_dev = dataset.data[dev_idx]
    if x_dev.shape != (455, 30):
        raise ValueError(f"Unexpected development matrix shape: {x_dev.shape}")

    # Map dataset feature names (e.g. 'mean radius' -> 'mean_radius')
    sklearn_feature_map = {
        name.replace(" ", "_"): i for i, name in enumerate(dataset.feature_names)
    }

    features_dict: dict[str, dict] = {}
    for feat_name in API_FEATURE_ORDER:
        col_idx = sklearn_feature_map[feat_name]
        col_values = x_dev[:, col_idx]

        defn = FEATURE_DEFINITIONS[feat_name]

        min_val = float(np.min(col_values))
        p01_val = float(np.percentile(col_values, 1))
        p05_val = float(np.percentile(col_values, 5))
        median_val = float(np.median(col_values))
        p95_val = float(np.percentile(col_values, 95))
        p99_val = float(np.percentile(col_values, 99))
        max_val = float(np.max(col_values))
        mean_val = float(np.mean(col_values))
        std_val = float(np.std(col_values))

        features_dict[feat_name] = {
            "api_name": feat_name,
            "name": feat_name,
            "display_name": defn["display_name"],
            "group": defn["group"],
            "description": defn["description"],
            "definition": defn["description"],
            "min": round(min_val, 6) if abs(min_val) < 1 else round(min_val, 4),
            "p01": round(p01_val, 6) if abs(p01_val) < 1 else round(p01_val, 4),
            "p05": round(p05_val, 6) if abs(p05_val) < 1 else round(p05_val, 4),
            "median": round(median_val, 6) if abs(median_val) < 1 else round(median_val, 4),
            "p95": round(p95_val, 6) if abs(p95_val) < 1 else round(p95_val, 4),
            "p99": round(p99_val, 6) if abs(p99_val) < 1 else round(p99_val, 4),
            "max": round(max_val, 6) if abs(max_val) < 1 else round(max_val, 4),
            "mean": round(mean_val, 6),
            "std": round(std_val, 6),
            "n_development": 455,
        }

    artifact = {
        "metadata": {
            "dataset": "WDBC",
            "source": "sklearn.datasets.load_breast_cancer",
            "outer_split_seed": 42,
            "development_n": 455,
            "test_n": 114,
            "reference_scope": "development_only",
            "feature_count": 30,
            "outer_test_samples_excluded": 114,
            "total_dataset_samples": 569,
            "protocol": "seed42 stratified outer split (development partition)",
            "disclaimer": (
                "These empirical reference statistics reflect only the 455-sample WDBC development "
                "partition derived from digitized fine needle aspirate (FNA) cell nuclei images. "
                "They do NOT represent clinical laboratory normal ranges, healthy ranges, or blood test values."
            ),
        },
        "features": features_dict,
    }
    return artifact


def main() -> None:
    data = generate_reference_data()

    OUTPUT_EXP.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FE.parent.mkdir(parents=True, exist_ok=True)

    formatted = json.dumps(data, indent=2) + "\n"

    with open(OUTPUT_EXP, "w", encoding="utf-8") as f:
        f.write(formatted)
    print(f"Wrote {OUTPUT_EXP} ({len(data['features'])} features, {data['metadata']['development_n']} samples)")

    with open(OUTPUT_FE, "w", encoding="utf-8") as f:
        f.write(formatted)
    print(f"Wrote {OUTPUT_FE} ({len(data['features'])} features, {data['metadata']['development_n']} samples)")


if __name__ == "__main__":
    main()
