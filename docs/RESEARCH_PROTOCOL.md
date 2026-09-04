# Research Protocol

## Overview

This project should be framed as a reproducible comparative study and educational screening prototype for breast cancer AI. It must not be presented as a clinical diagnostic system.

## Primary Research Question

Can classical ML on structured WDBC features and DL on mammography-like image data provide reliable screening signals, and under what conditions does a multimodal fusion strategy improve over single-modality baselines?

## Secondary Questions

- Which ML model provides the best sensitivity/specificity tradeoff on WDBC?
- Does ROI preprocessing improve DL screening metrics compared with original images?
- Are predicted probabilities calibrated enough for risk communication?
- Which modality contributes more false negatives?
- Can SHAP and Grad-CAM provide interpretable support without being mistaken for medical proof?

## Hypotheses

- H1: Calibrated ML models on WDBC can achieve high ROC-AUC under a standard stratified split.
- H2: DL performance is only valid when train/validation/test are separated by patient or study, not by image.
- H3: Multimodal fusion should only be claimed as better if it improves validation-selected and final test metrics over ML-only and DL-only on paired samples.

## Dataset Protocol

### WDBC Clinical Dataset

- Use `sklearn.datasets.load_breast_cancer()` or documented local CSV equivalent.
- Preserve 30 numeric features.
- Use deterministic seed, stratified train/validation/test or nested CV.
- Fit scaler and calibration only on training folds.
- Keep final test split untouched until final evaluation.

### CBIS-DDSM Image Dataset

- Source and license/citation must be documented in `docs/DATA_CARD.md`.
- Build a manifest with columns:
  - `image_path`
  - `study_id`
  - `patient_id` if available
  - `label`
  - `split`
  - `source`
- Split by `patient_id` when available; otherwise by conservative `study_id`.
- Verify no patient/study appears in more than one split.
- Perform augmentation after split and only on training data.

## Required Leakage Checks

Run:

```bash
python scripts/audit_cbis_splits.py --json
```

A valid final experiment requires:

- `cross_split_duplicate_prefix_count = 0`
- split/class counts recorded
- random seed recorded
- preprocessing version recorded

## ML Experiment

Minimum models:

- Logistic Regression with scaling and class weighting.
- Random Forest with class weighting.
- XGBoost only if artifact and evaluation are healthy.

Required outputs:

- `experiments/results/ml_model_comparison.csv`
- `experiments/results/ml_calibration.csv`
- `experiments/results/ml_confusion_matrices.csv`
- trained model artifacts under `models/`, published outside Git if large.

## DL Experiment

Minimum baselines:

- Custom CNN currently deployed.
- One pretrained baseline only if it answers a research question, e.g. ResNet50 or EfficientNet-B0.

Required controls:

- fixed seed
- input size
- preprocessing description
- train-only augmentation
- class imbalance handling
- early stopping/checkpoint criteria
- validation-selected threshold
- final test report

Do not use test-set performance to choose architecture, threshold, or preprocessing.

## Multimodal Experiment

Current API fusion uses `0.4 ML + 0.6 DL`. This is a demo heuristic until validated.

Scientific multimodal evaluation requires paired samples. If paired samples do not exist, report multimodal as product integration only.

If paired data exists:

1. Train/tune ML and DL independently without test leakage.
2. Generate validation probabilities for both modalities.
3. Search fusion weights on validation set only:

```text
w_ml in [0.0, 0.1, ..., 1.0]
w_dl = 1.0 - w_ml
```

4. Select weight by predefined primary metric, preferably sensitivity-constrained balanced accuracy or ROC-AUC.
5. Evaluate selected weight once on test.
6. Compare:
   - ML only
   - DL only
   - fixed heuristic fusion
   - validation-tuned fusion

## Metrics

Minimum report:

- Accuracy
- Precision
- Sensitivity / Recall
- Specificity
- F1-score
- ROC-AUC
- PR-AUC
- Balanced Accuracy
- Confusion Matrix
- False Negative count

Recommended:

- 95% bootstrap CI for primary metrics
- Brier score
- calibration curve
- ECE if implementation is stable

## Explainability

Separate these concepts:

- Model explanation: SHAP, coefficients, feature importance, Grad-CAM.
- LLM advice: patient-facing educational text generated after model output.

LLM advice must not be used as scientific evidence for model correctness.

## Final Claim Rules

- Do not claim DL result validity until leakage-safe split passes.
- Do not claim multimodal improvement unless paired test evaluation shows improvement.
- If multimodal underperforms, report it honestly and frame as a negative/neutral result.
- Always include: Research/Educational prototype, not for clinical diagnosis.
