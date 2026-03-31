"""
Utility functions for the project
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import joblib
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def save_model(model: Any, model_name: str, model_dir: Path) -> Path:
    """
    Save a trained model to disk
    
    Args:
        model: Trained model object
        model_name: Name for the saved model
        model_dir: Directory to save the model
        
    Returns:
        Path to saved model
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = model_dir / f"{model_name}_{timestamp}.pkl"
    joblib.dump(model, model_path)
    print(f"✅ Model saved to: {model_path}")
    return model_path


def load_model(model_path: Path) -> Any:
    """
    Load a trained model from disk
    
    Args:
        model_path: Path to the saved model
        
    Returns:
        Loaded model object
    """
    model = joblib.load(model_path)
    print(f"✅ Model loaded from: {model_path}")
    return model


def save_results(results: Dict[str, Any], results_name: str, results_dir: Path) -> Path:
    """
    Save experiment results to JSON
    
    Args:
        results: Dictionary containing results
        results_name: Name for the results file
        results_dir: Directory to save results
        
    Returns:
        Path to saved results
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = results_dir / f"{results_name}_{timestamp}.json"
    
    # Convert numpy types to Python types for JSON serialization
    results_json = {}
    for key, value in results.items():
        if isinstance(value, np.integer):
            results_json[key] = int(value)
        elif isinstance(value, np.floating):
            results_json[key] = float(value)
        elif isinstance(value, np.ndarray):
            results_json[key] = value.tolist()
        else:
            results_json[key] = value
    
    with open(results_path, 'w') as f:
        json.dump(results_json, f, indent=4)
    
    print(f"✅ Results saved to: {results_path}")
    return results_path


def save_figure(fig: plt.Figure, fig_name: str, results_dir: Path, 
                dpi: int = 300, bbox_inches: str = 'tight') -> Path:
    """
    Save a matplotlib figure
    
    Args:
        fig: Matplotlib figure object
        fig_name: Name for the saved figure
        results_dir: Directory to save figure
        dpi: Resolution of saved figure
        bbox_inches: Bounding box setting
        
    Returns:
        Path to saved figure
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    fig_path = results_dir / f"{fig_name}.png"
    fig.savefig(fig_path, dpi=dpi, bbox_inches=bbox_inches)
    print(f"✅ Figure saved to: {fig_path}")
    return fig_path


def print_section_header(title: str, width: int = 80, char: str = "="):
    """
    Print a formatted section header
    
    Args:
        title: Section title
        width: Width of the header
        char: Character to use for the border
    """
    print("\n" + char * width)
    print(f"{title:^{width}}")
    print(char * width + "\n")


def print_metrics_table(metrics: Dict[str, float], title: str = "Metrics"):
    """
    Print metrics in a formatted table
    
    Args:
        metrics: Dictionary of metric names and values
        title: Table title
    """
    print(f"\n📊 {title}")
    print("-" * 50)
    for metric_name, value in metrics.items():
        if isinstance(value, float):
            print(f"{metric_name:.<40} {value:.4f}")
        else:
            print(f"{metric_name:.<40} {value}")
    print("-" * 50 + "\n")


def create_comparison_table(results_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Create a comparison table from multiple model results
    
    Args:
        results_dict: Dictionary with model names as keys and metric dicts as values
        
    Returns:
        DataFrame with comparison results
    """
    df = pd.DataFrame(results_dict).T
    df = df.round(4)
    return df


def set_seed(seed: int = 42):
    """
    Set random seed for reproducibility
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    
    print(f"🎲 Random seed set to: {seed}")
