# Final runtime model

The only final runtime candidate integrated by this phase is `wdbc-logistic-regression-v1`: a WDBC structured-data `StandardScaler -> LogisticRegression` scikit-learn pipeline. Its runtime status is `research_demo`; it is not for clinical diagnosis.

## Artifact verification

The versioned registry at `models/model_registry.example.json` supplies the relative artifact filename and SHA-256. The default local artifact is `experiments/final/ml_runs/logistic_regression/logistic_regression_final_seed42.joblib`; it remains ignored by Git. `FINAL_ML_MODEL_PATH` may override the local artifact location with either an absolute path or a repository-relative path. The expected checksum is never overridden by the environment.

Startup checks file presence, SHA-256, the exact `scaler`/`lr` pipeline step names and types, classes `[0, 1]`, and feature count 30. Any failure marks the final model `unavailable`; it never discovers legacy `.pkl` files, loads a different model, or trains a replacement.

## Input contract

`PredictionRequest` uses snake-case API names. `build_wdbc_feature_vector` explicitly maps them into the exact 30-feature WDBC/sklearn order recorded in `docs/FINAL_RUNTIME_MODEL_CONTRACT.md`, validates finite numeric values, and produces `(1, 30)`. The saved pipeline receives raw values and owns all scaling. No external `ml_scaler.pkl` participates in this path.

## Probability semantics

The malignant probability is raw `pipeline.predict_proba(X)[0, 1]`, where class label `1` is malignant. Calibration is `none_raw`; no empirical rank transform, probability clamp, or display calibration is applied. The API returns the same value in `probability` and `raw_probability`.

## Threshold

The frozen raw-probability decision threshold is `0.36`:

```text
malignant = raw_probability >= 0.36
```

`risk_band` is returned separately as `research_demo_display_only`. It is a display heuristic and never changes classification.

## API behavior

- `GET /api/v1/models/status/` exposes model identity, safe short checksum, artifact verification, feature count, raw probability space, calibration, threshold, research/demo status, and `clinical_use: false`.
- `GET /readyz` includes the final ML status.
- `POST /api/v1/predict/` accepts only the final Logistic Regression candidate and returns its raw probability, classification, threshold and probability-space metadata.
- Runtime explanation returns an explicit unavailable/not-finally-integrated message. The separate research SHAP artifacts remain unchanged and are not represented as live final SHAP.

## Failure behavior

If the artifact is absent, checksum-mismatched, or structurally incompatible, the status endpoint reports `unavailable` and ML prediction endpoints return HTTP `503` with an explicit final-model-unavailable error. The system does not fall back to Random Forest, XGBoost, historical Logistic Regression artifacts, a second scaler, or runtime training.

## Legacy isolation

Legacy ML discovery/training code remains in the historical service module for reference, but API traffic is bound to `FinalMLRuntimeService`. The final service only uses the registry-selected `.joblib` path. Legacy artifacts are neither default nor a substitute when the final artifact fails verification.

## Runtime parity verification

Run:

```bash
PYTHONPATH=backend venv/bin/python scripts/verify_final_ml_runtime_parity.py
```

The script loads frozen WDBC rows by `sample_index`, compares runtime raw probabilities with the saved final `test_predictions.csv`, and checks the frozen `0.36` class decision for deterministic TP, TN, and one available error case. It never trains or writes a model artifact.

## Known limitations

WDBC has no external validation. This is a research/educational prototype, not a clinical diagnostic model. The display risk band is not a clinical risk assessment.

## DL blocked status

The final CBIS-DDSM candidate remains `cbis-efficientnetb0-full-v1` with `promotion_status: BLOCKED`. Platt calibration was selected in research but no frozen runtime-loadable Platt artifact exists. This phase does not load that EfficientNet candidate, refit Platt, reuse `calibration_profile.json`, or promote raw-only DL output.
