# Final WDBC ML Error Analysis

## Scope

This report describes frozen outer-test predictions from the final WDBC protocol. `sample_index` is a dataset row identifier only; it is not a patient identifier. No clinical or pathological explanation is inferred from these tabular errors.

## Primary candidate: Logistic Regression

At its development-selected raw-probability threshold of 0.36, Logistic Regression has one false positive and two false negatives on the 114-sample outer test set. One of the three errors is within 0.10 probability units of the threshold; two are at least 0.25 probability units from it. The latter are high-confidence errors under the pre-specified descriptive rule and remain important despite the small error count.

The test score distribution and each error record are preserved in `experiments/final/ml_error_analysis.csv`. The primary candidate's final confusion counts are TN 71, FP 1, FN 2, TP 40. These outcomes do not justify any post-test threshold adjustment.

## Baseline comparison

Random Forest has one false positive and three false negatives; XGBoost has zero false positives and four false negatives at their own development-selected thresholds. Each has two high-confidence errors under the same descriptive distance rule. This comparison helps characterize the pre-specified models but is not used to redesign them after viewing the test set.

## Limitation

WDBC is a small, curated structured-data benchmark without external validation in this project. Error counts and bootstrap intervals quantify uncertainty in this locked holdout; they do not establish clinical safety, generalization, or a clinical decision threshold.
