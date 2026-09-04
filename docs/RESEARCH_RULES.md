# Research Rules

1. The source of truth for CBIS-DDSM split membership is `manifests/cbis_group_split_seed42.csv`.
2. Final results are written only under `experiments/final/`; `experiments/results/` is development/legacy evidence.
3. Train, validation and test have distinct roles: fit, select/calibrate, and final evaluation.
4. No architecture, threshold, fusion weight or calibration choice may use final test data.
5. A filename-prefix group is a conservative study-like unit, not a verified patient identity.
6. No final DL metric, figure, model weight or XAI result may be inherited from the legacy folder split.
7. Multimodal fusion is a demo heuristic unless paired clinical-image data supports a separate valid study.
8. SHAP and Grad-CAM are explanatory aids, not evidence of medical correctness or ground truth localization.
9. The system is a Research / Educational Prototype and not for clinical diagnosis.
10. Preserve legacy artifacts; label them rather than delete them unless an explicitly approved, reversible cleanup is required.
