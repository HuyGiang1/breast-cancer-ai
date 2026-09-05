# 1. Why artifact freeze was required

EfficientNet-B0 full-image Platt calibration had been selected by frozen validation reliability analysis, but the fitted transform was not persisted for runtime loading. This phase deterministically materializes that already-defined transform; it does not retrain, reselect a method, tune parameters, use test labels for fitting, or change an operating threshold.

# 2. Historical calibration implementation

The historical `platt_fit` implementation in `scripts/analyze_final_dl_reliability.py` is exactly `LogisticRegression(C=1e6, solver="lbfgs").fit(raw_probability.reshape(-1, 1), labels)`. It fits scalar raw malignant probabilities directly with the identity input transform, not logits.

# 3. Calibration selection

Five-fold stratified OOF validation selected Platt by minimum validation Brier followed by log loss. The selection remains frozen in `experiments/final/calibration_selection.json` and is not rerun or changed here.

# 4. Final transform fitting

The persisted transform is fit once on all 390 frozen validation rows only. The historical validation output is necessarily five-fold OOF, while the test output is produced by this all-validation fitted transform. This matches the original analysis procedure exactly.

# 5. Frozen parameters

- Coefficient: `13.098001802204282`
- Intercept: `-7.0899037369408395`
- Classes: `[0, 1]`; solver: `lbfgs`; `C`: `1000000.0`; scikit-learn: `1.8.0`

# 6. Artifact integrity

The versioned, weight-free artifact is [efficientnet_b0_platt_final_seed42.json](/Users/GiangNguyenHuy/Documents/breast-cancer-ai/models/calibration/efficientnet_b0_platt_final_seed42.json). Its SHA-256 is `7f9a06f54d6146b57952bcc38704022e27c9953a1a6a9e98af7eb3b457632c5d`, recorded in the model registry and runtime contract. It never references the legacy Custom CNN calibration profile.

# 7. Reproduction test

The freeze script reproduces all existing Platt metrics within `1e-12`; observed and historical values are identical (absolute delta `0.0`).

| Split | Brier | LogLoss | ECE 10-bin |
| --- | ---: | ---: | ---: |
| Validation OOF historical / reproduced | 0.21184852416480707 | 0.6085768529896337 | 0.022126176245054915 |
| Test full-validation transform historical / reproduced | 0.208762152150943 | 0.6024092740995982 | 0.046994767185167104 |

The derived prediction exports are `experiments/final/dl_calibration/efficientnet_b0_validation_calibrated_predictions.csv` (historical OOF validation) and `efficientnet_b0_test_calibrated_predictions.csv` (frozen all-validation transform).

# 8. Runtime semantics

`predicted_class = raw_probability >= 0.515`. The frozen Platt artifact separately converts raw probability to calibrated display/reliability probability and must never be used with the `0.515` threshold. The `0.48` raw sensitivity-oriented point remains research-only.

# 9. Scientific status

No retraining, split change, model-selection change, calibration-method selection, threshold change, or test fitting occurred. The freeze script reads test labels only after fitting to reproduce historical descriptive metrics.

# 10. Decision

**APPROVED_FOR_INTEGRATION:** the previously missing, historically defined Platt transform is now a versioned artifact and reproduces frozen reliability evidence exactly. DL runtime integration remains a separate future feature phase and remains research/demo only.
