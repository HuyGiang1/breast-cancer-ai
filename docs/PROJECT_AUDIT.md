# Project Audit

Audit date: 2026-09-04

Repository: `/Users/GiangNguyenHuy/Documents/breast-cancer-ai`

Remote configured locally: `origin` -> `giangnguyenhuy87/breast-cancer-ai`

Fetch status: `git fetch origin` could not be completed in this environment because writing `.git/FETCH_HEAD` was blocked. Comparison below uses the existing local `origin/main` ref.

## Git State

- Local branch: `main` at `78cff81`
- Local `origin/main` ref: `4399f6b`
- Divergence by local refs: local has 4 unique commits; `origin/main` has 5 unique commits.
- Working tree has uncommitted source changes in backend/frontend plus tracked `.pyc` changes.
- No GitHub Actions workflow was present before this audit.
- No `tests/` directory was present before this audit.

## Tracked Artifact Findings

- Tracked `.pyc` files: 5
- Tracked `.keras` model files: 6
- Tracked `.pkl`/model/data artifacts covered by cleanup rules: present
- Tracked CBIS-DDSM processed image files: 5118
- Largest tracked files include duplicate `resnet50_best.keras` copies under `backend/` and `src/models/deep_learning/`, each about 97 MB.
- `.env` is ignored and not tracked in the local index, but real API keys are present in local runtime configuration. Treat any exposed key as sensitive and rotate if it was ever pushed or shared.

## Research Data Snapshot

Wisconsin/WDBC clinical data:

- Source used by code: `sklearn.datasets.load_breast_cancer()` and local CSV copies.
- Sample count: 569.
- Feature count: 30 numeric clinical/cytology features.
- Current ML retrain script: `scripts/train_ml_calibrated.py`.

CBIS-DDSM processed image data:

- Path: `data/cbis_ddsm/processed/images`
- Total images found: 2559.
- Split/class counts:
  - `train/benign`: 1040
  - `train/malignant`: 750
  - `val/benign`: 223
  - `val/malignant`: 160
  - `test/benign`: 224
  - `test/malignant`: 162
- Unique filename prefixes before `__`: 2354.
- Cross-split duplicate study-prefix count: 90.
- Leakage risk: CRITICAL until a patient/study-level split manifest proves independence.

## Area Review

