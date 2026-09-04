#!/usr/bin/env python3
"""Calibration, threshold, error and uncertainty analysis for frozen DL-03."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, brier_score_loss,
                             log_loss, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUN = FINAL / "runs" / "efficientnet_b0_full"
SEED = 42


def load_predictions(name: str):
    with (RUN / f"{name}_predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return np.array([int(r["label"]) for r in rows]), np.array([float(r["malignant_probability"]) for r in rows])


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1); result = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if mask.any(): result += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return float(result)


def reliability_metrics(y, p):
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    regression = LogisticRegression(C=1e6, solver="lbfgs").fit(logits, y)
    return {"brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, clipped)), "ece_10bin": ece(y, p),
            "calibration_intercept": float(regression.intercept_[0]), "calibration_slope": float(regression.coef_[0][0])}


def platt_fit(x, y):
    model = LogisticRegression(C=1e6, solver="lbfgs").fit(x.reshape(-1, 1), y)
    return lambda values: model.predict_proba(values.reshape(-1, 1))[:, 1]


def isotonic_fit(x, y):
    model = IsotonicRegression(out_of_bounds="clip").fit(x, y)
    return model.predict


def oof_predictions(y, p, factory):
    output = np.zeros_like(p); cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for train, holdout in cv.split(p, y): output[holdout] = factory(p[train], y[train])(p[holdout])
    return output


def operating_metrics(y, p, threshold):
    pred = (p >= threshold).astype(int); tn = int(((y == 0) & (pred == 0)).sum()); fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum()); tp = int(((y == 1) & (pred == 1)).sum())
    return {"threshold": float(threshold), "sensitivity": float(recall_score(y, pred, zero_division=0)), "specificity": float(tn/(tn+fp)),
            "precision": float(precision_score(y, pred, zero_division=0)), "f1": float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 0.0,
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)), "fn": fn, "fp": fp, "tn": tn, "tp": tp}


def main():
    figures = FINAL / "figures"; figures.mkdir(exist_ok=True)
    y_val, p_val = load_predictions("validation"); y_test, p_test = load_predictions("test")
    methods = {"Raw": (p_val, p_test), "Platt": (oof_predictions(y_val, p_val, platt_fit), platt_fit(p_val, y_val)(p_test)),
               "Isotonic": (oof_predictions(y_val, p_val, isotonic_fit), isotonic_fit(p_val, y_val)(p_test))}
    with (FINAL / "dl_calibration_raw.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Split", "Brier", "LogLoss", "ECE_10bin", "CalibrationIntercept", "CalibrationSlope"]); writer.writeheader()
        for split, y, p in (("Validation", y_val, p_val), ("Test", y_test, p_test)):
            m = reliability_metrics(y, p); writer.writerow({"Split": split, "Brier": m["brier"], "LogLoss": m["log_loss"], "ECE_10bin": m["ece_10bin"], "CalibrationIntercept": m["calibration_intercept"], "CalibrationSlope": m["calibration_slope"]})
    rows = []
    for name, (pv, pt) in methods.items():
        vm, tm = reliability_metrics(y_val, pv), reliability_metrics(y_test, pt)
        rows.append({"Method": name, "Validation_Brier": vm["brier"], "Validation_LogLoss": vm["log_loss"], "Validation_ECE_10bin": vm["ece_10bin"], "Test_Brier": tm["brier"], "Test_LogLoss": tm["log_loss"], "Test_ECE_10bin": tm["ece_10bin"]})
    with (FINAL / "calibration_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    selected = min(rows, key=lambda row: (row["Validation_Brier"], row["Validation_LogLoss"]))["Method"]
    # Raw probabilities remain frozen for threshold/error analysis; selection documents reliability only.
    with (FINAL / "calibration_selection.json").open("w", encoding="utf-8") as handle: json.dump({"selected_method": selected, "selection_split": "validation", "criterion": "minimum OOF validation Brier then log loss", "note": "Calibration does not alter architecture, weights, or the pre-specified raw-probability operating points."}, handle, indent=2)
    plt.figure(figsize=(6.5, 5))
    for split, y, p in (("Validation", y_val, p_val), ("Test", y_test, p_test)):
        observed, predicted = calibration_curve(y, p, n_bins=10, strategy="uniform"); plt.plot(predicted, observed, marker="o", label=split)
    plt.plot([0,1],[0,1],"k--"); plt.xlabel("Mean predicted probability"); plt.ylabel("Observed malignant frequency"); plt.legend(); plt.tight_layout(); plt.savefig(figures/"efficientnet_calibration_raw.png", dpi=160); plt.close()
    plt.figure(figsize=(6.5, 5))
    for name, (p, _) in methods.items():
        observed, predicted = calibration_curve(y_val, p, n_bins=10, strategy="uniform"); plt.plot(predicted, observed, marker="o", label=name)
    plt.plot([0,1],[0,1],"k--"); plt.xlabel("Validation predicted probability"); plt.ylabel("Observed malignant frequency"); plt.legend(); plt.tight_layout(); plt.savefig(figures/"efficientnet_calibration_comparison.png", dpi=160); plt.close()
    thresholds = np.round(np.arange(0.05, 0.951, 0.01), 2); sweep = [operating_metrics(y_val, p_val, t) for t in thresholds]
    balanced = max(sweep, key=lambda row: row["balanced_accuracy"])
    candidates = [row for row in sweep if row["sensitivity"] >= 0.80]
    sensitivity_point = max(candidates, key=lambda row: row["specificity"]) if candidates else None
    with (FINAL / "threshold_analysis.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sweep[0])); writer.writeheader(); writer.writerows(sweep)
    sensitivity_test = operating_metrics(y_test, p_test, sensitivity_point["threshold"]) if sensitivity_point else None
    with (FINAL / "threshold_operating_points.json").open("w", encoding="utf-8") as handle: json.dump({"balanced_validation": balanced, "sensitivity_oriented_validation": sensitivity_point, "sensitivity_oriented_test": sensitivity_test, "sensitivity_constraint": 0.80, "selection_split": "validation"}, handle, indent=2)
    plt.figure(figsize=(7,5)); plt.plot(thresholds,[r["sensitivity"] for r in sweep],label="Sensitivity"); plt.plot(thresholds,[r["specificity"] for r in sweep],label="Specificity"); plt.plot(thresholds,[r["balanced_accuracy"] for r in sweep],label="Balanced accuracy"); plt.axvline(balanced["threshold"],color="k",ls="--",label="Balanced point");
    if sensitivity_point: plt.axvline(sensitivity_point["threshold"],color="tab:red",ls=":",label="Sensitivity-oriented point")
    plt.xlabel("Validation threshold"); plt.legend(); plt.tight_layout(); plt.savefig(figures/"efficientnet_threshold_tradeoff.png",dpi=160); plt.close()
    frozen_threshold = float(json.loads((RUN/"threshold.json").read_text())["threshold"]); test_ops = operating_metrics(y_test,p_test,frozen_threshold)
    error_rows=[]
    for index,(label,probability) in enumerate(zip(y_test,p_test)):
        predicted=int(probability>=frozen_threshold); error_type=("TP" if label else "FP") if predicted else ("FN" if label else "TN")
        error_rows.append({"sample_identifier":f"test_index_{index}","group_identifier":"not_available_in_prediction_export","true_label":int(label),"probability":float(probability),"predicted_label":predicted,"error_type":error_type,"distance_from_threshold":float(abs(probability-frozen_threshold)),"source_representation":"images"})
    with (FINAL/"dl_error_analysis.csv").open("w",newline="",encoding="utf-8") as handle: writer=csv.DictWriter(handle,fieldnames=list(error_rows[0])); writer.writeheader(); writer.writerows(error_rows)
    summary={kind:{"count":sum(r["error_type"]==kind for r in error_rows),"probability_mean":float(np.mean([r["probability"] for r in error_rows if r["error_type"]==kind]))} for kind in ("TP","TN","FP","FN")}; summary.update({"threshold":frozen_threshold,"high_confidence_errors":sum(r["error_type"] in {"FP","FN"} and r["distance_from_threshold"]>=0.25 for r in error_rows),"borderline_errors":sum(r["error_type"] in {"FP","FN"} and r["distance_from_threshold"]<0.10 for r in error_rows),"test_operating_point":test_ops,"group_identifier_limitation":"Prediction export contains indexes but no group IDs; filenames are not used for pathological inference."})
    (FINAL/"dl_error_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    plt.figure(figsize=(7,5));
    for kind,color in (("FP","tab:orange"),("FN","tab:red")): plt.hist([r["probability"] for r in error_rows if r["error_type"]==kind],bins=12,alpha=.65,label=kind,color=color)
    plt.axvline(frozen_threshold,color="k",ls="--"); plt.xlabel("Malignant probability"); plt.ylabel("Count"); plt.legend(); plt.tight_layout(); plt.savefig(figures/"efficientnet_error_probability_distribution.png",dpi=160); plt.close()
    rng=np.random.default_rng(SEED); records=[]; valid={key:0 for key in ("ROC-AUC","PR-AUC","Sensitivity","Specificity","Balanced Accuracy")}; values={key:[] for key in valid}
    for _ in range(2000):
        ix=rng.integers(0,len(y_test),len(y_test)); y,p=y_test[ix],p_test[ix]
        if len(np.unique(y))<2: continue
        ops=operating_metrics(y,p,frozen_threshold); metrics={"ROC-AUC":roc_auc_score(y,p),"PR-AUC":average_precision_score(y,p),"Sensitivity":ops["sensitivity"],"Specificity":ops["specificity"],"Balanced Accuracy":ops["balanced_accuracy"]}
        for key,value in metrics.items(): values[key].append(float(value)); valid[key]+=1
    point={"ROC-AUC":roc_auc_score(y_test,p_test),"PR-AUC":average_precision_score(y_test,p_test),"Sensitivity":test_ops["sensitivity"],"Specificity":test_ops["specificity"],"Balanced Accuracy":test_ops["balanced_accuracy"]}
    for key in values: records.append({"Metric":key,"PointEstimate":point[key],"CI95_Lower":np.quantile(values[key],.025),"CI95_Upper":np.quantile(values[key],.975),"BootstrapIterations":2000,"ValidIterations":valid[key],"Seed":SEED})
    with (FINAL/"dl_bootstrap_ci.csv").open("w",newline="",encoding="utf-8") as handle: writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)

if __name__ == "__main__": main()
