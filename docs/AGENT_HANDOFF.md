# Agent Handoff

## Last completed phase

Phase 2 manifest-driven DL pipeline is complete locally. The canonical repository is `https://github.com/HuyGiang1/breast-cancer-ai` on branch `main`.

## Current phase

Phase 3 final DL retraining is next, but blocked until the ignored CBIS-DDSM processed image files are restored/mounted at the paths recorded in the manifest.

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

## Evidence and decisions

- Latest baseline commit before this documentation work: `9270fa4 research: add CBIS-DDSM group split manifest`.
- `manifests/cbis_group_split_seed42.csv` has 5,118 rows across two representations (processed full image and ROI), and `manifests/cbis_group_split_seed42_summary.json` reports 2,354 study-like groups.
- Manifest overlaps are zero: train/validation, train/test, validation/test.
- Final machine-readable statistics confirm 2,559 full processed images, 2,559 ROI images and 2,354 inferred groups.
- `scripts/train_dl_finetune_calibrated.py` now reads `manifests/cbis_group_split_seed42.csv` directly and supports `--image-set images|images_roi`.
- Tests assert 2,559 full-image records, 2,559 ROI records, deterministic split counts, and one split per group.
- Standard final test evaluation no longer applies random TTA; model/threshold selection remains validation-based.
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

- The local workspace has the manifest but not the ignored processed CBIS images required to train.
- Public deployment requires future VPS/domain credentials.

## Exact next command

`PYTHONPATH=backend venv/bin/python scripts/train_dl_finetune_calibrated.py --architecture custom_cnn --image-set images --epochs 25 --batch-size 16 --image-size 224`

Run only after verifying that every manifest `relative_path` resolves to a local processed image.

## Latest commit and Git status

Latest pushed checkpoint: `9bcba28 research: make DL training manifest-driven`. Run `git status --short` before continuing; expected status after committing this handoff update is clean.

Run `git status --short` before continuing. Expected status after this handoff checkpoint is clean.
