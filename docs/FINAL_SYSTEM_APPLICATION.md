# Final system application

## Architecture

The application remains a vanilla HTML/CSS/JavaScript frontend with FastAPI APIs. Frozen WDBC ML and CBIS-DDSM DL studies remain separate research/demo workflows.

## Final runtimes and status

The final ML Logistic Regression and final DL EfficientNet-B0 full-image runtime are checksum-verified and exposed through `/api/v1/models/final/status/`. It reports only safe status metadata; `clinical_use` is always false. Legacy model services are development/reference-only.

## Prediction, history, and reports

ML uses raw probability threshold `0.36`. DL uses raw probability threshold `0.515`; its frozen Platt output is display/reliability-only. Prediction history preserves model metadata and raw/display values. Reports include an explicit research/screening limitation.

## Research dashboard

`/api/v1/research/evidence/` reads the frozen `experiments/final/FINAL_RESULTS_SNAPSHOT.json`. The frontend displays WDBC ML and CBIS-DDSM DL evidence separately and does not imply a cross-modality model ranking. See `docs/FINAL_RESEARCH_RESULTS.md` for the full synthesis.

## Safety and failures

Result UI states that outputs are model predictions, not diagnoses. Final ML/DL unavailable states return controlled `503`; invalid ML input returns validation errors and corrupt image uploads return controlled `400`. The frontend uses API error messages rather than raw stack traces.

## Multimodal status

The existing 0.4 ML + 0.6 DL endpoint remains an experimental demo heuristic. It has no paired-data validation and is not a final scientific conclusion.

## Validation evidence

`scripts/verify_final_application.py` exercises health, readiness, unified status, final ML prediction, invalid ML request, final DL prediction, and corrupt-image handling offline. Contract and runtime parity scripts remain required checks.

## Remaining production tasks

End-to-end benchmark, Docker verification, CI release validation, safety review, VPS deployment, HTTPS, final README/release notes, and Word/PDF report updates remain separate phases.
