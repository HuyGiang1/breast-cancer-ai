# Production Roadmap

Priority order follows scientific correctness first, then reproducibility, Git hygiene, backend safety, web flow, deployment, and CI.

## P0 Critical

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P0-01 | `data/cbis_ddsm/processed/images` | Cross-split study-prefix duplicates detected | Rebuild split manifest by patient/study | `python scripts/audit_cbis_splits.py --json` | `cross_split_duplicate_prefix_count` is 0 |
| P0-02 | `scripts/train_dl_finetune_calibrated.py` | DL metrics depend on current split | Re-run DL on leakage-safe split | Compare regenerated JSON/CSV | Final DL report cites leakage-safe split |
| P0-03 | `backend/app/api/endpoints.py` | Multimodal uses fixed `0.4/0.6` heuristic | Keep UI heuristic label; build validation tuning experiment only with paired data | Fusion ablation table | Scientific claims do not rely on heuristic fusion |
| P0-04 | Git index | `.pyc`, CBIS images, model weights tracked | `git rm --cached` only; do not delete local files | `git ls-files` checks | No cache/raw images/large weights tracked |
| P0-05 | Git security | Local `.env` has real secrets | Secret scan and rotate exposed keys if ever shared/pushed | Scan output has no secrets | No secret is committed or documented |
| P0-06 | Branch state | Local `main` and `origin/main` diverged | Fetch in normal shell, inspect, merge/rebase safely | `git rev-list --left-right --count main...origin/main` | Local branch reconciled before push |

## P1 Required Research

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P1-01 | `docs/DATA_CARD.md` | Dataset provenance incomplete | Document WDBC/CBIS sources, counts, split policy | Review doc | Data card explains limitations and privacy |
| P1-02 | `scripts/train_ml_calibrated.py` | ML report too narrow | Add CV metrics, confusion matrix, PR-AUC, Brier | Regenerated CSV/JSON | ML report reproducible from one command |
| P1-03 | `scripts/evaluate_prediction_spread.py` or new script | Calibration not summarized uniformly | Generate Brier/calibration/ECE table | CSV/PNG artifacts | Probability reliability documented |
| P1-04 | New multimodal eval script | No paired fusion experiment | Build only after paired manifest exists | Ablation output | ML/DL/fusion compared on same samples |
| P1-05 | `docs/MODEL_CARD.md` | Model risks not formally documented | Add intended use, limits, metrics, thresholds | Review doc | Reader cannot confuse demo with diagnosis |
| P1-06 | README | Old README inaccurate | Replace with current architecture and commands | Manual review | Clone user can understand project |

## P2 Backend Hardening

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P2-01 | `backend/app/api/schemas.py` | Clinical inputs allowed negative values | Add non-negative validation | `pytest -q` | Negative feature rejected |
| P2-02 | `backend/app/api/endpoints.py` | Image uploads lacked strict size/type validation | Validate JPEG/PNG/WebP and max MB | Manual/API test | Bad/oversize image returns 400/413 |
| P2-03 | `backend/app/main.py` | No health/readiness endpoints | Add `/healthz` and `/readyz` | curl or import test | VPS can monitor app |
| P2-04 | `backend/app/api/endpoints.py` | Router file is large | Split routers after tests exist | API smoke test | Behavior unchanged after split |
| P2-05 | Auth/reset | File-mode reset token useful locally but unsafe if misconfigured | Ensure production uses SMTP and no token response | Integration test | Production reset flow sends email only |

## P3 Frontend Demo

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P3-01 | `frontend/index.html` | Medical disclaimer must be impossible to miss | Add clear research-only language in result/home flows | Browser check | Users see not-for-diagnosis warning |
| P3-02 | `frontend/app.js` | Multimodal result could look scientific | Label fixed fusion as demo heuristic unless validated | Browser check | UI avoids overstating fusion |
| P3-03 | `frontend/assets` | Assets previously ignored | Track necessary demo/web assets | `git status --ignored` | Public clone renders web correctly |
| P3-04 | Responsive | Need final visual QA | Check mobile/desktop prediction/history/patients | Screenshots/manual | No broken layout in main flows |

## P4 Deployment

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P4-01 | `docker-compose.yml` | No healthchecks | Add healthchecks after `/healthz` is stable | `docker compose ps` | Containers report healthy |
| P4-02 | Model artifacts | Heavy weights not in Git | Use server volume or GitHub Release artifact | Backend `/models/dl/status/` | Server can find selected model |
| P4-03 | VPS | No runbook | Follow `docs/DEPLOYMENT.md` | Domain loads app | App available over HTTPS |
| P4-04 | SQLite | Needs backup if public demo | Add backup command/runbook | Restore rehearsal | DB backup and restore documented |

## P5 GitHub/CI/Docs

| ID | File/Area | Problem | Action | Verify | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| P5-01 | `.github/workflows/ci.yml` | No CI | Run compile, pytest, app import, optional data audit | GitHub Actions green | PRs get baseline validation |
| P5-02 | `.dockerignore` | Docker context too large | Exclude data/model/cache/secrets | `docker compose build` | Build context stays small |
| P5-03 | Releases | Model strategy missing | Publish weights outside Git or document manual placement | Fresh clone checklist | Reproducible model setup |
| P5-04 | Commit workflow | Mixed changes | Commit logical groups | `git log --oneline` | History is understandable |

## Suggested Commit Order

1. `chore: clean repository ignore rules`
2. `docs: add research audit and protocol`
3. `fix: harden prediction validation and health checks`
4. `ci: add backend validation workflow`
5. `docs: add deployment and model data cards`
6. `chore: untrack generated and large artifacts`
