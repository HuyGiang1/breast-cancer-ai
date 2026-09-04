# Final Runtime Model Contract

This contract is review evidence for a future research/demo runtime integration. It does not promote a clinical model or authorize a backend change. Both models remain research candidates.

## WDBC Logistic Regression

### Identity

- Study: WDBC structured ML.
- Model/version: `wdbc-logistic-regression-v1`, StandardScaler followed by Logistic Regression.
- Local artifact: `experiments/final/ml_runs/logistic_regression/logistic_regression_final_seed42.joblib`.
- SHA-256: `15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755`.
- Verified local framework: scikit-learn 1.8.0.

### Input

The artifact receives these 30 numeric measurements in exactly this order:

1. `mean radius`
2. `mean texture`
3. `mean perimeter`
4. `mean area`
5. `mean smoothness`
6. `mean compactness`
7. `mean concavity`
8. `mean concave points`
9. `mean symmetry`
10. `mean fractal dimension`
11. `radius error`
12. `texture error`
13. `perimeter error`
14. `area error`
15. `smoothness error`
16. `compactness error`
17. `concavity error`
18. `concave points error`
19. `symmetry error`
20. `fractal dimension error`
21. `worst radius`
22. `worst texture`
23. `worst perimeter`
24. `worst area`
25. `worst smoothness`
26. `worst compactness`
27. `worst concavity`
28. `worst concave points`
29. `worst symmetry`
30. `worst fractal dimension`

The saved pipeline owns StandardScaler preprocessing. A future service must pass raw values in this order exactly once and must not apply a separate global scaler.

### Output and calibration

`predict_proba(...)[1]` is the raw malignant probability: classes are `[0, 1]`, where class label 1 is malignant. Calibration is **none/raw**; empirical rank display transforms in the current runtime are not part of the final research contract.

### Decision

- Positive class: malignant (1).
- Probability space used by the threshold: raw malignant probability.
- Frozen balanced threshold: 0.36.
- Decision: `raw_malignant_probability >= 0.36`.

### Research evidence and limitations

Use `experiments/final/ml_metrics.csv`, `experiments/final/ml_model_selection.json`, and `docs/FINAL_ML_MODEL_SELECTION.md`. Logistic Regression was selected from development OOF evidence, not final-test rank. WDBC has no external validation and this artifact is not a clinical diagnostic model.

## CBIS-DDSM EfficientNet-B0 full image

### Identity

- Study: CBIS-DDSM imaging DL.
- Model/version: `cbis-efficientnetb0-full-v1`, EfficientNet-B0 full processed image.
- Local artifact: `models/deep_learning/efficientnetb0_final_seed42.keras`.
- SHA-256: `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b`.
- Architecture/output: `efficientnetb0_finetuned`, input `(224, 224, 3)`, sigmoid layer `malignant_probability`.

### Input

- Representation: full processed image (`images`), not ROI.
- Decode RGB, cast to float32, resize with `tf.image.resize(..., (224, 224))`.
- The frozen training model uses `tf.keras.applications.efficientnet.preprocess_input` as recorded in its final config. Future code must reproduce the saved-model/training pipeline exactly and must not add an additional incompatible image normalization step.

### Output and calibration

The sigmoid output is the raw malignant probability. Platt was selected by validation OOF reliability, but the frozen fitted Platt parameters were not saved as a standalone runtime-loadable artifact. `models/deep_learning/calibration_profile.json` is a legacy Custom CNN/Isotonic/empirical profile and is not an acceptable substitute.

### Decision

- Positive class: malignant.
- Probability space used by the frozen balanced threshold: **raw** sigmoid probability.
- Frozen balanced threshold: 0.515.
- Decision: `raw_malignant_probability >= 0.515`.
- The 0.48 sensitivity-oriented point is research-only and must never silently become a runtime default.

### Research evidence and limitations

Use `experiments/final/runs/efficientnet_b0_full/metrics.json`, `experiments/final/roi_ablation.csv`, `experiments/final/calibration_selection.json`, and `docs/FINAL_DL_RELIABILITY_AND_ERROR_ANALYSIS.md`. EfficientNet-B0 full image was retained validation-first; ROI is rejected (ROI-C). The manifest has inferred study-like, not verified patient-level, grouping and no external validation.

## Integration status

The ML artifact is technically eligible for a controlled research/demo integration because artifact, scaler, class ordering, raw probability, and threshold are all integrity-verifiable. DL integration is blocked until a versioned frozen Platt artifact/parameters and an explicit product probability-display contract are supplied; no calibrator may be refit or replaced with the current legacy profile.