| Area | Current state | Grade | Problem | Required action | Priority |
| ---- | ------------- | ----- | ------- | --------------- | -------- |
| Research question | README states ML vs DL and deployment goals | PARTIAL | Questions are broad and not tied to measurable hypotheses | Define primary/secondary research questions and acceptance metrics | P1 REQUIRED |
| Novelty | Combines ML, DL, XAI, web demo | PARTIAL | Scientific novelty is product integration, not a new method | Frame as reproducible comparative study and clinical screening demo | P1 REQUIRED |
| Dataset quality | WDBC present; CBIS-DDSM processed images present locally | PARTIAL | CBIS provenance/license/split manifest not documented | Add data card, source instructions, counts, and split manifest | P0 CRITICAL |
| Data leakage control | Prefix audit found cross-split duplicates | CRITICAL | DL test metrics may be optimistic or invalid | Rebuild patient/study-level split before final DL/multimodal claims | P0 CRITICAL |
| ML methodology | Calibrated LR/RF training exists | PARTIAL | Single train/test split; limited metric report; XGBoost disabled at runtime | Add reproducible CV/evaluation report and model version metadata | P1 REQUIRED |
| DL methodology | Custom CNN, ResNet50, EfficientNet scripts/artifacts exist | PARTIAL | Split validity unresolved; model selection criteria mixed | Re-evaluate on leakage-safe split; keep baselines only if tied to questions | P0 CRITICAL |
| Multimodal methodology | API uses weighted average `0.4 ML + 0.6 DL` | CRITICAL | Weight is heuristic; no paired validation tuning or final paired test | Build paired validation/test manifest and fusion ablation | P0 CRITICAL |
| Evaluation metrics | Accuracy, sensitivity, specificity, ROC-AUC, bootstrap files exist | PARTIAL | Results cannot be final while split leakage risk remains | Regenerate final metrics after leakage-safe split | P0 CRITICAL |
| Statistical evidence | Bootstrap CI and McNemar-style outputs exist | PARTIAL | Tests apply to current experimental setup only | Re-run after corrected splits and document test assumptions | P1 REQUIRED |
| Calibration | ML calibrated models and DL calibration profile exist | PARTIAL | Threshold/risk bands partly heuristic; Brier/ECE not consistently reported | Add calibration table and separate UI heuristics from research thresholds | P1 REQUIRED |
| Explainability | SHAP/top features and Grad-CAM paths exist | PARTIAL | Need separate model explanation from LLM advice | Document XAI pipeline and expose clearly in UI/docs | P1 REQUIRED |
| Bias/generalization | No external validation dataset documented | MISSING | Cannot claim clinical generalization | Add limitation; optional external dataset only if time allows | P2 IMPORTANT |
| Backend API | FastAPI app with auth, patients, predictions, reports | PARTIAL | Large `endpoints.py`; limited validation; internal errors exposed before hardening | Add validation, health endpoints, tests, then consider router split | P1 REQUIRED |
| Frontend demo | Static app with home/learn/care/chat/predict/stats/history/patients | DONE | Needs stronger research-only disclaimers and asset tracking cleanup | Keep static frontend; improve copy and states after research blockers | P2 IMPORTANT |
| Docker | Dockerfile, compose, nginx present | PARTIAL | Model artifact strategy unclear; healthchecks missing | Document volume/release artifact flow; add compose healthchecks later | P2 IMPORTANT |
| Deployment | Nginx config exists | PARTIAL | No domain/HTTPS/backup/runbook docs before this audit | Use `docs/DEPLOYMENT.md` and production `.env` | P2 IMPORTANT |
| GitHub readiness | Remote exists; repo diverged | CRITICAL | Heavy tracked files and branch divergence block clean push | Untrack cache/data/model safely; merge/rebase remote; secret scan | P0 CRITICAL |
| CI/CD | None before audit | MISSING | No automated validation | Add minimal GitHub Actions without large dataset/model downloads | P1 REQUIRED |
| Documentation | README outdated; several docs ignored locally | PARTIAL | README says React/NextJS and has TBD metrics | Replace README and add docs set | P1 REQUIRED |

## Immediate Blockers

1. DL data leakage risk must be resolved before defending DL or multimodal conclusions.
2. Multimodal fusion has no scientific evidence; current `0.4/0.6` weight is a demo heuristic.
3. Git history/index contains tracked dataset/model/cache files that should not be part of a clean public repository.
4. Local branch and `origin/main` have diverged; do not push until reconciled.
5. Any real API key visible in local environment or previous logs should be rotated before publication.

## Remediation Started In This Pass

- Added safe ignore rules for caches, local environment files, generated outputs, large datasets, and model artifacts.
- Removed tracked cache/data/model artifacts from the Git index without deleting local files.
- Added a minimal CI workflow, smoke-test-friendly validation dependencies, and schema tests.
- Added health/readiness endpoints for deployment checks.
- Hardened prediction endpoints with non-negative clinical feature validation, image content-type checks, upload size limits, and generic internal error responses.
- Added `scripts/audit_cbis_splits.py`; current local CBIS-DDSM split still reports CRITICAL leakage risk and must be rebuilt before final research claims.
- Current tracked heavy-artifact check now returns zero for `.pyc`, `.keras`, `.pkl`, `.h5`, `.onnx`, `backend/data/*`, `data/cbis_ddsm/*`, and generated experiment result paths.
- Current tracked-source secret scan found no active secret-like API keys, but history scan flagged old notebook diffs for review. Rotate any real key that was ever committed, shared, or printed in logs.
