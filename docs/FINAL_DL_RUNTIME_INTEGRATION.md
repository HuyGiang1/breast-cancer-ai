# Final DL runtime integration

The research/demo DL runtime serves only `cbis-efficientnetb0-full-v1`, the frozen EfficientNet-B0 full processed-image candidate. It is not a clinical diagnostic model.

## Artifact and preprocessing

The service resolves `FINAL_DL_MODEL_PATH` or the registry artifact path, verifies SHA-256 `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b`, and verifies input/output shapes `(224, 224, 3)` and `(1,)`. Preprocessing exactly matches the frozen trainer: TensorFlow RGB decode, float32 cast, and `tf.image.resize(..., (224, 224))`. EfficientNet preprocessing remains inside the saved model graph.

## Probability and calibration

The sigmoid output is `raw_probability`. Classification is always `raw_probability >= 0.515`. The frozen Platt JSON is checksum-verified and maps raw probability to `calibrated_probability` for display/reliability only. The calibrated probability is never compared with `0.515`; `0.48` remains research-only.

## API and failure behavior

`POST /api/v1/predict/image/` returns raw and calibrated probability separately, model metadata, Platt calibration, raw decision threshold and research/demo status. `GET /api/v1/models/final/status/` reports final ML and DL status together. Missing/checksum-invalid model or calibration artifacts return HTTP 503; corrupt images return controlled HTTP 400.

## Legacy isolation and limitations

The final endpoint does not discover `.keras` files, select by mtime, use Custom CNN/ResNet/ROI fallbacks, or load the legacy calibration profile. The old DL service remains development/reference-only. Runtime Grad-CAM is not integrated. Multimodal fusion remains experimental only; no paired multimodal validation or clinical claim exists.

## Runtime parity

`scripts/verify_final_dl_runtime_parity.py` checks frozen TP, TN, FP and FN images through final preprocessing/model/calibration. It reproduced raw test predictions within `5.960e-08` and calibrated outputs within `1.295e-07`.
