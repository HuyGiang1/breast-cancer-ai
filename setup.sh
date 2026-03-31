#!/bin/bash

# Breast Cancer AI Research - Quick Setup Script
# Author: Giang Nguyen Huy

echo "🎗️  Breast Cancer AI Research - Setup"
echo "======================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
echo "   Python version: $python_version"

if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo ""
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

echo ""
echo "📥 Installing dependencies (this may take 5-10 minutes)..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "   ✅ All dependencies installed successfully!"
else
    echo "   ❌ Error installing dependencies. Please check requirements.txt"
    exit 1
fi

echo ""
echo "🧪 Testing imports..."
python3 << EOF
import numpy as np
import pandas as pd
import sklearn
import xgboost
import shap
import torch
import matplotlib

print("   ✅ NumPy:", np.__version__)
print("   ✅ Pandas:", pd.__version__)
print("   ✅ Scikit-learn:", sklearn.__version__)
print("   ✅ XGBoost:", xgboost.__version__)
print("   ✅ SHAP:", shap.__version__)
print("   ✅ PyTorch:", torch.__version__)
print("   ✅ Matplotlib:", matplotlib.__version__)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "======================================"
    echo "🚀 Next Steps:"
    echo "======================================"
    echo ""
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Launch Jupyter Notebook:"
    echo "   jupyter notebook notebooks/"
    echo ""
    echo "3. Start with: 01_wisconsin_eda.ipynb"
    echo ""
    echo "4. Read QUICKSTART.md for detailed guide"
    echo ""
    echo "======================================"
    echo "📚 Documentation:"
    echo "======================================"
    echo ""
    echo "- README.md          - Project overview"
    echo "- QUICKSTART.md      - Quick start guide"
    echo "- PROJECT_STATUS.md  - Current status & roadmap"
    echo ""
    echo "Good luck with your research! 🎗️✨"
else
    echo ""
    echo "❌ Setup incomplete. Please check error messages above."
    exit 1
fi
