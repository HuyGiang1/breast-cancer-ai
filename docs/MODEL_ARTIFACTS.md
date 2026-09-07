# Final Runtime Model Artifacts

Status: frozen for the research demo. Model weights and serialized estimators are distributed outside normal Git history and mounted read-only in production.

## Required artifacts

| Model | Runtime path | Role | SHA-256 |
| --- | --- | --- | --- |
| WDBC Logistic Regression | `runtime_models/logistic_regression_final_seed42.joblib` | Final ML research/demo runtime; raw threshold `0.36` | `15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755` |
| CBIS-DDSM EfficientNet-B0 | `runtime_models/efficientnetb0_final_seed42.keras` | Final DL research/demo runtime; full processed image; raw threshold `0.515` | `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b` |
| EfficientNet-B0 Platt metadata | `models/calibration/efficientnet_b0_platt_final_seed42.json` | Frozen calibrated display/reliability probability only | Verified by final runtime contract |

The DL class is always determined from raw probability `>= 0.515`; the Platt probability is not compared with that threshold.

## Installation

Obtain the two binary files from the approved private artifact/release channel, place them under `runtime_models/`, and verify:

```bash
sha256sum runtime_models/logistic_regression_final_seed42.joblib
sha256sum runtime_models/efficientnetb0_final_seed42.keras
git ls-files runtime_models
```

The final command must return no tracked files. Do not commit `.keras`, `.joblib`, `.pkl`, `.h5`, `.pt`, `.pth`, `.onnx`, patient data, or credentials.

## Runtime behavior

The final services verify checksum before serving inference and fail closed on missing or mismatched files. They do not fall back to historical models. `/api/v1/models/final/status/` exposes safe identity/status metadata and always reports `clinical_use: false`.

Docker Compose mounts `./runtime_models:/app/runtime_models:ro`.

## Provenance

- `experiments/final/FINAL_RESULTS_SNAPSHOT.json`
- `experiments/final/runs/efficientnet_b0_full/model_metadata.json`
- `experiments/final/ml_runs/logistic_regression/model_metadata.json`
- `docs/FINAL_RUNTIME_MODEL_CONTRACT.md`
- `docs/FINAL_MODEL_PROMOTION_REVIEW.md`

Historical/local experiment files are not deployment candidates and must not replace the two checksummed artifacts above.
