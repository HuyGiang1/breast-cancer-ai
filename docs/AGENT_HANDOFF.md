# Agent Handoff

## Last completed phase

Final DL reliability and error analysis is complete locally. The canonical repository is `https://github.com/HuyGiang1/breast-cancer-ai` on branch `main`.

## Current phase

DL architecture and weights are frozen. The next research phase is Grad-CAM/XAI for the retained EfficientNet-B0 full-image candidate.

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

`PYTHONPATH=backend venv/bin/python scripts/generate_final_dl_gradcam.py`

Run only after verifying that every manifest `relative_path` resolves to a local processed image.

## Latest commit and Git status

Latest pushed checkpoint: `f27dd63 research: evaluate EfficientNet-B0 ROI ablation`. Current reliability/error-analysis changes are pending a logical checkpoint commit.

Run `git status --short` before continuing. Expected status after this handoff checkpoint is clean.
