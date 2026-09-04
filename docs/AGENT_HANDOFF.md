# Agent Handoff

## Last completed phase

Phase 1 Dataset Truth is complete. The canonical repository is `https://github.com/HuyGiang1/breast-cancer-ai` on branch `main`.

## Current phase

Phase 2, manifest-driven DL pipeline. Do not start Deep Learning retraining until this training input contract is complete and tested.

## Files changed in this handoff checkpoint

- `docs/PROJECT_STATUS.md`
- `docs/AGENT_HANDOFF.md`
- `docs/FINAL_PROJECT_OVERVIEW.md`
- `docs/FINAL_DATASET_PROTOCOL.md`
- `scripts/build_final_dataset_statistics.py`
- `experiments/final/dataset_statistics.json`
- `experiments/final/dataset_statistics.csv`

## Evidence and decisions

- Latest baseline commit before this documentation work: `9270fa4 research: add CBIS-DDSM group split manifest`.
- `manifests/cbis_group_split_seed42.csv` has 5,118 rows across two representations (processed full image and ROI), and `manifests/cbis_group_split_seed42_summary.json` reports 2,354 study-like groups.
- Manifest overlaps are zero: train/validation, train/test, validation/test.
- Final machine-readable statistics confirm 2,559 full processed images, 2,559 ROI images and 2,354 inferred groups.
- Existing `scripts/train_dl_finetune_calibrated.py` still reads `data/cbis_ddsm/processed/images/{train,val,test}` via directory discovery. It must be converted to read the manifest directly.
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

- No scientific blocker for Phase 1/2.
- Phase 3 is intentionally deferred until the new training input contract is implemented.
- Public deployment requires future VPS/domain credentials.

## Exact next command

`PYTHONPATH=backend venv/bin/python -m pytest -q`

After the Phase 1 checkpoint, implement tests and a manifest parser for `scripts/train_dl_finetune_calibrated.py` before retraining.

## Latest commit and Git status

Latest pre-checkpoint commit: `9270fa4`.

Run `git status --short` before continuing; this checkpoint deliberately creates uncommitted documentation files until they are reviewed and validated together.
