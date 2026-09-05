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
