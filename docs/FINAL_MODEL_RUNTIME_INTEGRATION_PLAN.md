# Final Model Runtime Integration Plan

This is a plan only. No file below is modified in the promotion-review branch.

1. `backend/app/services/prediction.py`
   - Replace historical `.pkl` discovery and fallback training with explicit registry loading of `wdbc-logistic-regression-v1`.
   - Map request fields to the 30-item contract order, pass raw values to the saved pipeline, validate SHA-256, take `predict_proba(...)[1]`, and decide at raw threshold 0.36.
   - Remove empirical rank display transformation from final-candidate decision logic; expose version, probability space, threshold, and research disclaimer.

2. `backend/app/services/prediction_dl.py`
   - Replace mtime/profile model discovery with an explicit registry selection for EfficientNet-B0 full image only after the DL blocker is resolved.
   - Reproduce final decode/RGB/float32/TensorFlow resize preprocessing and verify the `.keras` SHA-256 before serving.
   - Do not load `calibration_profile.json`, fit Isotonic at runtime, use empirical postprocessing, or silently use 0.48. Apply 0.515 only to raw probability.
   - Load the versioned frozen Platt artifact only when supplied; otherwise surface a blocked readiness state rather than substitute a calibrator.

3. `backend/app/api/endpoints.py` and response schemas
   - Return selected model ID/version, artifact verification state, raw-versus-calibrated probability semantics, threshold space, and research-only disclaimer.
   - Keep experimental multimodal output distinctly labelled and do not treat it as validated fusion.

4. New registry/health support
   - Add a runtime registry loader based on `models/model_registry.example.json` schema and a local deployment-specific registry.
   - Extend health/status endpoints to distinguish `loaded`, `healthy`, `promotion_candidate`, `blocked`, and `legacy` without exposing sensitive filesystem details.

5. Tests
   - Add known-input ML pipeline parity, 0.36 threshold-boundary, feature-order, and SHA mismatch tests.
   - Add DL SHA, preprocessing parity, raw-space 0.515 boundary, 0.48-not-default, legacy-profile rejection, and missing-Platt-blocker tests.
   - Add API metadata/disclaimer and no-fallback-training tests.

6. Documentation and deployment
   - Publish the deployment-specific registry without weights, document model-volume placement and checksums, and keep artifacts out of Git.
   - Gate DL runtime integration on a reviewed frozen Platt artifact/probability-display resolution. No clinical promotion follows from technical integration.
