# Model artifact installation

Place the untracked binaries in `runtime_models/` before starting Compose:

- `logistic_regression_final_seed42.joblib` SHA-256 `15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755`
- `efficientnetb0_final_seed42.keras` SHA-256 `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b`

Set `FINAL_ML_MODEL_PATH=/app/runtime_models/logistic_regression_final_seed42.joblib` and `FINAL_DL_MODEL_PATH=/app/runtime_models/efficientnetb0_final_seed42.keras`. The service verifies both checksums at startup; confirm with `/api/v1/models/final/status/`.
