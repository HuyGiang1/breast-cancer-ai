# Agent Handoff

## Last completed phase

System application finalization is complete on `feat/system-finalization`. The canonical repository is `https://github.com/HuyGiang1/breast-cancer-ai`.

## Current phase

ML and DL research are frozen and both final candidates are integrated for research/demo use only. The next phase is **Production Readiness**; it must not retrain, recalibrate, reselect thresholds, or make a clinical promotion.

## Git workflow

- Current branch: `feat/system-finalization`
- Base branch: `feat/final-dl-runtime-integration`
- Branch commits: application finalization commits pending.
- Verification passed: `python3 -m compileall backend/app scripts tests`; `pytest -q`; `scripts/validate_final_model_contract.py`; `scripts/validate_frozen_dl_calibration.py`; `scripts/freeze_final_dl_calibration.py` twice.

## Files changed in this handoff checkpoint

- `docs/PROJECT_STATUS.md`
- `docs/AGENT_HANDOFF.md`
- `docs/FINAL_PROJECT_OVERVIEW.md`
- `docs/FINAL_DATASET_PROTOCOL.md`
- `scripts/build_final_dataset_statistics.py`
- `experiments/final/dataset_statistics.json`
- `experiments/final/dataset_statistics.csv`
- `scripts/dl_manifest.py`
- `tests/test_dl_manifest.py`
- `scripts/train_dl_finetune_calibrated.py`
- `scripts/verify_final_dl_dataset.py`
- `docs/RESEARCH_RULES.md`
- `docs/LEGACY_RESEARCH_ARTIFACTS.md`
- `experiments/final/dataset_verification.json`
- `experiments/final/runs/custom_cnn_full/`
- `experiments/final/runs/resnet50_full/`
- `experiments/final/runs/efficientnet_b0_full/`
- `experiments/final/dl_metrics.csv`
- `experiments/final/figures/`
- `scripts/compare_final_dl_baselines.py`
- `docs/FINAL_DL_EXPERIMENT_LOG.md`
- `experiments/final/runs/efficientnet_b0_roi/`
- `experiments/final/roi_ablation.csv`
- `scripts/compare_efficientnet_roi_ablation.py`
- `docs/DL_BASELINE_AND_ROI_ANALYSIS.md`
- `scripts/analyze_final_dl_reliability.py`
- `experiments/final/calibration_metrics.csv`
- `experiments/final/threshold_analysis.csv`
- `experiments/final/dl_error_analysis.csv`
- `experiments/final/dl_bootstrap_ci.csv`
- `docs/FINAL_DL_RELIABILITY_AND_ERROR_ANALYSIS.md`
- `scripts/generate_final_dl_gradcam.py`
- `experiments/final/gradcam/`
- `experiments/final/gradcam_selection.json`
- `experiments/final/figures/efficientnet_gradcam_examples.png`
- `docs/FINAL_DL_XAI_ANALYSIS.md`
- `scripts/run_final_ml_study.py`
- `experiments/final/ml_dataset_statistics.json`
- `experiments/final/ml_split_seed42.csv`
- `experiments/final/ml_runs/`
- `experiments/final/ml_cv_metrics.csv`
- `experiments/final/ml_oof_predictions.csv`
- `experiments/final/ml_calibration_metrics.csv`
- `experiments/final/ml_threshold_analysis.csv`
- `experiments/final/ml_metrics.csv`
- `experiments/final/ml_bootstrap_ci.csv`
- `experiments/final/ml_error_analysis.csv`
- `docs/FINAL_ML_MODEL_SELECTION.md`
- `docs/FINAL_ML_ERROR_ANALYSIS.md`
- `scripts/generate_final_ml_shap.py`
- `experiments/final/ml_shap_global.csv`
- `experiments/final/ml_shap_selection.json`
- `experiments/final/ml_shap_cases/`
- `experiments/final/figures/ml_shap_summary.png`
- `experiments/final/figures/ml_shap_bar.png`
- `experiments/final/figures/ml_shap_examples.png`
- `docs/FINAL_ML_XAI_ANALYSIS.md`
- `scripts/generate_paper_artifacts.py`
- `scripts/validate_final_research_artifacts.py`
- `paper_artifacts/`
- `experiments/final/FINAL_RESULTS_SNAPSHOT.json`
- `docs/FINAL_RESEARCH_RESULTS.md`
- `docs/REPORT_UPDATE_NOTES.md`
- `models/model_registry.example.json`
- `docs/FINAL_RUNTIME_MODEL_CONTRACT.md`
- `docs/FINAL_MODEL_ARTIFACT_AUDIT.md`
- `docs/FINAL_MODEL_PROMOTION_REVIEW.md`
- `docs/FINAL_MODEL_RUNTIME_INTEGRATION_PLAN.md`
- `scripts/validate_final_model_contract.py`
- `backend/app/services/final_ml_runtime.py`
- `scripts/verify_final_ml_runtime_parity.py`
- `tests/test_final_ml_runtime.py`
- `docs/FINAL_ML_RUNTIME_INTEGRATION.md`
- `models/calibration/efficientnet_b0_platt_final_seed42.json`
- `experiments/final/dl_calibration/`
- `backend/app/services/final_dl_calibration.py`
- `scripts/freeze_final_dl_calibration.py`
- `scripts/validate_frozen_dl_calibration.py`
- `tests/test_frozen_dl_calibration.py`
- `docs/FINAL_DL_CALIBRATION_ARTIFACT.md`
- `backend/app/services/final_dl_runtime.py`
- `scripts/verify_final_dl_runtime_parity.py`
- `tests/test_final_dl_runtime.py`
- `docs/FINAL_DL_RUNTIME_INTEGRATION.md`

