#!/usr/bin/env python3
"""Build paper-ready tables, figures, and a manifest from frozen final artifacts."""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
PAPER = ROOT / "paper_artifacts"
TABLES = PAPER / "tables"
FIGURES = PAPER / "figures"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def copy_figure(target: str, source: str, phase: str, artifacts: list[dict]) -> None:
    destination = FIGURES / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / source, destination)
    artifacts.append({"file": str(destination.relative_to(ROOT)), "source": source, "generated_by": "scripts/generate_paper_artifacts.py (reproducible copy)", "research_phase": phase, "final": True})


def compose_roi_figure(target: str, sources: list[str], artifacts: list[dict]) -> None:
    images = [Image.open(ROOT / source).convert("RGB") for source in sources]
    try:
        height = max(image.height for image in images)
        resized = [image.resize((round(image.width * height / image.height), height), Image.Resampling.LANCZOS) for image in images]
        canvas = Image.new("RGB", (sum(image.width for image in resized), height), "white")
        offset = 0
        for image in resized:
            canvas.paste(image, (offset, 0)); offset += image.width
        destination = FIGURES / target; destination.parent.mkdir(parents=True, exist_ok=True); canvas.save(destination)
    finally:
        for image in images: image.close()
    artifacts.append({"file": str((FIGURES / target).relative_to(ROOT)), "source": sources, "generated_by": "scripts/generate_paper_artifacts.py (side-by-side composition of frozen final figures)", "research_phase": "DL-04 ROI ablation", "final": True})


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict] = []
    stats = read_json(FINAL / "dataset_statistics.json")
    ml_stats = read_json(FINAL / "ml_dataset_statistics.json")
    verification = read_json(FINAL / "dataset_verification.json")
    dataset_rows = [
        {"Study": "WDBC structured ML", "Measure": "Samples", "Value": ml_stats["total_samples"], "Notes": "sklearn.datasets.load_breast_cancer"},
        {"Study": "WDBC structured ML", "Measure": "Features", "Value": ml_stats["features"], "Notes": "numeric features"},
        {"Study": "WDBC structured ML", "Measure": "Malignant / benign", "Value": f"{ml_stats['malignant_count']} / {ml_stats['benign_count']}", "Notes": "1=malignant; 0=benign"},
        {"Study": "WDBC structured ML", "Measure": "Development / held-out test", "Value": "455 / 114", "Notes": "fixed stratified outer split, seed 42"},
        {"Study": "CBIS-DDSM imaging DL", "Measure": "Full processed images", "Value": stats["cbis_ddsm"]["original_processed_images"], "Notes": "images representation"},
        {"Study": "CBIS-DDSM imaging DL", "Measure": "ROI representations", "Value": stats["cbis_ddsm"]["roi_images"], "Notes": "images_roi representation"},
        {"Study": "CBIS-DDSM imaging DL", "Measure": "Manifest rows", "Value": stats["cbis_ddsm"]["manifest_rows"], "Notes": "two representations; not patients"},
        {"Study": "CBIS-DDSM imaging DL", "Measure": "Study-like groups", "Value": stats["cbis_ddsm"]["group_count"], "Notes": "filename-prefix grouping; not verified patient-level"},
        {"Study": "CBIS-DDSM imaging DL", "Measure": "Group overlap", "Value": "0", "Notes": "train/validation/test pairwise overlap all zero"},
    ]
    write_csv(TABLES / "dataset_statistics.csv", dataset_rows)
    ml_metrics = read_csv(FINAL / "ml_metrics.csv")
    ml_rows = [{"Model": row["model"], "Accuracy": row["accuracy"], "Precision": row["precision"], "Sensitivity": row["sensitivity"], "Specificity": row["specificity"], "F1": row["f1"], "Balanced Accuracy": row["balanced_accuracy"], "ROC-AUC": row["roc_auc"], "PR-AUC": row["pr_auc"], "Brier": row["brier_score"], "TN": row["tn"], "FP": row["fp"], "FN": row["fn"], "TP": row["tp"], "Calibration": row["calibration"], "Frozen Threshold": row["threshold"], "Selection Note": "Primary candidate selected from development OOF evidence" if row["model"] == "Logistic Regression" else "Final-test comparison only"} for row in ml_metrics]
    write_csv(TABLES / "ml_model_comparison.csv", ml_rows)
    dl_metrics = read_csv(FINAL / "dl_metrics.csv")
    dl_rows = [{**row, "Selection Note": "Retained candidate selected validation-first" if row["Model"] == "EfficientNet-B0" else "Final baseline comparison"} for row in dl_metrics]
    write_csv(TABLES / "dl_model_comparison.csv", dl_rows)
    roi_rows = [{**row, "Decision": "ROI-C: reject ROI; validation discrimination and sensitivity decreased"} for row in read_csv(FINAL / "roi_ablation.csv")]
    write_csv(TABLES / "roi_ablation.csv", roi_rows)
    write_csv(TABLES / "ml_calibration.csv", read_csv(FINAL / "ml_calibration_metrics.csv"))
    write_csv(TABLES / "dl_calibration.csv", read_csv(FINAL / "calibration_metrics.csv"))
    write_csv(TABLES / "ml_bootstrap_ci.csv", read_csv(FINAL / "ml_bootstrap_ci.csv"))
    write_csv(TABLES / "dl_bootstrap_ci.csv", read_csv(FINAL / "dl_bootstrap_ci.csv"))
    ml_errors = read_csv(FINAL / "ml_error_analysis.csv")
    ml_error_rows = []
    for model in ("Logistic Regression", "Random Forest", "XGBoost"):
        rows = [row for row in ml_errors if row["model"] == model]
        counts = Counter(row["outcome_type"] for row in rows)
        errors = [row for row in rows if row["outcome_type"] in {"FP", "FN"}]
        ml_error_rows.append({"Model": model, "TP": counts["TP"], "TN": counts["TN"], "FP": counts["FP"], "FN": counts["FN"], "Borderline Errors (<0.10)": sum(float(row["confidence_distance_from_threshold"]) < .10 for row in errors), "High-confidence Errors (>=0.25)": sum(float(row["confidence_distance_from_threshold"]) >= .25 for row in errors)})
    write_csv(TABLES / "ml_error_summary.csv", ml_error_rows)
    dl_error = read_json(FINAL / "dl_error_summary.json")
    write_csv(TABLES / "dl_error_summary.csv", [{"Model": "EfficientNet-B0 full", "TP": dl_error["TP"]["count"], "TN": dl_error["TN"]["count"], "FP": dl_error["FP"]["count"], "FN": dl_error["FN"]["count"], "Threshold": dl_error["threshold"], "Borderline Errors (<0.10)": dl_error["borderline_errors"], "High-confidence Errors (>=0.25)": dl_error["high_confidence_errors"]}])
    shap_top = read_csv(FINAL / "ml_shap_global.csv")[:10]
    gradcam = read_json(FINAL / "gradcam" / "selection.json")
    xai_rows = [{"Study": "WDBC ML", "Method": "SHAP LinearExplainer", "Summary": f"Top feature by mean absolute SHAP: {shap_top[0]['Feature']}", "Limitation": "Log-odds model contribution; non-causal; post-hoc test description"}, {"Study": "CBIS-DDSM DL", "Method": "Grad-CAM", "Summary": f"{len(gradcam['selected_cases'])} deterministic TP/TN/FP/FN examples; layer {gradcam['gradcam_layer']}", "Limitation": "Qualitative attention visualization; not localization or pathology evidence"}]
    write_csv(TABLES / "xai_summary.csv", xai_rows)
    figure_sources = [
        ("01_ml_roc_comparison.png", "experiments/final/figures/ml_roc_comparison.png", "Final WDBC ML evaluation"),
        ("02_ml_pr_comparison.png", "experiments/final/figures/ml_pr_comparison.png", "Final WDBC ML evaluation"),
        ("03_ml_confusion_matrix.png", "experiments/final/figures/ml_confusion_matrices.png", "Final WDBC ML evaluation"),
        ("04_ml_calibration.png", "experiments/final/figures/ml_calibration_comparison.png", "Final WDBC ML evaluation"),
        ("05_ml_shap_global.png", "experiments/final/figures/ml_shap_summary.png", "Final WDBC SHAP/XAI"),
        ("06_dl_roc_comparison.png", "experiments/final/figures/dl_roc_comparison.png", "Final DL baseline evaluation"),
        ("07_dl_pr_comparison.png", "experiments/final/figures/dl_pr_comparison.png", "Final DL baseline evaluation"),
        ("08_dl_confusion_matrix.png", "experiments/final/figures/dl_confusion_matrices.png", "Final DL baseline evaluation"),
        ("09_dl_calibration.png", "experiments/final/figures/efficientnet_calibration_comparison.png", "Final DL reliability analysis"),
        ("10_dl_threshold_tradeoff.png", "experiments/final/figures/efficientnet_threshold_tradeoff.png", "Final DL reliability analysis"),
        ("11_dl_gradcam_examples.png", "experiments/final/figures/efficientnet_gradcam_examples.png", "Final DL Grad-CAM/XAI"),
    ]
    for target, source, phase in figure_sources: copy_figure(target, source, phase, artifacts)
    compose_roi_figure("12_roi_ablation.png", ["experiments/final/figures/efficientnet_full_vs_roi_roc.png", "experiments/final/figures/efficientnet_full_vs_roi_pr.png"], artifacts)
    table_sources = {"dataset_statistics.csv": ["experiments/final/dataset_statistics.json", "experiments/final/ml_dataset_statistics.json"], "ml_model_comparison.csv": ["experiments/final/ml_metrics.csv"], "dl_model_comparison.csv": ["experiments/final/dl_metrics.csv"], "roi_ablation.csv": ["experiments/final/roi_ablation.csv"], "ml_calibration.csv": ["experiments/final/ml_calibration_metrics.csv"], "dl_calibration.csv": ["experiments/final/calibration_metrics.csv"], "ml_bootstrap_ci.csv": ["experiments/final/ml_bootstrap_ci.csv"], "dl_bootstrap_ci.csv": ["experiments/final/dl_bootstrap_ci.csv"], "ml_error_summary.csv": ["experiments/final/ml_error_analysis.csv"], "dl_error_summary.csv": ["experiments/final/dl_error_summary.json"], "xai_summary.csv": ["experiments/final/ml_shap_global.csv", "experiments/final/gradcam/selection.json"]}
    for table, source in table_sources.items(): artifacts.append({"file": str((TABLES / table).relative_to(ROOT)), "source": source, "generated_by": "scripts/generate_paper_artifacts.py", "research_phase": "Final paper artifact consolidation", "final": True})
    snapshot = {"dataset": {"wdbc": ml_stats, "cbis_ddsm": stats["cbis_ddsm"], "cbis_verification": {"status": verification["status"], "group_overlap": {"train_val": verification["train_val_group_overlap"], "train_test": verification["train_test_group_overlap"], "val_test": verification["val_test_group_overlap"]}}}, "ml": {"primary_candidate": "Logistic Regression", "selection": read_json(FINAL / "ml_model_selection.json"), "final_test_metrics": ml_metrics}, "dl": {"retained_candidate": "EfficientNet-B0 full processed image", "final_test_metrics": dl_metrics}, "roi": {"decision": "ROI-C", "comparison": read_csv(FINAL / "roi_ablation.csv")}, "calibration": {"ml": read_csv(FINAL / "ml_calibration_metrics.csv"), "dl": read_csv(FINAL / "calibration_metrics.csv"), "dl_selected": read_json(FINAL / "calibration_selection.json")}, "threshold": {"ml": {row["model"]: row["threshold"] for row in ml_metrics}, "dl": dl_error["threshold"]}, "bootstrap": {"ml": read_csv(FINAL / "ml_bootstrap_ci.csv"), "dl": read_csv(FINAL / "dl_bootstrap_ci.csv")}, "xai": {"ml": {"method": "SHAP LinearExplainer", "top_features": shap_top}, "dl": {"method": "Grad-CAM", "selection": gradcam["selection_counts"], "layer": gradcam["gradcam_layer"]}}, "limitations": ["CBIS-DDSM grouping is study-like and not verified patient-level.", "No external validation is available.", "WDBC structured ML and CBIS-DDSM imaging DL are separate datasets/modalities without paired multimodal evaluation.", "Grad-CAM is qualitative and SHAP is non-causal.", "Research / educational prototype; not for clinical diagnosis."]}
    write_json(FINAL / "FINAL_RESULTS_SNAPSHOT.json", snapshot)
    artifacts.append({"file": "experiments/final/FINAL_RESULTS_SNAPSHOT.json", "source": table_sources | {"snapshot": "frozen experiments/final CSV/JSON"}, "generated_by": "scripts/generate_paper_artifacts.py", "research_phase": "Final paper artifact consolidation", "final": True})
    write_json(PAPER / "MANIFEST.json", {"schema_version": 1, "generator": "scripts/generate_paper_artifacts.py", "artifacts": artifacts})
    print(json.dumps({"tables": len(table_sources), "figures": 12, "snapshot": str(FINAL / "FINAL_RESULTS_SNAPSHOT.json"), "manifest": str(PAPER / "MANIFEST.json")}, indent=2))


if __name__ == "__main__":
    main()
