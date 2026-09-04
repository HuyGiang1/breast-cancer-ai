# Project Status

| Phase | Status | Evidence | Commit |
| --- | --- | --- | --- |
| 0. Re-audit baseline | DONE | `main` clean; API/tests/compile previously passed; CI present | `9270fa4` |
| 1. Dataset truth | DONE | Final JSON/CSV statistics and precise protocol generated from manifest seed 42 | Pending checkpoint commit |
| 2. Manifest-driven DL pipeline | IN_PROGRESS | Existing DL trainer still discovers legacy folders; migration is next | - |
| 3-4. Final DL retraining/evaluation | BLOCKED | Must complete Phase 2; retraining intentionally not started | - |
| 5. Final ML re-evaluation | NOT_STARTED | Existing calibrated ML trainer is available | - |
| 6-10. Analysis, XAI, paper artifacts, selection | NOT_STARTED | Development artifacts exist but are not final evidence | - |
| 11-18. Software and operations finalization | IN_PROGRESS | FastAPI, static web, Docker, Nginx, CI and artifact policy exist | `9270fa4` and earlier |
| 19. VPS/domain/HTTPS | BLOCKED | Requires VPS and domain access from project owner | - |
| 20-25. Production safety, CI, docs, release | IN_PROGRESS | Baseline safeguards and documentation exist; final release depends on research phases | - |

## Scientific status

- WDBC structured-data study can be reproduced independently.
- CBIS-DDSM final DL results have **not** been generated from the new manifest.
- The manifest uses filename prefix before `__` as a conservative study-like group. It is not a verified patient-level split because the local processed snapshot lacks complete patient/case metadata.
- The current `0.4 * ML + 0.6 * DL` fusion is an experimental software heuristic, not a validated multimodal research finding.
- System framing: **Research / Educational Prototype - Not for clinical diagnosis.**
