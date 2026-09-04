# 1. Research scope

This repository contains two separate final research studies and a software demonstration. Study A evaluates classical models on WDBC structured measurements. Study B evaluates image models on CBIS-DDSM processed mammography images. Study C summarizes reliability, calibration, uncertainty, and explainability for the frozen candidates. Experimental multimodal integration remains a software demonstration only because the WDBC and CBIS-DDSM samples are not paired.

# 2. Dataset protocol

**Study A - WDBC structured ML.** `sklearn.datasets.load_breast_cancer` supplies 569 samples and 30 numeric features. The project label convention is 1 = malignant and 0 = benign (212 malignant, 357 benign). A fixed seed-42 stratified outer split reserves 114 samples for held-out description and retains 455 development samples.

**Study B - CBIS-DDSM imaging DL.** The final source is `manifests/cbis_group_split_seed42.csv`: 2,559 full processed images, 2,559 ROI representations, and 5,118 manifest rows. The manifest has 2,354 filename-prefix study-like groups with zero train/validation, train/test, and validation/test group overlap. This is not a verified patient-level split because complete patient/case metadata is absent from the local processed snapshot.

The legacy folder split is leakage-affected historical evidence and is not used for final metrics, tables, figures, or conclusions.

# 3. ML methodology

All ML model, calibration, and threshold decisions were made using five-fold stratified out-of-fold predictions within the 455-sample development set. Scaling is contained inside the Logistic Regression pipeline. Logistic Regression, Random Forest, and a newly trained healthy XGBoost model were compared. Raw and Platt probabilities were compared from development OOF estimates; each model's frozen threshold was selected from development OOF balanced accuracy. The final test set was evaluated only after those decisions.

# 4. ML results

Within the WDBC structured-data study, all three frozen models showed strong held-out discrimination. Logistic Regression is the primary ML candidate because development OOF evidence, not final-test ranking, gave it the strongest ROC-AUC (0.9950), PR-AUC (0.9941), selected-probability balanced accuracy (0.9724), lowest Brier score (0.0200), and fewest OOF FN (4). It retained raw probabilities and a frozen threshold of 0.36.

On its held-out test description, Logistic Regression had ROC-AUC 0.9954, PR-AUC 0.9932, sensitivity 0.9524, specificity 0.9861, balanced accuracy 0.9692, 2 FN, and 1 FP. Its 2,000-replicate bootstrap ROC-AUC interval was 0.9858-1.0000 and balanced-accuracy interval was 0.9299-1.0000. Random Forest and XGBoost remain comparison models; their final-test values do not revise the development-first candidate decision.

The two LR FNs and one FP are documented without clinical interpretation. SHAP explains feature contributions to the fitted Logistic Regression log-odds: `worst texture` has the largest mean absolute contribution in the frozen test explanation set. SHAP is non-causal and post-hoc.

# 5. DL methodology

Final DL training and evaluation use the manifest-driven inferred study-like split, fixed seed 42, full processed images unless stated otherwise, validation-based checkpoints and thresholds, and no test-time augmentation. Custom CNN, frozen ImageNet ResNet50, and frozen ImageNet EfficientNet-B0 are comparison architectures. Architecture selection was validation-first. EfficientNet-B0 was selected for the pre-specified ROI experiment by validation ROC-AUC, not test performance.

# 6. DL results

Within the CBIS-DDSM imaging study, EfficientNet-B0 full processed images was the strongest evaluated DL architecture under the leakage-controlled protocol and is retained as a research candidate. Its final-test description is ROC-AUC 0.7229, PR-AUC 0.6564, sensitivity 0.6786, specificity 0.6250, balanced accuracy 0.6518, and 54 FN. ResNet50 had higher sensitivity (0.7202) and fewer FN (47), but much lower specificity (0.4152); Custom CNN had lower discrimination and sensitivity.

For EfficientNet-B0, Platt calibration was selected from validation OOF reliability (validation Brier 0.2118 versus 0.2327 raw). The frozen balanced threshold is approximately 0.515. The 2,000-replicate test bootstrap interval is 0.6720-0.7722 for ROC-AUC and 0.6024-0.7007 for balanced accuracy. Test error description at the balanced point contains 54 FN and 84 FP; these results remain research-grade evidence, not clinical performance claims.

Grad-CAM was run after model freeze with checksum verification and deterministic TP/TN/FP/FN case selection. It is a qualitative attention visualization, not lesion localization, pathology evidence, or causal explanation.

# 7. Ablation result

The controlled EfficientNet-B0 full-versus-ROI experiment is **ROI-C**. On validation, ROI reduced ROC-AUC from 0.7044 to 0.6789, PR-AUC from 0.6152 to 0.6060, and sensitivity from 0.6813 to 0.5125. Although ROI specificity increased, it did not satisfy the validation-first discrimination and screening-sensitivity criterion. Full processed images remain the retained representation. Test values are descriptive confirmation and were not used to choose the representation.

# 8. Explainability

WDBC SHAP uses `LinearExplainer` with development-only background data and explains feature contributions to the frozen Logistic Regression malignant log-odds. It is not a causal or medical explanation. CBIS-DDSM Grad-CAM uses the frozen final EfficientNet-B0 full-image model and demonstrates coarse activation patterns on selected examples. It is not a segmentation or ground-truth localization method.

# 9. Scientific findings

- Within WDBC, the development-first protocol retained Logistic Regression as the most stable and calibrated primary classical-ML candidate.
- Within CBIS-DDSM, EfficientNet-B0 full images was the strongest evaluated DL architecture under the final inferred-group manifest protocol.
- The ROI-only representation was rejected by its pre-specified validation-first criterion.
- Calibration, uncertainty estimates, error summaries, SHAP, and Grad-CAM improve characterization of the frozen models but do not establish clinical utility.
- There is no valid cross-dataset ML-versus-DL head-to-head comparison, and no validated multimodal performance claim.

# 10. Limitations

- CBIS-DDSM grouping is not verified patient-level grouping.
- Neither study has external validation in this repository.
- DL discrimination is moderate and uncertainty remains material.
- WDBC and CBIS-DDSM are distinct datasets/modalities without paired multimodal evaluation.
- Grad-CAM is qualitative only and SHAP is non-causal.
- The system is a research / educational prototype, not a clinical diagnostic tool.

# 11. Contributions

- A reproducible WDBC outer-holdout and development-OOF classical ML study with calibration, threshold, bootstrap, error, and SHAP artifacts.
- A manifest-driven CBIS-DDSM DL protocol with inferred-group overlap checks, baseline comparison, controlled ROI ablation, reliability analysis, and checksum-verified Grad-CAM.
- A machine-readable final snapshot and provenance manifest that connect final research evidence to paper-ready tables and figures.
- Explicit separation of research evidence from runtime and multimodal demonstration behavior.

# 12. Future work

- Obtain patient/case metadata for a verified CBIS-DDSM patient-level split.
- Perform external validation for both study types.
- Assemble a paired tabular-image dataset before evaluating multimodal fusion.
- Conduct additional robustness, subgroup, and prospective-style studies under a newly specified protocol.

# 13. Final conclusion

The final artifacts support conservative, modality-specific conclusions only. Logistic Regression is the frozen primary candidate within the WDBC structured-data study, and EfficientNet-B0 full processed images is the frozen retained candidate within the CBIS-DDSM imaging study. Neither candidate is promoted to runtime or clinical use by this research synthesis.
