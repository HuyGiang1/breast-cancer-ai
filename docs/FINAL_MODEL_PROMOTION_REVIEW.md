# 1. Purpose

This review determines whether frozen research artifacts are technically ready for a future research/demo runtime integration. It performs no model promotion, retraining, threshold change, calibration change, or backend modification.

# 2. Frozen research state

The final ML candidate is WDBC Logistic Regression, selected from development OOF evidence with raw probability threshold 0.36. The final DL candidate is EfficientNet-B0 full processed image, retained validation-first with raw sigmoid threshold 0.515. ML and DL research are frozen and are separate studies.

# 3. ML candidate review

The final local Logistic Regression artifact exists and matches its recorded SHA-256. It is a scikit-learn 1.8.0 pipeline containing StandardScaler then Logistic Regression, accepts 30 features, has class order `[0, 1]`, and exposes malignant raw probability at `predict_proba(...)[1]`. The threshold artifact, test prediction export, metadata, and final snapshot consistently identify raw probability threshold 0.36.

# 4. DL candidate review

The final EfficientNet-B0 full artifact exists and matches its recorded SHA-256. Its input is 224 by 224 RGB and its final sigmoid output is named `malignant_probability`. Config, metadata, threshold, test prediction export, and snapshot consistently identify the full `images` representation and raw threshold 0.515. The ROI artifact is rejected by validation-first ROI-C and is not eligible for automatic runtime selection.

# 5. Calibration review

ML uses raw probability; no calibration transform is part of its final contract. DL Platt calibration was selected for validation reliability, but `calibration_selection.json` explicitly preserves raw-probability operating points. At the original review, the transform was not persisted; this was resolved later by deterministic artifact freezing from frozen validation predictions using the already-defined final calibration procedure. `models/calibration/efficientnet_b0_platt_final_seed42.json` now contains the identity-input scalar Platt parameters and is SHA-256 verified (`7f9a06f54d6146b57952bcc38704022e27c9953a1a6a9e98af7eb3b457632c5d`). The existing `calibration_profile.json` instead encodes a legacy Custom CNN empirical/Isotonic profile and must not be reused.

# 6. Probability-space and threshold consistency

| Model | Frozen probability for decision | Frozen threshold | Runtime current behavior | Review |
| --- | --- | ---: | --- | --- |
| WDBC Logistic Regression | Raw malignant `predict_proba` index 1 | 0.36 | Auto-discovers legacy `.pkl`, applies empirical display transform, decides at 0.50 | Runtime mismatch; candidate contract itself is consistent |
| EfficientNet-B0 full | Raw sigmoid malignant output | 0.515 | Auto-discovers/priority-selects legacy artifacts, applies profile-driven empirical/Isotonic postprocess, has legacy threshold/profile | Runtime mismatch; frozen Platt display artifact is now available but not yet integrated |

The DL balanced threshold was selected on raw probabilities, not Platt-calibrated probabilities. Applying Platt and then comparing to 0.515 would be a contract mismatch. The 0.48 sensitivity-oriented point remains research-only.

# 7. Artifact integrity

Both selected model files are present locally and match their recorded SHA-256. ML metadata/config/threshold agree. DL metadata/config/threshold agree on architecture, full representation, image size, preprocessing policy, raw output, and threshold. The Platt artifact is versioned, SHA-256 verified, and metric-equivalent to the frozen historical analysis.

# 8. Legacy runtime artifacts

The current ML service discovers historical root `.pkl` files and may train fallback models. The current DL service discovers many `.keras` files by path/mtime and consumes a legacy Custom CNN calibration profile. It defaults to exposing Custom CNN only and can apply empirical/Isotonic probability postprocessing. None of this discovery, fallback, or postprocessing is part of the final candidate contract.

# 9. Runtime implementation gaps

| Concern | Current runtime | Final research contract | Required change |
| --- | --- | --- | --- |
| ML artifact | Historical `.pkl` discovery | Explicit final `.joblib` | Registry-based explicit load with SHA check |
| ML feature order | API underscore names and optional global scaler | 30 fixed WDBC order; scaler inside pipeline | Canonical schema mapping; no duplicate scaling |
| ML probability/threshold | Empirical display transform; raw decision 0.50 | Raw malignant p; 0.36 | Remove transform from decision and use frozen threshold |
| DL artifact | Mtime/profile discovery; Custom CNN default | Explicit EfficientNet-B0 full `.keras` | Registry-based explicit load with SHA check |
| DL preprocessing | PIL/OpenCV resize and model-name branch | Frozen TensorFlow decode/cast/resize plus saved-model policy | Match final training path exactly |
| DL calibration | Legacy empirical/Isotonic profile; optional runtime fitting | Frozen scalar-input Platt artifact | Load only the versioned artifact in a future runtime phase; do not reuse/refit |
| DL decision | Legacy profile thresholds | Raw p; 0.515 | Enforce raw-space threshold and keep 0.48 research-only |
| Metadata/health | Paths and ad hoc health only | Version, SHA, probability space, status | Add registry-backed status endpoint |
| XAI/fallback | Runtime explanation may use fallback logic | Frozen research XAI is post-hoc | Label runtime explanations separately; do not claim equivalence |

# 10. Risks

- No verified patient-level CBIS grouping and no external validation.
- Runtime currently could silently use legacy artifacts or an incompatible probability transformation.
- DL runtime still needs explicit EfficientNet loading and separation of raw classification from frozen calibrated display output.
- Neither candidate is clinically approved; this is research/demo integration only.

# 11. Decision

- **ML: APPROVED_FOR_INTEGRATION.** The final artifact, preprocessing pipeline, positive-class index, raw probability space, and raw threshold are integrity-verifiable. Future integration must replace the legacy runtime path, not layer on top of it.
- **DL: APPROVED_FOR_INTEGRATION.** Previously blocked because the transform was not persisted; this is resolved by deterministic artifact freezing from frozen validation predictions using the already-defined final calibration procedure. The artifact reproduces all frozen Platt metrics exactly. Runtime still requires a separate controlled implementation that preserves raw threshold `0.515` and uses calibration only for display/reliability.
