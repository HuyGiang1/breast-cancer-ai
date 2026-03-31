"""
Clinical evaluation metrics for breast cancer prediction
Following medical standards with emphasis on Sensitivity
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, 
    confusion_matrix, classification_report, average_precision_score
)
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def calculate_clinical_metrics(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    y_pred_proba: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive clinical metrics for breast cancer prediction
    
    Key metrics:
    - Sensitivity (Recall): True Positive Rate - MOST IMPORTANT in cancer detection
    - Specificity: True Negative Rate
    - PPV (Precision): Positive Predictive Value
    - NPV: Negative Predictive Value
    - ROC-AUC: Area Under ROC Curve
    - PR-AUC: Area Under Precision-Recall Curve
    
    Args:
        y_true: True labels (0=Benign, 1=Malignant)
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities (optional, for AUC metrics)
        
    Returns:
        Dictionary of metrics
    """
    # Basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred)  # Sensitivity
    f1 = f1_score(y_true, y_pred)
    
    # Confusion matrix for Specificity and NPV
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Clinical metrics
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0  # Same as recall
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0  # Same as precision
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    metrics = {
        'accuracy': accuracy,
        'sensitivity': sensitivity,  # ⭐ Most important for cancer
        'specificity': specificity,
        'ppv': ppv,  # Precision
        'npv': npv,
        'f1_score': f1,
    }
    
    # AUC metrics (if probabilities provided)
    if y_pred_proba is not None:
        roc_auc = roc_auc_score(y_true, y_pred_proba)
        pr_auc = average_precision_score(y_true, y_pred_proba)
        metrics['roc_auc'] = roc_auc
        metrics['pr_auc'] = pr_auc
    
    return metrics


def find_optimal_threshold(
    y_true: np.ndarray, 
    y_pred_proba: np.ndarray,
    target_sensitivity: float = 0.95
) -> Tuple[float, Dict[str, float]]:
    """
    Find optimal threshold that prioritizes sensitivity (catching cancer cases)
    
    In cancer detection, we prioritize Sensitivity over Specificity
    (Better to have false positives than miss cancer cases)
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        target_sensitivity: Target sensitivity level (default 0.95 = 95%)
        
    Returns:
        Tuple of (optimal_threshold, metrics_at_threshold)
    """
    # Get ROC curve
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    
    # Find threshold that achieves target sensitivity
    sensitivity_mask = tpr >= target_sensitivity
    
    if sensitivity_mask.any():
        # Choose threshold with highest specificity among those meeting sensitivity target
        valid_indices = np.where(sensitivity_mask)[0]
        specificities = 1 - fpr[valid_indices]
        best_idx = valid_indices[np.argmax(specificities)]
        optimal_threshold = thresholds[best_idx]
    else:
        # If target not achievable, use Youden's J statistic
        j_scores = tpr - fpr
        best_idx = np.argmax(j_scores)
        optimal_threshold = thresholds[best_idx]
        print(f"⚠️  Target sensitivity {target_sensitivity:.2f} not achievable")
    
    # Calculate metrics at optimal threshold
    y_pred_optimal = (y_pred_proba >= optimal_threshold).astype(int)
    metrics = calculate_clinical_metrics(y_true, y_pred_optimal, y_pred_proba)
    
    return optimal_threshold, metrics


