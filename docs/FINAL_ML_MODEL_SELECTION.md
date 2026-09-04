# Final WDBC ML Model Selection

## Protocol

The WDBC source is `sklearn.datasets.load_breast_cancer`: 569 samples, 30 numeric features, 212 malignant and 357 benign after explicitly converting sklearn's target to the project convention `1 = malignant`, `0 = benign`. A single stratified outer test holdout (20%, seed 42) is locked in `experiments/final/ml_split_seed42.csv`; it contains 114 samples. The remaining 455 samples are development data.

All development decisions use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`. Scaling for Logistic Regression is inside its sklearn pipeline. There is no SMOTE or other resampling. The outer test set was not used for model configuration, calibration selection, threshold selection, or candidate selection.

## Models and health

The pre-specified comparison contains Logistic Regression, Random Forest, and a newly trained XGBoost model. XGBoost 3.2.0 was available, trained reproducibly with a fixed configuration, and passed probability-health checks: finite probabilities in `[0, 1]` with non-constant output. No historical XGBoost artifact was reused.

## Development comparison

| Model | OOF ROC-AUC | OOF PR-AUC | OOF Sensitivity | OOF Specificity | OOF Balanced Accuracy | CV ROC-AUC mean +/- SD | CV PR-AUC mean +/- SD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.9950 | 0.9941 | 0.9765 | 0.9684 | 0.9724 | 0.9954 +/- 0.0053 | 0.9944 +/- 0.0052 |
| Random Forest | 0.9876 | 0.9859 | 0.9588 | 0.9649 | 0.9619 | 0.9882 +/- 0.0074 | 0.9868 +/- 0.0068 |
| XGBoost | 0.9939 | 0.9924 | 0.9529 | 0.9895 | 0.9712 | 0.9935 +/- 0.0049 | 0.9920 +/- 0.0046 |

Full fold-level and OOF results are in `experiments/final/ml_cv_metrics.csv` and `experiments/final/ml_oof_predictions.csv`.

## Calibration and thresholds

Raw and Platt calibration were compared with cross-fitted development OOF predictions. Selection criterion was minimum Brier score, then log loss.

| Model | Selected probability | OOF Brier | OOF Log Loss | Frozen OOF threshold |
| --- | --- | ---: | ---: | ---: |
| Logistic Regression | Raw | 0.0200 | 0.0755 | 0.36 |
| Random Forest | Platt | 0.0305 | 0.1141 | 0.44 |
| XGBoost | Raw | 0.0225 | 0.0849 | 0.60 |

Thresholds maximize development OOF balanced accuracy, with documented deterministic tie-breaks. They are research operating points, not clinical thresholds.

## Primary candidate

**Logistic Regression is the final ML candidate, not a runtime promotion.** It has the strongest development OOF ROC-AUC and PR-AUC, the highest selected-probability balanced accuracy, the fewest OOF false negatives (4), the best calibration by Brier/log loss, and low fold-to-fold variation. XGBoost is close on development balanced accuracy and has higher OOF specificity, but has lower OOF discrimination and more missed malignant examples (8). Random Forest trails both on OOF discrimination, calibration, and balanced accuracy.

The frozen final test is descriptive confirmation only. It must not trigger another WDBC configuration, calibration, threshold, or retraining change under this protocol.
