# Final DL Experiment Log

All entries use `manifests/cbis_group_split_seed42.csv`, `image_set=images`, seed 42, validation-based checkpoint/threshold selection, and no test-time augmentation. Models are final research candidates only; none is promoted to runtime.

## DL-01: Custom CNN full image

- **Hypothesis:** A compact domain baseline can learn a discriminative signal from full processed images.
- **Training strategy:** Custom CNN; rescaling 1/255; 224 input; focal loss; class weights; early stopping on validation ROC-AUC.
- **Test result:** ROC-AUC 0.6153, PR-AUC 0.5207, sensitivity 0.4583, specificity 0.6518, FN 91.
- **Interpretation:** A valid baseline but weak screening sensitivity and discrimination.
- **Decision:** Retain only as baseline; no tuning in this phase.

## DL-02: ResNet50 full image

- **Hypothesis:** ImageNet-pretrained ResNet50 may improve feature extraction over Custom CNN.
- **Training strategy:** ImageNet ResNet50 backbone, frozen; `resnet50.preprocess_input`; 224 input; focal loss; class weights; validation selection.
- **Test result:** ROC-AUC 0.6278, PR-AUC 0.5844, sensitivity 0.7202, specificity 0.4152, FN 47.
- **Interpretation:** It reduces false negatives substantially, but this is paired with a high false-positive count (131) and low specificity.
- **Decision:** Retain as high-sensitivity comparator; do not promote or tune from test results.

## DL-03: EfficientNet-B0 full image

- **Hypothesis:** ImageNet-pretrained EfficientNet-B0 provides a better accuracy-efficiency tradeoff for the processed mammography input.
- **Training strategy:** ImageNet EfficientNet-B0 backbone, frozen; EfficientNet preprocessing; 224 input; focal loss; class weights; validation selection.
- **Test result:** ROC-AUC 0.7229, PR-AUC 0.6564, sensitivity 0.6786, specificity 0.6250, FN 54, Brier 0.2297.
- **Interpretation:** Best discrimination, calibration proxy, balanced accuracy and specificity among final baselines, while preserving substantially higher sensitivity than Custom CNN.
- **Selection rule before DL-04:** Selected for ROI ablation by highest baseline **validation** ROC-AUC (0.7044), with validation PR-AUC 0.6152 and balanced accuracy 0.6580. Test metrics were not used to choose the architecture or representation experiment.
- **Decision:** Candidate for one controlled full-image versus ROI ablation. No production promotion.

## Baseline comparison decision

**CASE A.** EfficientNet-B0 is clearly strongest overall by ROC-AUC, PR-AUC, balanced accuracy and Brier score. ResNet50 has marginally higher sensitivity and fewer FN, but its specificity is markedly lower. The next and only proposed training experiment is a controlled EfficientNet-B0 ROI ablation with all non-representation settings fixed.

## DL-04: EfficientNet-B0 ROI ablation

- **Hypothesis:** ROI preprocessing may help EfficientNet-B0 focus on lesion signal and improve discrimination over full processed images.
- **Controlled variable:** `image_set=images_roi`; all other recorded EfficientNet-B0 full-image settings were retained.
- **Validation-first result:** ROI ROC-AUC 0.6789 versus full 0.7044; PR-AUC 0.6060 versus 0.6152; sensitivity 0.5125 versus 0.6813; specificity 0.7739 versus 0.6348.
- **Test description:** ROI ROC-AUC 0.7240 versus full 0.7229, but sensitivity is 0.5536 versus 0.6786 and FN is 75 versus 54. These values did not drive selection.
- **Decision:** **CASE ROI-C.** Reject ROI as the final representation candidate; retain full processed image. Stop DL training and proceed to calibration plus error analysis.
