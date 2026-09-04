# DL Baseline and ROI Analysis

## Scope and selection rule

All full-image baselines and the ROI ablation use the same manifest, inferred group split, seed, label mapping, image size, ImageNet initialization policy, optimizer, learning-rate policy, epoch budget, early stopping, checkpoint rule and validation threshold-selection method. The sole independent variable in DL-04 is the representation: full processed image versus ROI image.

EfficientNet-B0 was selected for DL-04 by validation ROC-AUC (0.7044), not by test metrics.

## Validation-first result

| Metric | Full validation | ROI validation | Delta (ROI - Full) |
| --- | ---: | ---: | ---: |
| ROC-AUC | 0.7044 | 0.6789 | -0.0255 |
| PR-AUC | 0.6152 | 0.6060 | -0.0092 |
| Sensitivity | 0.6813 | 0.5125 | -0.1688 |
| Specificity | 0.6348 | 0.7739 | +0.1391 |
| Balanced Accuracy | 0.6580 | 0.6432 | -0.0148 |
| Brier | 0.2327 | 0.2351 | +0.0024 |

**Decision: CASE ROI-C.** ROI lowers validation discrimination and sensitivity. Its specificity gain does not compensate for the screening-relevant loss of sensitivity under the pre-specified primary criterion. Full processed image remains the representation candidate.

## Confirmatory test description

ROI test ROC-AUC is 0.7240 versus 0.7229 for full image, but its sensitivity falls from 0.6786 to 0.5536 and FN rises from 54 to 75. These test values describe generalization only and were not used to choose the representation.

## Questions

1. **Why EfficientNet-B0 is stronger:** it has the best full-image ROC-AUC, PR-AUC, balanced accuracy and Brier score; its pretrained feature extractor provides a more favorable trade-off than the compact Custom CNN and the low-specificity ResNet50 baseline.
2. **Does ROI help:** not under validation-first discrimination and screening sensitivity. ROI is rejected for the current final representation.
3. **Sensitivity/specificity:** ResNet50 favors sensitivity at high false-positive cost. Full EfficientNet-B0 offers the most balanced final baseline; ROI shifts too far toward specificity.
4. **False negatives:** Custom CNN 91, ResNet50 47, EfficientNet full 54, EfficientNet ROI 75. ROI worsens missed malignant samples materially.
5. **Learning curves:** no obvious catastrophic divergence is evident in saved histories; however, moderate AUC and imperfect calibration indicate remaining room for reliability analysis.
6. **Final candidate readiness:** EfficientNet full is a research candidate, not a clinical model or production promotion decision.
7. **Next phase:** calibration and error analysis should precede any new architecture/training experiment. No additional DL training is proposed.