def plot_confusion_matrix(
    y_true: np.ndarray, 
    y_pred: np.ndarray,
    class_names: list = ['Benign', 'Malignant'],
    title: str = 'Confusion Matrix',
    figsize: Tuple[int, int] = (8, 6)
) -> plt.Figure:
    """
    Plot confusion matrix with clinical labels
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: Names of classes
        title: Plot title
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    cm = confusion_matrix(y_true, y_pred)
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Count'}, ax=ax)
    
    ax.set_ylabel('True Label', fontsize=12)
    ax.set_xlabel('Predicted Label', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add clinical annotations
    tn, fp, fn, tp = cm.ravel()
    ax.text(1.5, -0.3, f'TN={tn}  FP={fp}\nFN={fn}  TP={tp}', 
            ha='left', va='top', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    return fig


def plot_roc_curve(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    model_name: str = 'Model',
    figsize: Tuple[int, int] = (8, 6)
) -> plt.Figure:
    """
    Plot ROC curve with AUC score
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        model_name: Name of the model
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    roc_auc = roc_auc_score(y_true, y_pred_proba)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(fpr, tpr, color='darkorange', lw=2, 
            label=f'{model_name} (AUC = {roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
            label='Random Classifier')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=12)
    ax.set_ylabel('True Positive Rate (Sensitivity)', fontsize=12)
    ax.set_title(f'ROC Curve - {model_name}', fontsize=14, fontweight='bold')
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_precision_recall_curve(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    model_name: str = 'Model',
    figsize: Tuple[int, int] = (8, 6)
) -> plt.Figure:
    """
    Plot Precision-Recall curve with AP score
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        model_name: Name of the model
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(recall, precision, color='darkgreen', lw=2,
            label=f'{model_name} (AP = {pr_auc:.3f})')
    
    # Baseline
    baseline = (y_true == 1).sum() / len(y_true)
    ax.plot([0, 1], [baseline, baseline], color='navy', lw=2, 
            linestyle='--', label=f'Baseline ({baseline:.3f})')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Recall (Sensitivity)', fontsize=12)
    ax.set_ylabel('Precision (PPV)', fontsize=12)
    ax.set_title(f'Precision-Recall Curve - {model_name}', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc="lower left", fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    return fig


def print_clinical_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray] = None,
    model_name: str = 'Model'
):
    """
    Print comprehensive clinical evaluation report
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities
        model_name: Name of the model
    """
    print("\n" + "="*80)
    print(f"CLINICAL EVALUATION REPORT - {model_name}".center(80))
    print("="*80 + "\n")
    
    # Calculate metrics
    metrics = calculate_clinical_metrics(y_true, y_pred, y_pred_proba)
    
    print("📊 PERFORMANCE METRICS")
    print("-"*80)
    print(f"{'Accuracy':<30} {metrics['accuracy']:>10.4f}")
    print(f"{'Sensitivity (Recall) ⭐':<30} {metrics['sensitivity']:>10.4f}")
    print(f"{'Specificity':<30} {metrics['specificity']:>10.4f}")
    print(f"{'PPV (Precision)':<30} {metrics['ppv']:>10.4f}")
    print(f"{'NPV':<30} {metrics['npv']:>10.4f}")
    print(f"{'F1-Score':<30} {metrics['f1_score']:>10.4f}")
    
    if 'roc_auc' in metrics:
        print(f"{'ROC-AUC':<30} {metrics['roc_auc']:>10.4f}")
    if 'pr_auc' in metrics:
        print(f"{'PR-AUC':<30} {metrics['pr_auc']:>10.4f}")
    
    print("-"*80)
    
    # Confusion matrix details
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    print(f"\n📋 CONFUSION MATRIX")
    print("-"*80)
    print(f"{'True Negatives (TN)':<30} {tn:>10d}")
    print(f"{'False Positives (FP)':<30} {fp:>10d}")
    print(f"{'False Negatives (FN)':<30} {fn:>10d}  ⚠️  Missed cancer cases")
    print(f"{'True Positives (TP)':<30} {tp:>10d}  ✅ Correctly detected")
    print("-"*80)
    
    # Clinical interpretation
    print(f"\n🏥 CLINICAL INTERPRETATION")
    print("-"*80)
    
    if metrics['sensitivity'] >= 0.95:
        print("✅ EXCELLENT: Sensitivity ≥95% - Very few cancer cases missed")
    elif metrics['sensitivity'] >= 0.90:
        print("✅ GOOD: Sensitivity ≥90% - Acceptable for screening")
    elif metrics['sensitivity'] >= 0.80:
        print("⚠️  MODERATE: Sensitivity ≥80% - Consider improvement")
    else:
        print("❌ LOW: Sensitivity <80% - Not suitable for clinical use")
    
    if metrics['specificity'] >= 0.90:
        print("✅ EXCELLENT: Specificity ≥90% - Few false alarms")
    elif metrics['specificity'] >= 0.80:
        print("✅ GOOD: Specificity ≥80% - Acceptable false positive rate")
    else:
        print("⚠️  MODERATE: Specificity <80% - Many false positives")
    
    print("-"*80)
    print(f"\n💡 NOTE: In cancer detection, Sensitivity is prioritized over Specificity")
    print(f"   (Better to have false positives than miss cancer cases)")
    print("="*80 + "\n")
