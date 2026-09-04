# Project Status

| Phase | Status | Evidence | Commit |
| --- | --- | --- | --- |
| 0. Re-audit baseline | DONE | `main` clean; API/tests/compile previously passed; CI present | `9270fa4` |
| 1. Dataset truth | DONE | Final JSON/CSV statistics and precise protocol generated from manifest seed 42 | `98b7724` |
| 2. Manifest-driven DL pipeline | DONE | Parser, tests and final trainer read `cbis_group_split_seed42.csv` directly | `9bcba28` |
| 3-4. Final DL retraining/evaluation | DONE | Three baselines and controlled EfficientNet ROI ablation complete; full image retained by validation-first ROI-C decision | `f27dd63` |
| DL calibration and error analysis | DONE | Platt selected by OOF validation reliability; threshold, errors and bootstrap CI generated; DL frozen | `ff6e53a` |
| DL XAI / Grad-CAM | DONE | Checksum-verified, deterministic TP/TN/FP/FN Grad-CAM analysis for frozen EfficientNet-B0 full-image candidate | - |
| 5. Final ML re-evaluation | DONE | Locked WDBC outer test, development OOF CV, calibration/threshold selection, bootstrap and error analysis complete; candidate not promoted | - |
| Final ML SHAP / XAI | NOT_STARTED | Evaluation is frozen; explanations are intentionally a separate next phase | - |
| 6-10. Analysis, paper artifacts, selection | NOT_STARTED | Development artifacts exist but are not final evidence | - |
| 11-18. Software and operations finalization | IN_PROGRESS | FastAPI, static web, Docker, Nginx, CI and artifact policy exist | `9270fa4` and earlier |
| 19. VPS/domain/HTTPS | BLOCKED | Requires VPS and domain access from project owner | - |
| 20-25. Production safety, CI, docs, release | IN_PROGRESS | Baseline safeguards and documentation exist; final release depends on research phases | - |

## Scientific status

- WDBC structured-data study can be reproduced independently.
- CBIS-DDSM final DL baselines, ROI ablation, calibration and uncertainty artifacts have been generated from the manifest-driven protocol.
- The manifest uses filename prefix before `__` as a conservative study-like group. It is not a verified patient-level split because the local processed snapshot lacks complete patient/case metadata.
- The current `0.4 * ML + 0.6 * DL` fusion is an experimental software heuristic, not a validated multimodal research finding.
- System framing: **Research / Educational Prototype - Not for clinical diagnosis.**
