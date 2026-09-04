# Final Dataset Protocol

## Purpose

This protocol defines the source-of-truth datasets and split discipline for final research artifacts. It replaces any reliance on the legacy CBIS-DDSM folder split for final DL training or evaluation.

## Study A: WDBC structured data

- Source: `sklearn.datasets.load_breast_cancer` (WDBC).
- Samples: 569; 357 benign and 212 malignant under the project convention.
- Features: 30 numeric tumor characteristics.
- Label convention: `1 = malignant`, `0 = benign`.
- Split: stratified, fixed seed 42. Final protocol must keep a validation partition for threshold/model selection and a separate locked test partition for final reporting.
- Scaling/calibration: fitted using training data and internal cross-validation only; validation selects threshold; test is evaluation only.

## Study B: CBIS-DDSM processed mammography images

- Source of truth: `manifests/cbis_group_split_seed42.csv`.
- Manifest rows: 5,118, comprising full processed images and ROI representations.
- Group count: 2,354.
- Group strategy: filename prefix before `__`.
- Seed: 42; group allocation: 70% train, 15% validation, 15% test per class after rounding.
- Group overlap: zero for train/validation, train/test, and validation/test.
- Unit of analysis: image representation for DL input; unit of split independence: inferred study-like group.
- Limitation: no complete patient/case metadata is available in the local processed snapshot. This is a conservative study-like group split, **not a verified patient-level split**.

## Allowed data usage

| Split | Permitted use |
| --- | --- |
| Train | Model fitting and train-only augmentation |
| Validation | Early stopping, architecture choice, calibration and threshold selection |
| Test | One-time final independent evaluation only |

Validation and test must not receive random augmentation. Any test-time augmentation must be predeclared, deterministic/reproducible, and reported separately from the standard evaluation.

## Required integrity checks

- Every manifest row resolves to exactly one declared split.
- A `group_id` appears in one split only.
- A group has one class label only.
- Training code reads samples directly from the manifest and does not rediscover split membership from legacy directories.
- Final reports identify full-image and ROI representations correctly and do not call 5,118 rows independent patients or cases.
