"""Pure helpers for the frozen EfficientNet-B0 Platt display calibration."""

from __future__ import annotations

import math
from typing import Any, Mapping


def apply_platt_calibration(raw_probability: float, artifact: Mapping[str, Any]) -> float:
    """Apply the frozen identity-input Platt transform without sklearn runtime."""
    raw = float(raw_probability)
    if not math.isfinite(raw) or not 0.0 <= raw <= 1.0:
        raise ValueError("Raw malignant probability must be finite and within [0, 1].")
    coefficient = float(artifact["coefficient"])
    intercept = float(artifact["intercept"])
    if not math.isfinite(coefficient) or not math.isfinite(intercept):
        raise ValueError("Frozen Platt parameters must be finite.")
    z = coefficient * raw + intercept
    if z >= 0:
        calibrated = 1.0 / (1.0 + math.exp(-z))
    else:
        exp_z = math.exp(z)
        calibrated = exp_z / (1.0 + exp_z)
    if not math.isfinite(calibrated) or not 0.0 <= calibrated <= 1.0:
        raise ValueError("Frozen Platt transform returned an invalid probability.")
    return calibrated


def classify_final_dl_raw_probability(raw_probability: float) -> int:
    """The frozen classification rule remains in raw, not calibrated, space."""
    raw = float(raw_probability)
    if not math.isfinite(raw) or not 0.0 <= raw <= 1.0:
        raise ValueError("Raw malignant probability must be finite and within [0, 1].")
    return int(raw >= 0.515)
