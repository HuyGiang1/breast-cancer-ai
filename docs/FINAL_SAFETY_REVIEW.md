# Final Operational Safety Review

Review date: 2026-09-05. Scope: software behavior of the final research/demo runtime. This is not clinical validation, medical advice, or regulatory certification.

| Check | Result | Evidence |
| --- | --- | --- |
| `clinical_use=false` | Pass | `/api/v1/models/final/status/` returns `clinical_use: false`; both final services report `research_demo`. |
| Research/educational disclaimer | Pass | Final result and evidence UI labels the application as research/educational and not for clinical diagnosis. |
| No diagnosis-certainty claim | Pass | UI describes model output as support for screening and directs users to qualified clinical evaluation. |
| Unsupported medical advice constrained | Pass | Advisor prompts/local fallback state that outputs are not diagnosis and advise clinical evaluation for concerning findings. |
| Multimodal is experimental only | Pass | API status returns `multimodal_status: experimental_only`; no paired fusion validation is claimed. |
| No ML legacy fallback | Pass | `FinalMLRuntimeService` serves only the frozen Logistic Regression artifact and fails unavailable on missing/checksum-invalid artifact. |
| No DL legacy fallback | Pass | `FinalDLRuntimeService` serves only frozen EfficientNet-B0 and frozen Platt metadata; missing/checksum-invalid artifact fails unavailable. |
| Missing/checksum mismatch fails closed | Pass | Final runtime tests cover missing and checksum-invalid ML artifacts; DL runtime validates model and calibration SHA before load. |
| Invalid ML input handled | Pass | Pydantic feature validation returns a controlled `422`; final application verifier exercises it. |
| Corrupt DL image handled | Pass | Validated upload plus DL decoder returns controlled `400`; final application verifier exercises it. |
| User traceback exposure | Pass | Final prediction endpoints convert unexpected errors to fixed error details and do not return exception text. |
| Secret exposure | Pass | `.env` and runtime artifacts are ignored; readiness validator rejects tracked `.env`. |
| Host paths exposed through API | Pass | Final status returns a truncated SHA and operational metadata, not local artifact paths. |
| Password reset in production | Pass with operator requirement | API returns a reset token only in `APP_MAIL_MODE=file`; deployment requires `APP_MAIL_MODE=smtp`, where the response does not expose it. |
| Threshold-aware uncertainty | Pass | ML uses raw threshold `0.36`; DL compares raw probability with raw threshold `0.515`. Multimodal `0.5` wording is explicitly probability ambiguity, not a frozen model threshold. |

The historical `prediction.py` and `prediction_dl.py` remain reference/development code only. Production app import-boundary validation confirms `app.main` does not load either module, and final endpoints directly use `final_ml_runtime.py` and `final_dl_runtime.py`.
