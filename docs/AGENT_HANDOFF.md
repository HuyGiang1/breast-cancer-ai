# Agent Handoff

## Current state

- Repository: `https://github.com/HuyGiang1/breast-cancer-ai`
- Current branch: `feat/frontend-architecture-v2`
- Base branch: `feat/frontend-premium-redesign`
- Frontend Premium Redesign: COMPLETE
- Frontend Architecture V2: COMPLETE
- Legacy Frontend Retirement: COMPLETE
- Cross-device Final QA: COMPLETE
- Frontend status: **FROZEN FOR RELEASE**
- Next stage: `docs/final-documentation`; do not create it automatically.
- Research is frozen. Do not retrain, recalibrate, change split/model/threshold, or promote clinical use.

## Final frontend evidence

- 21 canonical routes and controllers; no runtime legacy frontend dependency.
- Browser matrix: 21 routes at 1440x900, 1280x800, 768x1024, and 390x844, 84/84 PASS.
- Full disposable workflow matrix passed auth/recovery/roles, final ML/DL and experimental multimodal, patient association/history/report, advisor, status, profile/password, and controlled 400/401/403/404/422 states.
- ML uses raw threshold `0.36`. DL uses raw threshold `0.515`; Platt remains display/reliability only. Multimodal remains unpaired and experimental.
- Mobile navigation, keyboard focus, network failure UX, static transfer/security, research values, and Nginx serving were verified.
- Detailed evidence: `docs/FRONTEND_FINAL_QA.md` and `docs/FRONTEND_ARCHITECTURE_V2.md`.

## Required verification

```bash
find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check
python3 scripts/verify_frontend_v2.py
git diff --check
PYTHONPATH=.:backend venv/bin/python -m pytest -q
python3 -m compileall backend/app scripts tests
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_application.py
PYTHONPATH=.:backend venv/bin/python scripts/verify_production_readiness.py
```

The existing Pydantic V2 class-config warning is pre-existing. External advisor provider failures remain controlled. Docker must be stopped with `docker compose down`, never `down -v`.

## Next session

After the current branch is pushed, CI is green, and the user explicitly starts the next phase, create `docs/final-documentation` from this branch. Finalize the Word/PDF report, README, release notes, and release documentation without redesigning the frozen frontend or changing research/model contracts.

VPS, domain, DNS, TLS, and external deployment remain blocked until infrastructure and credentials are provided.
