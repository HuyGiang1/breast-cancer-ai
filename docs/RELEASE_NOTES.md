# Release Notes

Proposed release: `v1.0.0-research-demo`

No GitHub release or tag has been created. Production deployment has not yet been executed.

## Highlights

- Frozen, reproducible WDBC ML and CBIS-DDSM DL evidence streams.
- Checksum-verified Logistic Regression and EfficientNet-B0 research/demo runtimes.
- Frontend Architecture V2 with 21 canonical routes and modular ES Modules.
- Final research report in source Markdown, DOCX, and PDF formats.
- Docker Compose, Nginx, CI, backup/restore, safety, and server deployment handoff.

## Research Studies

Study A compares Logistic Regression, Random Forest, and XGBoost on 569 WDBC samples with development OOF selection and a 114-sample held-out test. Logistic Regression is the frozen primary candidate and uses raw malignant probability threshold `0.36`.

Study B compares Custom CNN, ResNet50, and EfficientNet-B0 on a CBIS-DDSM processed snapshot. The 5,118 manifest rows represent 2,559 source images plus 2,559 ROI representations, not independent mammograms or patients. EfficientNet-B0 full processed images is retained from validation-first evidence and uses raw threshold `0.515`.

Study C records calibration, bootstrap uncertainty, error analysis, SHAP, and Grad-CAM. The frozen Platt output improves DL reliability and is used for display only.

## Final Runtime Models

- WDBC Logistic Regression: checksum-verified, fail-closed, raw threshold `0.36`.
- CBIS-DDSM EfficientNet-B0 full image: checksum-verified, fail-closed, raw threshold `0.515`.
- EfficientNet-B0 Platt artifact: checksum-verified display/reliability mapping.

Model binaries remain outside Git and are mounted read-only at runtime.

## Frontend Architecture V2

The final frontend is static HTML/CSS with vanilla JavaScript ES Modules organized into core, services, components, and page controllers. Legacy monolith assets were removed. Final browser QA covered 21 routes at four viewports for 84/84 passes.

## Research Transparency

- WDBC and CBIS-DDSM remain separate studies; there is no cross-dataset leaderboard.
- CBIS grouping is inferred study-like grouping, not verified patient-level grouping.
- ROI was rejected by its validation-first criterion.
- SHAP is non-causal and Grad-CAM is qualitative coarse attention.
- The 40/60 multimodal score is an unpaired software heuristic marked `experimental_only`.

## Testing / QA

Release gates cover JavaScript syntax, frontend dependency integrity, 24 backend tests, Python compileall, final application and production readiness validators, Docker health/readiness, model SHA checks, SQLite persistence, Nginx serving, and full frontend browser workflows.

## Deployment State

Local Docker and production-readiness verification are complete. The user has a server, but production deployment has not yet been executed. Server access/configuration, domain, DNS, HTTPS, and external production smoke remain pending for `deploy/server-production`.

## Safety

This release is a research and educational prototype with `clinical_use=false`. It is not for clinical diagnosis and does not replace pathology, radiology review, or clinician assessment.

## Known Limitations

- No external validation.
- CBIS-DDSM split is not verified patient-level.
- DL discrimination is moderate and uncertainty remains material.
- No paired-data multimodal validation.
- No formal regulatory, clinical workflow, physical-device, or WCAG certification.
- Static-client local-storage bearer auth and SQLite suit the current research demo, not a regulated clinical system.
