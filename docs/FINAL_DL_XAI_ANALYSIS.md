# Final DL XAI / Grad-CAM Analysis

## Scope and frozen candidate

This analysis applies only to the frozen EfficientNet-B0 full processed-image candidate. It uses the fixed manifest test order, the saved model checksum `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b`, and the validation-selected raw-probability threshold of 0.515. It does not retrain the model, change its weights, alter the threshold, or select an operating point from test results.

`scripts/generate_final_dl_gradcam.py` dynamically selects the final spatial convolutional layer in the saved network (`top_conv`). It reproduces the final trainer's TensorFlow decode-and-resize path, then confirms that each selected image reproduces its frozen exported raw probability before its Grad-CAM is written.

## Selection protocol

The clean `images` records in `manifests/cbis_group_split_seed42.csv` are filtered to the fixed test split in manifest order and matched exactly to `test_predictions.csv`. Selection uses no visual inspection: within each outcome type, it chooses the case nearest the median absolute distance from the frozen threshold and a distinct case with the greatest distance. There are two each of TP, TN, FP, and FN.

The test outcome counts are TP 114, TN 140, FP 84, and FN 54. `metadata.csv` records the sample index, manifest group ID and path, labels, raw probability, validation-only Platt probability, threshold, outcome, selection reason, dimensions, output paths, and Grad-CAM layer. Platt probabilities are descriptive metadata only; Grad-CAM and sample selection use raw neural-model probabilities.

## Visible observations

The generated TP examples show broad activation over substantial portions of the processed image rather than a sharply bounded point. The TN examples also contain activation, but their raw malignant probabilities remain below the frozen threshold. This is a qualitative visual observation from the generated overlays, not evidence that activation identifies pathology.

The selected FP and FN examples include broad or edge-adjacent activation patterns. In particular, the high-confidence FP overlay concentrates strongly around a small bright feature within a larger activated region, while the selected FN overlays do not show a consistently localized malignant-specific pattern. These eight deterministic examples are illustrative only and are not a quantitative localization study.

## Failure observations

The test set has 84 false positives and 54 false negatives at the frozen 0.515 threshold. The selected FP examples demonstrate that a confident malignant prediction can occur for a benign-labelled processed image; selected FN examples demonstrate that a malignant-labelled image can remain below threshold. Grad-CAM does not explain the clinical cause of either outcome and must not be used to infer lesion boundaries, pathology, or causality.

## Limitations

- Grad-CAM is a coarse model-attention visualization, not a segmentation mask or proof of diagnostic reasoning.
- The source snapshot supports only conservative study-like grouping, not verified patient-level grouping.
- Inputs are resized to 224 by 224 for the frozen model; overlays show that model-input representation.
- The fixed test set is used only to describe the pre-specified candidate. These visualizations must not drive preprocessing, architecture, threshold, or retraining changes.
- The model remains a research / educational prototype and is not for clinical diagnosis.

## Artifacts

- `experiments/final/gradcam/selection.json` and `experiments/final/gradcam_selection.json`: deterministic selection and checksum record.
- `experiments/final/gradcam/metadata.csv`: selected-case provenance and probabilities.
- `experiments/final/gradcam/{tp,tn,fp,fn}/`: original model-input image, Grad-CAM heatmap, and overlay for each selected case.
- `experiments/final/figures/efficientnet_gradcam_examples.png`: 2 by 4 representative overlay figure.

## Decision

Final DL XAI / Grad-CAM is complete for the frozen EfficientNet-B0 full-image candidate. The next research phase is final ML re-evaluation. No further DL training is authorized from these Grad-CAM outputs.
