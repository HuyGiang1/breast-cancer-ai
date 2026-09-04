# Legacy Research Artifacts

The artifacts below are preserved for traceability, but they predate the final manifest-driven CBIS-DDSM methodology. They must not be reported as final DL evidence.

| Artifact | Why legacy | Can be used in final report? |
| --- | --- | --- |
| `models/deep_learning/*.keras` (current project-specific DL weights) | Trained or promoted before the clean study-like group manifest became the source of truth. | NO |
| `models/deep_learning/*_summary.json` and `calibration_profile.json` | Refer to legacy DL checkpoints/probability behavior. | NO |
| `experiments/results/dl_models_comparison.csv`, `cnn_models_comparison.*`, `ml_vs_dl_*` | Contains DL comparisons from the legacy split. | NO for DL/fusion claims |
| `experiments/results/*training*`, `learning_curves.png` | Histories/logs from pre-final DL runs. | NO |
| `experiments/results/*roc*`, `*pr*`, `*confusion*`, `*calibration*`, `bootstrap_*` | Evaluation figures include legacy DL results. | NO for DL results |
| `experiments/results/gradcam_*`, `frontend/results/gradcam_*` | Generated from legacy DL weights or runtime artifacts. | NO |
| `experiments/results/ablation_study.csv`, `phase*.json`, `statistical_*` | Development ablations/comparisons predate the final methodology. | NO where they support DL or multimodal claims |
| `experiments/results/shap_*`, `wisconsin_*`, `feature_*` | Development ML exploration; rerun from final ML protocol before final reporting. | NO as final evidence until regenerated |
| Multimodal endpoint result and `0.4/0.6` fusion | Demo heuristic without paired clinical-image validation. | NO |

Legacy artifacts may be used internally to understand prior work or debug regressions. They are not deleted and must be called **LEGACY / PRELIMINARY / DEVELOPMENT ONLY** whenever referenced.
