"""
Configuration settings for the breast cancer prediction project
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Model directories
MODEL_DIR = PROJECT_ROOT / "models"

# Experiment directories
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"

# Dataset paths
WISCONSIN_DATA_PATH = RAW_DATA_DIR / "wisconsin_breast_cancer.csv"
CBIS_DDSM_DIR = RAW_DATA_DIR / "CBIS-DDSM"

# Model settings
RANDOM_STATE = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.1

# Training settings
BATCH_SIZE = 32
LEARNING_RATE = 0.0001
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10

# Image settings
IMAGE_SIZE = (224, 224)
IMAGE_CHANNELS = 3

# Clinical thresholds
SENSITIVITY_THRESHOLD = 0.95  # Prioritize catching cancer cases
SPECIFICITY_THRESHOLD = 0.80

# Create directories if they don't exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
                  MODEL_DIR, EXPERIMENTS_DIR, RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