## Evidence and decisions

- Latest baseline commit before this documentation work: `9270fa4 research: add CBIS-DDSM group split manifest`.
- `manifests/cbis_group_split_seed42.csv` has 5,118 rows across two representations (processed full image and ROI), and `manifests/cbis_group_split_seed42_summary.json` reports 2,354 study-like groups.
- Manifest overlaps are zero: train/validation, train/test, validation/test.
- Final machine-readable statistics confirm 2,559 full processed images, 2,559 ROI images and 2,354 inferred groups.
- `scripts/train_dl_finetune_calibrated.py` now reads `manifests/cbis_group_split_seed42.csv` directly and supports `--image-set images|images_roi`.
- Tests assert 2,559 full-image records, 2,559 ROI records, deterministic split counts, and one split per group.
- Standard final test evaluation no longer applies random TTA; model/threshold selection remains validation-based.
- Gate A passed all 5,118 manifest records: zero missing paths, corrupt images, invalid rows, mixed-label groups and cross-split group overlaps.
- Gate B passes: manifest-only split source, group validation, no validation/test random augmentation, validation-based checkpoint/threshold selection, fixed seed and saved config.
- Custom CNN full-image candidate completed with final-run artifacts. It is not promoted; test ROC-AUC is 0.6153, sensitivity 0.4583 and FN 91, so it remains a comparison baseline rather than a selected production model.
- ResNet50 test ROC-AUC is 0.6278; sensitivity is 0.7202 and FN 47, but specificity is 0.4152.
- EfficientNet-B0 test ROC-AUC is 0.7229, PR-AUC 0.6564, sensitivity 0.6786, specificity 0.6250 and FN 54. It is the ROI-ablation candidate, not a runtime model.
- ROI ablation is CASE ROI-C by validation-first comparison: validation ROC-AUC falls from 0.7044 to 0.6789 and sensitivity from 0.6813 to 0.5125. Full image remains the candidate representation. No runtime model is promoted.
- Platt calibration is selected by 5-fold OOF validation Brier/log loss; final fitting used validation only. DL weights are frozen. The next action is XAI, not further training.
- Grad-CAM is complete for the checksum-verified EfficientNet-B0 full-image `.keras` artifact. The script dynamically selected `top_conv`, reproduced frozen probabilities with the trainer's TensorFlow preprocessing, and deterministically selected two examples each from TP, TN, FP, and FN.
- Grad-CAM is qualitative attention evidence only: no lesion localization, pathology, clinical causality, or tuning conclusion is claimed from it.
- Final WDBC ML evaluation uses a fixed 20% stratified outer holdout (seed 42) and 5-fold stratified development OOF CV. All scaling is fold-safe inside the Logistic Regression pipeline; no resampling is used.
- XGBoost 3.2.0 was healthy and included as a new reproducible comparison model; no legacy XGBoost artifact was reused.
- Logistic Regression is the development-selected ML candidate: OOF ROC-AUC 0.9950, PR-AUC 0.9941, balanced accuracy 0.9724, and raw-probability Brier 0.0200. It is not promoted to runtime.
- ML final test results are frozen. Subsequent SHAP/XAI is explanatory only and cannot change the selected model, calibrator, or threshold.
- Final ML SHAP/XAI used `shap.LinearExplainer` on the frozen Logistic Regression classifier after its saved StandardScaler, with all 455 development samples as the background and all 114 frozen test samples as the explanation set. SHAP values are malignant-class log-odds contributions.
- The deterministic local selection includes one median-confidence TP, one TN, the only FP, and both FNs. Logistic Regression remains frozen and is not promoted to runtime.
- Final paper artifacts read frozen `experiments/final` CSV/JSON only. They include 11 tables, 12 provenance-tracked figures, `paper_artifacts/MANIFEST.json`, and `experiments/final/FINAL_RESULTS_SNAPSHOT.json`.
- The synthesis explicitly treats WDBC ML and CBIS-DDSM DL as distinct studies. There is no cross-dataset model ranking and no validated multimodal conclusion.
- Promotion review verifies the final Logistic Regression pipeline, feature count/class ordering, raw probability, threshold 0.36, and artifact SHA-256. It is approved only for a future controlled research/demo integration.
- Promotion review verifies EfficientNet-B0 full-image SHA-256, input, preprocessing policy, raw output, and raw threshold 0.515. The prior missing Platt artifact is now resolved by a deterministic full-validation freeze: coefficient `13.098001802204282`, intercept `-7.0899037369408395`, artifact SHA `7f9a06f54d6146b57952bcc38704022e27c9953a1a6a9e98af7eb3b457632c5d`, and exact historical metric reproduction.
- Final ML runtime uses only the registry-selected final `.joblib`, verifies SHA-256 and pipeline structure at startup, maps the 30 API fields explicitly, sends raw values to the embedded scaler/pipeline, uses raw `predict_proba(...)[1]`, and classifies at the frozen threshold 0.36. There is no auto-discovery, double scaling, rank transform, 0.50 threshold, or fallback training in the final path.
- Runtime parity passed for frozen test TP sample 250, TN sample 120, and FN sample 73; maximum raw-probability delta was `2.776e-17`. API smoke checks passed for health, readiness, ML/DL status and the representative benign/malignant ML predictions.
- DL runtime remains unmodified and unintegrated. Existing Custom CNN handling is legacy/development and is not a final substitute. A future DL runtime must use raw `0.515` for classification and the frozen Platt artifact only for display/reliability.
- Existing DL metrics and figures under `experiments/results/` are development/preliminary only, because legacy folders had 90 cross-split study-like prefixes.
- Keep multimodal fusion as `Experimental Multimodal Integration` unless valid paired clinical-image data is found.
- Do not commit raw CBIS-DDSM, runtime database, `.env`, or model weight artifacts.

## Commands executed

- `git status --short`
- `git branch --show-current`
- `git remote -v`
- `git log --oneline -10`
- Read the split summary, FastAPI app/routes/security, Docker/Nginx, CI, frontend flows, and ML/DL training scripts.

## Current blockers

- Public deployment requires future VPS/domain credentials.

## Exact next command

Create `feat/final-dl-runtime-integration` from `research/freeze-dl-calibration-artifact` and implement only the frozen EfficientNet-B0 full-image runtime contract. Do not retrain, refit Platt, re-evaluate, or promote clinical use.

## Latest commit and Git status

Latest branch documentation commit is `7f6d274`; final DL runtime implementation is `b761cdf`. After this branch is pushed, the next action is `feat/system-finalization` from this branch. No DL training, ML re-evaluation change, or clinical/runtime promotion is authorized automatically.

Run `git status --short` before continuing. Expected status after this handoff checkpoint is clean.
