# Agent Handoff

## Last completed phase

Safe research reset gates are complete and the Custom CNN final candidate run is complete locally. The canonical repository is `https://github.com/HuyGiang1/breast-cancer-ai` on branch `main`.

## Current phase

Phase 3 continues with ResNet50 and EfficientNet-B0 baseline runs using the same manifest and full-image representation.

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

`MPLCONFIGDIR=/private/tmp/breast-cancer-ai-mpl PYTHONPATH=backend venv/bin/python scripts/train_dl_finetune_calibrated.py --architecture resnet50 --image-set images --epochs 25 --batch-size 16 --image-size 224 --learning-rate 0.0001 --output-stem resnet50_final_seed42 --run-dir experiments/final/runs/resnet50_full`

Run only after verifying that every manifest `relative_path` resolves to a local processed image.

## Latest commit and Git status

Latest pushed checkpoint: `9d9cb1b docs: update phase handoff status`. Current safe-reset and Custom CNN changes are pending a logical checkpoint commit.

Run `git status --short` before continuing. Expected status after this handoff checkpoint is clean.
