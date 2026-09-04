# Report Update Notes

These notes map the final machine-readable artifacts to future Word/PDF report edits. This branch does not modify Word or PDF files.

## Numbers to replace

- Replace any preliminary or historically dated WDBC model numbers with `paper_artifacts/tables/ml_model_comparison.csv`. The primary candidate statement must use development OOF selection evidence, not final-test ranking.
- Replace any legacy DL metrics with `paper_artifacts/tables/dl_model_comparison.csv` and `paper_artifacts/tables/roi_ablation.csv`.
- Replace preliminary calibration/uncertainty values with `paper_artifacts/tables/ml_calibration.csv`, `paper_artifacts/tables/dl_calibration.csv`, `paper_artifacts/tables/ml_bootstrap_ci.csv`, and `paper_artifacts/tables/dl_bootstrap_ci.csv`.
- Replace prior error counts with `paper_artifacts/tables/ml_error_summary.csv` and `paper_artifacts/tables/dl_error_summary.csv`.

## Tables to replace

- Dataset summary: `paper_artifacts/tables/dataset_statistics.csv`.
- WDBC model comparison: `paper_artifacts/tables/ml_model_comparison.csv`.
- CBIS-DDSM model comparison: `paper_artifacts/tables/dl_model_comparison.csv`.
- ROI ablation: `paper_artifacts/tables/roi_ablation.csv`.
- Calibration, uncertainty, error, and XAI summaries: remaining CSV files under `paper_artifacts/tables/`.

## Figures to replace

- WDBC ROC, PR, confusion, calibration, and SHAP: `paper_artifacts/figures/01_*` through `05_*`.
- CBIS-DDSM ROC, PR, confusion, calibration, threshold, and Grad-CAM: `paper_artifacts/figures/06_*` through `11_*`.
- ROI ablation: `paper_artifacts/figures/12_roi_ablation.png`.

## Claims to update

- Change “DL preliminary” to “final manifest-driven, inferred study-like group protocol; research candidate only.”
- State that EfficientNet-B0 full image selection and ROI rejection are validation-first.
- State that Logistic Regression selection is development OOF-first.
- State that ML and DL results are separate studies, not a cross-dataset competition.
- State that multimodal fusion is a software demonstration only, not a validated result.

## Claims to remove

- Remove metrics or figures from legacy leakage-affected CBIS folder splits.
- Remove any claim of verified patient-level CBIS splitting.
- Remove causal/clinical wording for SHAP or Grad-CAM.
- Remove any implication that the current models are clinically deployable or that multimodal fusion has been validated.

## Text to preserve

- Research and educational prototype warning.
- Dataset provenance and reproducibility framing, updated to cite the final manifest/snapshot.
- Clear separation between product demonstration behavior and scientific claims.
