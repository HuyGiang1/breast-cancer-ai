# Model Card

## Intended Use

Breast Cancer AI is a research and educational prototype for comparing classical machine learning, deep learning, and demo multimodal prediction workflows for breast cancer screening signals.

It is not a medical device and must not be used for clinical diagnosis, treatment selection, or replacing physician review.

## Current Models

### Structured Clinical ML

- Runtime service: `backend/app/services/prediction.py`
- Training script: `scripts/train_ml_calibrated.py`
- Current runtime models observed during smoke test:
  - Logistic Regression
  - Random Forest
- XGBoost artifact exists in older paths but was disabled at runtime because the service detected unhealthy probability behavior.

### Image DL

- Runtime service: `backend/app/services/prediction_dl.py`
- Training script: `scripts/train_dl_finetune_calibrated.py`
- Current runtime model observed during smoke test:
  - Custom CNN
- Historical artifacts include ResNet50 and EfficientNet-B0, but they should not be treated as final research winners without leakage-safe reevaluation.

### Multimodal Demo

- Runtime endpoint: `POST /api/v1/predict/multimodal/`
- Current fusion: weighted average, `0.4 * ML probability + 0.6 * DL probability`.
- Status: heuristic demo only. Not validated as a scientific fusion strategy.

## Dataset Summary

- WDBC: 569 samples, 30 numeric features.
- CBIS-DDSM processed local images: 2559 images in train/validation/test folders.
- Current CBIS split has CRITICAL leakage risk because 90 study-prefixes appear across multiple splits.

## Metrics

Existing artifacts report:

- ML retrain ROC-AUC values in `models/ml_retrain_report_20260404.json`.
- DL sensitivity/specificity/ROC-AUC in `experiments/results/phase2_summary.json` and `phase3_statistical_analysis.json`.

These are development artifacts, not final publishable claims, until data split methodology is fixed and reproduced.

## Thresholds

- ML decision threshold in runtime service: 0.5.
- DL threshold may be loaded from `models/deep_learning/calibration_profile.json`.
- UI risk bands:
  - Low: malignant probability < 0.35
  - Medium: 0.35 to < 0.65
  - High: >= 0.65

Risk bands are communication heuristics unless explicitly validated in a research experiment.

## Explainability

- ML: SHAP/top-feature style explanations are supported by service code.
- DL: Grad-CAM-style result images are generated for image predictions when requested.
- LLM advice is separate from model explanation and must not be cited as evidence of model correctness.

## Limitations

- DL split leakage risk invalidates final DL claims until corrected.
- Multimodal fusion requires paired clinical-image samples. Current WDBC and CBIS workflows are not naturally paired.
- No external validation dataset is documented.
- Demo user records should be synthetic; do not upload real patient data to a public demo.
- Probability calibration needs final Brier/ECE/calibration analysis after leakage-safe splits.

## Ethical and Medical Warning

This project is for research and education only. It cannot diagnose cancer. Any suspicious symptom or imaging result requires evaluation by qualified medical professionals and appropriate clinical tests.
