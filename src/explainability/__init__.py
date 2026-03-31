"""
Explainability utilities package
"""
from .shap_explainer import SHAPExplainer, compare_shap_across_models

__all__ = ['SHAPExplainer', 'compare_shap_across_models']
