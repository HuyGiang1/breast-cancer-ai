"""
Data loading and preprocessing utilities
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def load_wisconsin_data(data_path: Path) -> pd.DataFrame:
    """
    Load Wisconsin Breast Cancer dataset
    
    Args:
        data_path: Path to the CSV file
        
    Returns:
        DataFrame with the loaded data
    """
    # Check if file exists
    if not data_path.exists():
        print(f"⚠️  Data file not found at {data_path}")
        print("📥 Downloading Wisconsin dataset...")
        download_wisconsin_data(data_path)
    
    df = pd.read_csv(data_path)
    print(f"✅ Loaded Wisconsin dataset: {df.shape[0]} samples, {df.shape[1]} features")
    return df


def download_wisconsin_data(save_path: Path):
    """
    Download Wisconsin Breast Cancer dataset from sklearn
    
    Args:
        save_path: Path to save the CSV file
    """
    from sklearn.datasets import load_breast_cancer
    
    # Load from sklearn
    data = load_breast_cancer()
    
    # Create DataFrame
    df = pd.DataFrame(data.data, columns=data.feature_names)
    df['target'] = data.target
    df['diagnosis'] = df['target'].map({0: 'M', 1: 'B'})  # M=Malignant, B=Benign
    
    # Save to CSV
    save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"✅ Downloaded and saved to: {save_path}")


def preprocess_wisconsin_data(
    df: pd.DataFrame,
    target_col: str = 'target',
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
    apply_smote: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Preprocess Wisconsin dataset with proper train/val/test splitting
    
    Args:
        df: Input DataFrame
        target_col: Name of target column
        test_size: Proportion of test set
        val_size: Proportion of validation set (from training data)
        random_state: Random seed
        apply_smote: Whether to apply SMOTE for handling imbalance
        
    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    # Separate features and target
    X = df.drop(columns=[target_col, 'diagnosis'], errors='ignore')
    y = df[target_col]
    
    # Convert diagnosis to binary if needed (M=1=Malignant, B=0=Benign)
    if y.dtype == 'object':
        y = (y == 'M').astype(int)
    
    print(f"📊 Class distribution:")
    print(f"   Benign (0): {(y == 0).sum()} ({(y == 0).sum()/len(y)*100:.1f}%)")
    print(f"   Malignant (1): {(y == 1).sum()} ({(y == 1).sum()/len(y)*100:.1f}%)")
    
    # First split: train+val vs test (stratified)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Second split: train vs val (stratified)
    val_size_adjusted = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size_adjusted, 
        random_state=random_state, stratify=y_temp
    )
    
    print(f"\n📂 Data split:")
    print(f"   Train: {X_train.shape[0]} samples")
    print(f"   Val:   {X_val.shape[0]} samples")
    print(f"   Test:  {X_test.shape[0]} samples")
    
    # Standardize features (fit on train only!)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Apply SMOTE to training data only (to handle imbalance)
    if apply_smote:
        print("\n⚖️  Applying SMOTE to training data...")
        smote = SMOTE(random_state=random_state)
        X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
        print(f"   After SMOTE - Train: {X_train_scaled.shape[0]} samples")
        print(f"   Benign: {(y_train == 0).sum()}, Malignant: {(y_train == 1).sum()}")
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test


def get_feature_names(df: pd.DataFrame, target_col: str = 'target') -> list:
    """
    Get feature names from DataFrame
    
    Args:
        df: Input DataFrame
        target_col: Name of target column to exclude
        
    Returns:
        List of feature names
    """
    return [col for col in df.columns if col not in [target_col, 'diagnosis']]
