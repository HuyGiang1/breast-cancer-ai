# Frontend Premium Redesign

Date: 2026-09-05

## Scope and contract

This redesign modernizes the static HTML/CSS/vanilla JavaScript workspace. It does not change FastAPI routes, authentication/doctor authorization, API payloads, frozen ML/DL artifacts, raw decision thresholds, calibration, or research metrics.

- ML classification remains based on raw probability `>= 0.36`.
- DL classification remains based on raw probability `>= 0.515`.
- DL Platt calibration remains a display/reliability value only.
- WDBC ML and CBIS-DDSM DL stay as separate studies; the interface does not create a shared leaderboard or clinical multimodal claim.

## Delivered interface

- A responsive research workspace shell with desktop sidebar, compact tablet state, mobile drawer, visible page context, and keyboard-accessible brand navigation.
- An evidence-first landing page that presents Logistic Regression/WDBC and EfficientNet-B0/CBIS-DDSM separately, alongside permanent research-only framing.
- Dense dashboard KPI cards and a research page that renders the packaged evidence snapshot instead of legacy DL benchmark constants.
- A 30-feature ML form organized into mean, error, and worst-measurement groups with completion feedback.
- DL image upload with click, drag/drop, selected-file metadata, preview, removal, demo images, and existing invalid-input handling.
- Result probability bars; DL results retain a distinct raw classification threshold marker and separately list calibrated display probability.
- Consistent surface, spacing, type, focus, reduced-motion, status, upload, patient/history, chat, result, and responsive styling in `frontend/premium.css`.

## Verification

- `node --check frontend/app.js`
- `git diff --check`
- Chrome headless visual review at 1440px desktop and 390px narrow viewport using the static frontend server.

The static review has no backend running, so final model status cards remain in their loading state. Backend-integrated regression is recorded in the phase verification commands before release.

## Known operational boundary

The UI is a research/educational prototype. It does not provide clinical diagnosis, medical normal-range guidance, or production deployment credentials. VPS/domain/HTTPS provisioning remains an external deployment task.
