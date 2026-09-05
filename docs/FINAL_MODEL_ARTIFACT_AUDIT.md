# Final Model Artifact Audit

This audit classifies local artifacts without deleting or modifying them. `PROMOTION_CANDIDATE` means eligible for a later controlled research/demo integration review; it does not mean clinical approval.

| Artifact | Type | Research provenance | Current runtime use | Health | Final eligibility | Required future action |
| --- | --- | --- | --- | --- | --- | --- |
| `experiments/final/ml_runs/logistic_regression/logistic_regression_final_seed42.joblib` | ML | Final WDBC study, SHA verified | Not discovered; runtime scans root `.pkl` files | Healthy pipeline, 30 features, classes `[0,1]` | PROMOTION_CANDIDATE | Load by explicit registry path; use raw p and 0.36 |
| `experiments/final/ml_runs/random_forest/random_forest_final_seed42.joblib` | ML | Final WDBC comparison | Not discovered | Healthy final comparison | RESEARCH_BASELINE | Keep comparison-only |
| `experiments/final/ml_runs/xgboost/xgboost_final_seed42.joblib` | ML | Final WDBC comparison, new healthy XGBoost | Not discovered | Healthy probabilities in final study | RESEARCH_BASELINE | Keep comparison-only |
| `models/wisconsin_logistic_regression_20260404_retrained.pkl` | ML | Historical dated retrain | Auto-discovered by current runtime | Legacy provenance, not byte-verified to final | LEGACY | Stop auto-discovery in future integration |
| `models/wisconsin_random_forest_20260404_retrained.pkl` | ML | Historical dated retrain | Auto-discovered by current runtime | Legacy provenance | LEGACY | Stop auto-discovery in future integration |
| Historical XGBoost artifact | ML | Earlier artifact described as unhealthy | Not present as a current final artifact | Unhealthy/reproducibility failure | UNHEALTHY | Do not restore or expose |
| `models/deep_learning/custom_cnn_final_seed42.keras` | DL | Final DL baseline | Not current default by final contract | Baseline only | RESEARCH_BASELINE | Keep for comparison |
| `models/deep_learning/resnet50_final_seed42.keras` | DL | Final DL baseline | Not current default by final contract | Baseline only | RESEARCH_BASELINE | Keep for comparison |
| `models/deep_learning/efficientnetb0_final_seed42.keras` | DL | Final EfficientNet-B0 full candidate, SHA verified | Not selected by current runtime | Model healthy; calibration artifact incomplete | BLOCKED | Persist/recover frozen Platt artifact and implement explicit raw decision contract |
| `models/deep_learning/efficientnetb0_roi_final_seed42.keras` | DL | Controlled ROI ablation | Could be discovered by timestamp if experimental exposure enabled | ROI-C rejected | RESEARCH_BASELINE | Never select automatically |
| `models/deep_learning/custom_cnn_finetuned_calibrated_refresh.keras` | DL | Historical refresh | Preferred by legacy calibration profile | Legacy Custom CNN profile | LEGACY | Replace implicit profile-driven promotion in future integration |
| `models/deep_learning/custom_cnn_*.keras`, `*_best.keras`, `dl_image_rf_20260404.pkl` | DL | Historical/smoke/development artifacts | May be auto-discovered | Mixed/unknown provenance | LEGACY or UNUSED | Retain local; exclude from explicit registry |
| `models/deep_learning/calibration_profile.json` | Calibration | Legacy Custom CNN empirical/Isotonic profile | Loaded by current DL runtime | Incompatible with final EfficientNet contract | LEGACY | Do not apply to final candidate |
