"""
Machine Learning models for Wisconsin Breast Cancer dataset
"""
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
import numpy as np
from typing import Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')


class WisconsinMLModels:
    """
    Collection of ML models for Wisconsin dataset
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize ML models
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.models = {}
        
    def get_logistic_regression(self, tune: bool = False) -> LogisticRegression:
        """
        Get Logistic Regression model (Baseline)
        
        Args:
            tune: Whether to tune hyperparameters
            
        Returns:
            Trained or configured model
        """
        if tune:
            param_grid = {
                'C': [0.001, 0.01, 0.1, 1, 10, 100],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'saga']
            }
            model = GridSearchCV(
                LogisticRegression(random_state=self.random_state, max_iter=1000),
                param_grid, cv=5, scoring='recall', n_jobs=-1, verbose=0
            )
        else:
            model = LogisticRegression(
                random_state=self.random_state,
                max_iter=1000,
                class_weight='balanced'  # Handle imbalance
            )
        
        return model
    
    def get_random_forest(self, tune: bool = False) -> RandomForestClassifier:
        """
        Get Random Forest model
        
        Args:
            tune: Whether to tune hyperparameters
            
        Returns:
            Trained or configured model
        """
        if tune:
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': ['balanced', 'balanced_subsample']
            }
            model = GridSearchCV(
                RandomForestClassifier(random_state=self.random_state),
                param_grid, cv=5, scoring='recall', n_jobs=-1, verbose=0
            )
        else:
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                random_state=self.random_state,
                class_weight='balanced',
                n_jobs=-1
            )
        
        return model
    
    def get_xgboost(self, tune: bool = False) -> XGBClassifier:
        """
        Get XGBoost model
        
        Args:
            tune: Whether to tune hyperparameters
            
        Returns:
            Trained or configured model
        """
        if tune:
            param_grid = {
                'max_depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'n_estimators': [100, 200, 300],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
                'scale_pos_weight': [1, 2, 3]  # Handle imbalance
            }
            model = GridSearchCV(
                XGBClassifier(
                    random_state=self.random_state, 
                    eval_metric='logloss',
                    enable_categorical=False
                ),
                param_grid, cv=5, scoring='recall', n_jobs=-1, verbose=0
            )
        else:
            model = XGBClassifier(
                max_depth=5,
                learning_rate=0.1,
                n_estimators=200,
                random_state=self.random_state,
                eval_metric='logloss',
                scale_pos_weight=1,  # Can adjust based on class imbalance
                n_jobs=-1,
                enable_categorical=False  # Fix for feature name issues
            )
        
        return model
    
    def train_all_models(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        tune: bool = False
    ) -> Dict[str, Any]:
        """
        Train all ML models
        
        Args:
            X_train: Training features
            y_train: Training labels
            tune: Whether to tune hyperparameters
            
        Returns:
            Dictionary of trained models
        """
        print("\n🚀 Training Machine Learning Models...\n")
        
        # Logistic Regression
        print("📊 Training Logistic Regression (Baseline)...")
        lr_model = self.get_logistic_regression(tune=tune)
        lr_model.fit(X_train, y_train)
        self.models['Logistic Regression'] = lr_model
        print("   ✅ Completed")
        
        # Random Forest
        print("📊 Training Random Forest...")
        rf_model = self.get_random_forest(tune=tune)
        rf_model.fit(X_train, y_train)
        self.models['Random Forest'] = rf_model
        print("   ✅ Completed")
        
        # XGBoost
        print("📊 Training XGBoost...")
        xgb_model = self.get_xgboost(tune=tune)
        xgb_model.fit(X_train, y_train)
        self.models['XGBoost'] = xgb_model
        print("   ✅ Completed")
        
        print("\n✅ All models trained successfully!\n")
        
        return self.models
    
    def get_model(self, model_name: str) -> Any:
        """
        Get a trained model by name
        
        Args:
            model_name: Name of the model
            
        Returns:
            Trained model
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found. Available: {list(self.models.keys())}")
        return self.models[model_name]
