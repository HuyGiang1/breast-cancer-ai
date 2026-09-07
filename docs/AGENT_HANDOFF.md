# Agent Handoff

## Current state

- Repository: `https://github.com/HuyGiang1/breast-cancer-ai`
- Current branch: `feat/frontend-architecture-v2`
- Base branch: `feat/frontend-premium-redesign`
- Latest completed scope: Batch 7 legacy retirement and canonical V2 cutover
- Next scope on the same branch: Batch 8 full route and cross-device QA
- Next stage after Batch 8: `docs/final-documentation`; do not create it automatically.
- Research is frozen. Do not retrain, recalibrate, change split/model/threshold, or promote clinical use.

## Batch 7 result

- The 21 canonical HTML routes map one-to-one to ES-module page controllers.
- Removed `frontend/app.js`, `frontend/styles.css`, `frontend/premium.css`, two unused JS shims, and unreferenced legacy demo/article images.
- Nginx uses explicit static `404` behavior; API, results, health, and readiness proxies are unchanged.
- Workspace/support CSS has semantic ownership. `scripts/verify_frontend_v2.py` validates the complete route and dependency graph.
- Authenticated desktop Chrome cutover QA passed all workspace routes without legacy requests, app errors, blank pages, active-navigation errors, or horizontal overflow.
- Full contracts and compatibility decisions are in `docs/FRONTEND_ARCHITECTURE_V2.md`.

## Verification passed

```bash
find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check
python3 scripts/verify_frontend_v2.py
git diff --check
PYTHONPATH=.:backend venv/bin/python -m pytest -q
python3 -m compileall backend/app scripts tests
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_application.py
PYTHONPATH=.:backend venv/bin/python scripts/verify_production_readiness.py
```

Nginx returned `200` for every canonical route, `404` for the three retired bundles and unknown routes, `403` for static directory requests, and JavaScript MIME for modules. Docker must be stopped with `docker compose down`, never `down -v`.

## Exact next work

Run Batch 8 only: full public/authenticated workflow and viewport matrix across desktop, tablet, and mobile; verify navigation drawer, auth redirects, forms, API errors, tables/charts, long content, overflow, console/network, and direct refresh. Fix only QA regressions, update the three trackers, push the same branch, and wait for CI. Do not begin final documentation automatically.

External VPS, domain, DNS, TLS, and production deployment remain blocked until credentials/infrastructure are provided.
