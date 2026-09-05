# Frontend Architecture V2 Plan

## Objective

Replace the single-page monolith with static HTML pages and vanilla ES modules while preserving all frozen research and backend contracts.

## Migration

1. Establish shared CSS, API/auth core, service modules, shell components, and static route validation.
2. Create public/auth entry pages and the reusable authenticated workspace shell.
3. Move dashboard, prediction, research, patient, history, report, advisor, model-status, and profile controllers into page modules.
4. Remove the giant `app.js` from active entry pages only after each workflow has an equivalent module path.

## Invariants

- ML raw classification threshold: `0.36`.
- DL raw classification threshold: `0.515`; Platt is display/reliability only.
- WDBC and CBIS-DDSM evidence stays separate.
- All model surfaces state research/educational use and `clinical_use=false`.
- Nginx continues serving only static frontend files and proxying `/api/` and `/results/`.

## Batch 2 Verification

Completed on 2026-09-05 for commit `116cde8`.

- Nginx served `200` for `/`, `/login.html`, `/register.html`, `/forgot-password.html`, `/reset-password.html`, and `/pages/dashboard.html`.
- Public CSS and V2 core/service/component/page modules resolved over Nginx with `200`; static `node --check` passed for every V2 module.
- Chrome headless rendered the landing successfully through `http://127.0.0.1/` at desktop viewport. The host Chrome emitted its known display/updater permission noise but produced a valid screenshot; no application asset failure was observed.
- Auth smoke was non-destructive: invalid login returned controlled `401 {"detail":"Invalid email or password"}`. Forgot-password with a non-existent email returned the intended generic `200` response with no reset token.
- Browser interaction checks at tablet/mobile remain a final full-browser QA gate for Batch 8. Batch 2's HTTP/module/auth gate is complete.
