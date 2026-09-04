# NEXT_STEPS

This file tracks the follow-up work from the source audit. Keep each change small,
verify it, then update the status here.

## Current Change

- Status: implemented
- Scope: add research evidence dashboard powered by saved experiment artifacts.
- Files: `backend/app/api/endpoints.py`, `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
- Verification:
  - Python source parse passes.
  - Existing API smoke test passes.
  - `/api/v1/research/evidence/` returns compact evidence from experiment/model JSON files.
  - Stats page renders research highlights, ML retrain evidence, DL screening evidence, and clinical interpretation.

## Completed Changes

1. Replaced wildcard CORS with environment-configured allowed origins.
2. Added downloadable HTML reports for saved AI prediction records.
3. Added reliability labels and uncertainty warnings for ML, DL, and multimodal results.
4. Added a research evidence dashboard powered by saved experiment artifacts.

## Recommended Next Small Tasks

1. Hide password reset tokens from production responses.
2. Add upload size validation for image prediction endpoints.
3. Add clinical feature value ranges in backend schemas and frontend form validation.
4. Update `README.md` so it matches the current static frontend and FastAPI setup.
5. Add a richer API smoke test covering auth, prediction, history, and report export.
