"""
SHAP (SHapley Additive exPlanations) for model explainability
"""
import shap
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import Any, Optional, List
import warnings
warnings.filterwarnings('ignore')


class SHAPExplainer:
    """
    SHAP explainability for Wisconsin ML models
    """
    
    def __init__(self, model: Any, X_background: np.ndarray, feature_names: List[str]):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained model
            X_background: Background data for SHAP (typically training set)
            feature_names: List of feature names
        """
        self.model = model
        self.X_background = X_background
        self.feature_names = feature_names
        
        # Initialize appropriate explainer based on model type
        model_type = type(model).__name__
        print(f"🔍 Initializing SHAP explainer for {model_type}...")
        
        if 'XGB' in model_type or 'RandomForest' in model_type:
            # Tree-based explainer (faster)
            self.explainer = shap.TreeExplainer(model)
        elif 'Logistic' in model_type:
            # Linear explainer
            self.explainer = shap.LinearExplainer(model, X_background)
        else:
            # General explainer (slower but works for any model)
            self.explainer = shap.KernelExplainer(
                model.predict_proba, 
                shap.sample(X_background, 100)
            )
        
        self.shap_values = None
        
    def calculate_shap_values(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate SHAP values for given data
        
        Args:
            X: Input data
            
        Returns:
            SHAP values
        """
        print("📊 Calculating SHAP values...")
        self.shap_values = self.explainer.shap_values(X)
        
        # For binary classification, some explainers return values for both classes
        if isinstance(self.shap_values, list):
            self.shap_values = self.shap_values[1]  # Use positive class
        
        print("   ✅ SHAP values calculated")
        return self.shap_values
    
    def plot_summary(
        self, 
        X: np.ndarray, 
        max_display: int = 20,
        figsize: tuple = (10, 8)
    ) -> plt.Figure:
        """
        Plot SHAP summary plot (beeswarm)
        Shows feature importance and impact direction
        
        Args:
            X: Input data
            max_display: Maximum number of features to display
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        plt.figure(figsize=figsize)
        shap.summary_plot(
            self.shap_values, 
            X, 
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        plt.title("SHAP Summary Plot - Feature Impact on Model Output", 
                  fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_bar(
        self, 
        X: np.ndarray, 
        max_display: int = 20,
        figsize: tuple = (10, 8)
    ) -> plt.Figure:
        """
        Plot SHAP bar plot (mean absolute SHAP values)
        Shows average feature importance
        
        Args:
            X: Input data
            max_display: Maximum number of features to display
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        plt.figure(figsize=figsize)
        shap.summary_plot(
            self.shap_values, 
            X, 
            feature_names=self.feature_names,
            plot_type="bar",
            max_display=max_display,
            show=False
        )
        plt.title("SHAP Feature Importance - Mean Absolute Impact", 
                  fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_waterfall(
        self, 
        X: np.ndarray, 
        sample_idx: int = 0,
        figsize: tuple = (10, 8)
    ) -> plt.Figure:
        """
        Plot SHAP waterfall plot for a single prediction
        Shows how features contribute to specific prediction
        
        Args:
            X: Input data
            sample_idx: Index of sample to explain
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        plt.figure(figsize=figsize)
        
        # Extract values if it's an Explanation object
        shap_vals = self.shap_values
        if hasattr(shap_vals, 'values'):
            shap_vals = shap_vals.values
        
        # Get expected value
        if hasattr(self.explainer, 'expected_value'):
            expected_val = self.explainer.expected_value
            # Handle if it's array-like
            if isinstance(expected_val, (list, np.ndarray)):
                expected_val = expected_val[-1] if len(expected_val) > 1 else expected_val[0]
        else:
            expected_val = 0
        
        # Get sample data
        sample_shap = shap_vals[sample_idx]
        sample_data = X[sample_idx]
        
        # Ensure 1D
        if len(sample_shap.shape) > 1:
            sample_shap = sample_shap.flatten()
        if len(sample_data.shape) > 1:
            sample_data = sample_data.flatten()
        
        # Create explanation object for the sample
        exp = shap.Explanation(
            values=sample_shap,
            base_values=expected_val,
            data=sample_data,
            feature_names=self.feature_names
        )
        
        shap.waterfall_plot(exp, show=False)
        plt.title(f"SHAP Waterfall Plot - Sample {sample_idx}", 
                  fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_force(
        self, 
        X: np.ndarray, 
        sample_idx: int = 0
    ):
        """
        Plot SHAP force plot for a single prediction (interactive HTML)
        
        Args:
            X: Input data
            sample_idx: Index of sample to explain
            
        Returns:
            SHAP force plot object
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        # Extract values if it's an Explanation object
        shap_vals = self.shap_values
        if hasattr(shap_vals, 'values'):
            shap_vals = shap_vals.values
        
        # Get expected value
        expected_value = self.explainer.expected_value
        if isinstance(expected_value, (list, np.ndarray)):
            expected_value = expected_value[-1] if len(expected_value) > 1 else expected_value[0]
        
        # Get sample data
        sample_shap = shap_vals[sample_idx]
        sample_data = X[sample_idx]
        
        # Ensure 1D
        if len(sample_shap.shape) > 1:
            sample_shap = sample_shap.flatten()
        if len(sample_data.shape) > 1:
            sample_data = sample_data.flatten()
        
        return shap.force_plot(
            expected_value,
            sample_shap,
            sample_data,
            feature_names=self.feature_names
        )
    
    def get_feature_importance(self, X: np.ndarray) -> pd.DataFrame:
        """
        Get feature importance based on mean absolute SHAP values
        
        Args:
            X: Input data
            
        Returns:
            DataFrame with feature importance
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        # Extract values if it's an Explanation object
        shap_vals = self.shap_values
        if hasattr(shap_vals, 'values'):
            shap_vals = shap_vals.values
        
        # Ensure it's a numpy array
        shap_vals = np.array(shap_vals)
        
        # Calculate mean absolute SHAP values across samples (axis=0)
        mean_abs_shap = np.abs(shap_vals).mean(axis=0)
        
        # Ensure 1D array and correct length
        while len(mean_abs_shap.shape) > 1:
            mean_abs_shap = mean_abs_shap.flatten()
        
        # Verify length matches feature names
        if len(mean_abs_shap) != len(self.feature_names):
            # Take only first n features if mismatch
            mean_abs_shap = mean_abs_shap[:len(self.feature_names)]
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': mean_abs_shap
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def explain_prediction(
        self, 
        X: np.ndarray, 
        sample_idx: int,
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        Explain a specific prediction
        
        Args:
            X: Input data
            sample_idx: Index of sample to explain
            top_n: Number of top features to show
            
        Returns:
            DataFrame with feature contributions
        """
        if self.shap_values is None:
            self.calculate_shap_values(X)
        
        # Extract values if it's an Explanation object
        shap_vals = self.shap_values
        if hasattr(shap_vals, 'values'):
            shap_vals = shap_vals.values
        
        # Get SHAP values for this sample
        sample_shap = shap_vals[sample_idx]
        
        # Ensure 1D
        if len(sample_shap.shape) > 1:
            sample_shap = sample_shap.flatten()
        
        sample_values = X[sample_idx]
        if len(sample_values.shape) > 1:
            sample_values = sample_values.flatten()
        
        # Create DataFrame
        explanation_df = pd.DataFrame({
            'feature': self.feature_names,
            'feature_value': sample_values,
            'shap_value': sample_shap,
            'abs_shap': np.abs(sample_shap)
        }).sort_values('abs_shap', ascending=False).head(top_n)
        
        return explanation_df


def compare_shap_across_models(
    models_dict: dict,
    X_test: np.ndarray,
    feature_names: List[str],
    top_n: int = 10
) -> pd.DataFrame:
    """
    Compare SHAP feature importance across multiple models
    
    Args:
        models_dict: Dictionary of model_name: model pairs
        X_test: Test data
        feature_names: List of feature names
        top_n: Number of top features to compare
        
    Returns:
        DataFrame with comparison
    """
    importance_dict = {}
    
    for model_name, model in models_dict.items():
        print(f"\n📊 Computing SHAP for {model_name}...")
        explainer = SHAPExplainer(model, X_test[:100], feature_names)
        importance_df = explainer.get_feature_importance(X_test)
        importance_dict[model_name] = importance_df.set_index('feature')['importance']
    
    # Combine into single DataFrame
    comparison_df = pd.DataFrame(importance_dict).head(top_n)
    
    return comparison_df
