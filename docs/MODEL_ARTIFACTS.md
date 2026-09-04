# Model Artifacts

Audit date: 2026-09-04

Model weights and serialized estimators are not stored in normal Git. Keep them in a release artifact, server volume, or external artifact store, then place them at the expected paths below before running inference.

Recommended strategy for this project: use GitHub Releases for final inference artifacts, plus a server volume for deployment. Do not commit `.keras`, `.pkl`, `.h5`, `.pt`, `.pth`, or `.onnx` files to the repository.

## Required Runtime Artifacts

| Model | Filename | Expected path | Current role | Version | SHA-256 |
| ----- | -------- | ------------- | ------------ | ------- | ------- |
| Custom CNN | `custom_cnn_best.keras` | `backend/custom_cnn_best.keras` | Backend demo DL fallback/discovery | local legacy | `b6ceb487f7b03b40264f58a358d56e62dbdd439d24e6b00383f5e8c2960d3022` |
| EfficientNetB0 | `efficientnetb0_best.keras` | `backend/efficientnetb0_best.keras` | Optional DL inference artifact | local legacy | `3ed64096d62f14e28f37b3f48fb94bc96610a4ee860b896b9275b867b66b7b0e` |
| ResNet50 | `resnet50_best.keras` | `backend/resnet50_best.keras` | Optional DL inference artifact | local legacy | `3a6fe0e1a52c1947c6adb9f78101416d26c8ee9478a544c497a1325660e2836d` |
| Wisconsin Logistic Regression | `wisconsin_logistic_regression_20260404_retrained.pkl` | `models/wisconsin_logistic_regression_20260404_retrained.pkl` | ML baseline candidate | 20260404 retrained | `c0f45867b88082b00fd27657e87c4786b9243f1a5de8928eb07b54fca26467c6` |
| Wisconsin Random Forest | `wisconsin_random_forest_20260404_retrained.pkl` | `models/wisconsin_random_forest_20260404_retrained.pkl` | ML baseline candidate | 20260404 retrained | `a91b7c0af0f5cd599ff5ae6b0ea0737f5c5b8c405b8beaf43b298c4d58ce74a7` |

## Local Research Artifacts

| Artifact | Expected path | Notes | SHA-256 |
| -------- | ------------- | ----- | ------- |
| Custom CNN canonical copy | `models/deep_learning/custom_cnn_best.keras` | Research copy; duplicate role should be consolidated later | `ccb47928b1cb3811cab47d0015f066992b621a76ef38c9a3b22115a5faba4417` |
| Custom CNN calibrated | `models/deep_learning/custom_cnn_finetuned_calibrated.keras` | Local calibrated experiment artifact | `720fccf568b2af22aa0b059bfa0c2730e3c09421da901a8e1437902da2de16d4` |
| Custom CNN calibrated refresh | `models/deep_learning/custom_cnn_finetuned_calibrated_refresh.keras` | Local calibrated refresh artifact | `bf42db7b75156daf374b2b1bc0e697d32d314f279345c39ddd844cd10c8447f0` |
| Custom CNN calibrated smoke | `models/deep_learning/custom_cnn_finetuned_calibrated_smoke.keras` | Smoke/test artifact; not a release candidate | `2be710e45f684c5138eb3af3eeb3583f4783733fea2ab296a0f0fb28b209c495` |
| Custom CNN retrained balanced | `models/deep_learning/custom_cnn_retrained_balanced.keras` | Local experiment artifact | `116bde100593cf69ab536bf1c3045c1bfea7d548e6320713c278a804108e99b7` |
| Custom CNN v2 ROI | `models/deep_learning/custom_cnn_v2_finetuned_roi.keras` | ROI experiment artifact | `095f722c27a1e0de2fa3be2d36f1c8eb7a029c674780c19c4d2057a803cd2349` |
| DL image Random Forest | `models/deep_learning/dl_image_rf_20260404.pkl` | Experimental image-feature model | `231deb8625343cc3c4defdb44da64c4bea60fc97afbf14859faba26e73b1ac72` |

## Release Flow

1. Rebuild leakage-safe CBIS-DDSM split.
2. Train final candidate models with fixed seeds and committed config.
3. Evaluate exactly once on the locked test set.
4. Select final inference artifacts.
5. Create a GitHub Release such as `models-vYYYYMMDD`.
6. Upload only final runtime artifacts and a checksum manifest.
7. On the server, download artifacts into a persistent volume mounted at the expected paths.

## Server Placement

For Docker/VPS deployment, keep model files outside the image and mount them into the container:

```text
/opt/breast-cancer-ai/models/backend/custom_cnn_best.keras -> backend/custom_cnn_best.keras
/opt/breast-cancer-ai/models/backend/efficientnetb0_best.keras -> backend/efficientnetb0_best.keras
/opt/breast-cancer-ai/models/backend/resnet50_best.keras -> backend/resnet50_best.keras
```

The current model artifacts are legacy/local until the CBIS-DDSM leakage blocker is fixed. Do not use them for final scientific claims.
