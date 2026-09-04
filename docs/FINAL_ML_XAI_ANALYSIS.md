# 1. Objective

This post-hoc SHAP analysis describes feature contributions to the frozen final WDBC Logistic Regression model output. It does not select features, retrain a model, change calibration, change threshold, or promote a runtime model.

# 2. Frozen model and dataset

The model is the checksum-verified final `StandardScaler -> LogisticRegression` artifact from the final ML study. The SHA-256 is `15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755`. It uses 30 WDBC features, the locked seed-42 split in `experiments/final/ml_split_seed42.csv`, raw malignant probabilities, the label convention `1 = malignant` and `0 = benign`, and the frozen research threshold 0.36.

The SHAP explanation set is the same 114-sample final held-out test set used for the frozen report. Its use here is descriptive only.

# 3. SHAP methodology

`shap.LinearExplainer` explains the Logistic Regression classifier in the transformed feature space after the frozen `StandardScaler`. Its reference/background is the 455 locked development samples only; no test sample is used as background. The exact 30 sklearn WDBC feature names are attached to the transformed SHAP explanation, including local waterfall plots.

SHAP values are on the **log-odds of the malignant class** scale. A positive value contributes toward a higher fitted-model malignant log-odds; a negative value contributes toward lower fitted-model malignant log-odds. Values are not percentages, causal risk factors, biological causes, clinical proof, or diagnostic evidence.

# 4. Global feature contributions

Global ranking uses mean absolute SHAP over the frozen test set, not coefficient magnitude.

| Rank | Feature | Mean absolute SHAP | Mean SHAP |
| ---: | --- | ---: | ---: |
| 1 | worst texture | 1.2576 | -0.2763 |
| 2 | radius error | 0.8329 | -0.2358 |
| 3 | worst symmetry | 0.7576 | -0.1163 |
| 4 | compactness error | 0.7230 | -0.0527 |
| 5 | mean concave points | 0.7055 | -0.0135 |
| 6 | worst concavity | 0.6954 | -0.0570 |
| 7 | worst radius | 0.6751 | -0.1111 |
| 8 | worst area | 0.6431 | -0.1223 |
| 9 | worst concave points | 0.5729 | -0.0511 |
| 10 | mean concavity | 0.5372 | -0.0403 |

The mean signed value summarizes the frozen test distribution only. Direction for an individual prediction can differ, as the summary plot and waterfall examples show.

# 5. Correct prediction explanations

The deterministic representative TP is sample index 196 (true malignant, predicted malignant, probability 0.999). Its largest positive model-output contributions are `worst texture` (+1.95 log-odds), `radius error` (+0.84), `concave points error` (+0.78), `perimeter error` (+0.68), and `mean smoothness` (+0.62).

The deterministic representative TN is sample index 325 (true benign, predicted benign, probability 0.002). Its largest contributions include negative `worst texture` (-1.16), negative `radius error` (-1.01), positive `compactness error` (+0.84), negative `worst concavity` (-0.76), and negative `mean concave points` (-0.68). These are feature contributions under the fitted model, not explanations of biology or diagnosis.

# 6. Error explanations

The only FP is sample index 455 (true benign, predicted malignant, probability 0.643; 0.283 from threshold). `worst texture` (+3.79) is its largest positive contribution, alongside positive `mean texture` (+1.17) and `compactness error` (+0.69). Negative contributions from `worst symmetry` (-1.24), `worst concavity` (-0.90), and several other features partially countered, but did not offset, the fitted-model output. This is a high-confidence error by the pre-specified distance rule.

Both frozen FNs are included. Sample index 73 is true malignant but predicted benign at probability 0.086 (0.274 from threshold, high-confidence error). Its leading contributions are jointly negative: `worst texture` (-1.22), `radius error` (-0.70), `worst symmetry` (-0.56), `area error` (-0.42), and `perimeter error` (-0.39), with smaller positive contributions such as `texture error` (+0.44) and `symmetry error` (+0.38).

Sample index 190 is true malignant but predicted benign at probability 0.276 (0.084 from threshold, borderline error). Its pattern is mixed: a large negative `compactness error` contribution (-5.97) is partly offset by positive `worst symmetry` (+3.86), `worst texture` (+2.72), and `worst concavity` (+2.55). The two FNs therefore do not display the same local SHAP pattern: one has several leading negative contributions, while the other has competing contributions dominated by one negative feature contribution.

# 7. Interpretation

SHAP suggests that the frozen linear model uses combinations of standardized WDBC features, with `worst texture` and `radius error` having the largest average absolute contribution magnitudes in this held-out explanation set. Local examples demonstrate that the same feature can contribute in different directions for different samples. This describes model behavior under this fitted model only.

# 8. Limitations

- SHAP is a model explanation, not a causal explanation.
- WDBC features are engineered measurements; this analysis does not establish biological mechanism or clinical interpretation.
- No external validation dataset is included in this project.
- Feature correlations can affect attribution interpretation, especially for a linear model with correlated predictors.
- Test-set SHAP is post-hoc descriptive and cannot be used to revise the frozen evaluation protocol.
- This is a research / educational prototype, not a clinical diagnostic tool.

# 9. Final ML XAI conclusion

Final ML SHAP/XAI is complete for the frozen Logistic Regression candidate. No feature removal, retraining, calibration change, threshold change, candidate change, or runtime promotion is performed from these findings. The next phase is paper artifacts and final research synthesis.
