# 1. Candidate model

EfficientNet-B0 on full processed images is the frozen final DL research candidate. Its architecture, weights, manifest and representation are frozen after this phase; it is not promoted to runtime and is not a clinical diagnostic model.

# 2. Why this candidate was selected

EfficientNet-B0 full image was selected from the baseline architectures by validation-first comparison (validation ROC-AUC 0.7044). The controlled ROI experiment was CASE ROI-C: ROI validation ROC-AUC decreased to 0.6789 with substantial sensitivity loss, so full image remains the candidate representation.

# 3. Calibration

Raw probability reliability was compared with 5-fold out-of-fold validation calibration estimates. Platt is selected by validation reliability, not test discrimination: validation Brier/log loss/ECE are 0.2118/0.6086/0.0221 for Platt versus 0.2327/0.6580/0.1139 raw. Isotonic improved Brier but was less stable by validation log loss than Platt.

The final Platt calibrator is fitted only on the complete validation set and applied once to test, yielding test Brier/log loss/ECE 0.2088/0.6024/0.0470. Calibration improves probability reliability; it is not an architecture or model-selection claim.

# 4. Threshold analysis

The frozen balanced operating point is approximately 0.515, selected on validation balanced accuracy and described on test as sensitivity 0.6786, specificity 0.6250, FN 54 and FP 84.

A pre-specified **research sensitivity-oriented operating point** was selected only on validation: maximize specificity subject to sensitivity at least 0.80. Validation selected threshold 0.48. Its one-time test description is sensitivity 0.8095, specificity 0.4643, FN 32, FP 120 and balanced accuracy 0.6369. It is not a clinical threshold.

# 5. Error analysis

At the balanced operating point, test contains 54 FN and 84 FP. Mean malignant probability is 0.4708 for FN and 0.5520 for FP. There are no errors at least 0.25 from the threshold under the recorded definition; 130 errors are within 0.10 of it. This suggests many errors are near the operating boundary, but it does not establish a pathological subtype or filename-based causal explanation.

Prediction exports retain sample indexes but not group identifiers. No patient information or pathology claims are inferred from filenames.

# 6. Bootstrap uncertainty

Two thousand fixed-seed bootstrap replicates on frozen test predictions produced: ROC-AUC 0.7229 (95% CI 0.6720-0.7722), PR-AUC 0.6564 (0.5802-0.7343), sensitivity 0.6786 (0.6073-0.7457), specificity 0.6250 (0.5609-0.6875), and balanced accuracy 0.6518 (0.6024-0.7007). All 2,000 replicates contained both classes.

# 7. Interpretation

The model has moderate discrimination and a more balanced trade-off than the other DL baselines. Platt calibration improves probability reliability on validation and test. The sensitivity-oriented research point reduces FN but produces many more FP, so operating-point choice must be documented rather than treated as universally better.

# 8. Limitations

- Study-like grouping is not a verified patient-level split.
- There is no external validation.
- Dataset size limits precision of estimates.
- The system makes no clinical-use or diagnostic claim.
- Current performance remains research-grade/demo evidence only.

# 9. Decision

- **CALIBRATION:** PLATT, selected by OOF validation reliability.
- **OPERATING POINT:** frozen balanced threshold plus documented sensitivity-oriented research threshold.
- **DL TRAINING:** FROZEN.
- **NEXT:** Grad-CAM / XAI on the frozen EfficientNet-B0 full-image candidate.
