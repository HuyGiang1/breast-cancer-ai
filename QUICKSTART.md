# 🚀 Quick Start Guide - Breast Cancer AI Research

Hướng dẫn nhanh để bắt đầu dự án nghiên cứu.

---

## 📋 Prerequisites

- Python 3.9+
- pip hoặc conda
- Jupyter Notebook
- Git
- ~2GB free disk space (cho datasets)

---

## ⚡ Quick Setup (5 phút)

### 1. Clone & Navigate
```bash
cd /Users/GiangNguyenHuy/Documents/breast-cancer-ai
```

### 2. Create Virtual Environment
```bash
# Sử dụng venv
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Hoặc conda
conda create -n breast-cancer python=3.9
conda activate breast-cancer
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: Cài đặt có thể mất 5-10 phút (nhiều libraries lớn).

### 4. Launch Jupyter
```bash
jupyter notebook notebooks/
```

---

## 🎯 Workflow - Thứ tự thực hiện

### Phase 1: Wisconsin Dataset (ML Models) - **BẮT ĐẦU TỪ ĐÂY**

#### Step 1: EDA (Exploratory Data Analysis)
```bash
# Open in Jupyter
01_wisconsin_eda.ipynb
```
**Thời gian**: ~10-15 phút  
**Output**: 
- Class distribution plots
- Feature correlation matrix
- Box plots, histograms
- EDA insights

#### Step 2: Preprocessing
```bash
02_wisconsin_preprocessing.ipynb
```
**Thời gian**: ~5 phút  
**Output**:
- `wisconsin_processed.pkl` (train/val/test splits)
- Class distribution after SMOTE
- Verification plots

#### Step 3: Train Models
```bash
03_wisconsin_train_models.ipynb
```
**Thời gian**: ~10-20 phút (training 3 models)  
**Output**:
- Trained models: LR, RF, XGBoost
- Confusion matrices
- ROC curves
- Performance comparison table

#### Step 4: SHAP Explainability
```bash
04_wisconsin_evaluation_shap.ipynb
```
**Thời gian**: ~15-20 phút (SHAP computation)  
**Output**:
- SHAP summary plots
- Feature importance rankings
- Individual prediction explanations
- Comparison across models

**✅ Sau Phase 1, bạn đã có:**
- 3 ML models trained & evaluated
- Clinical metrics (Sensitivity, Specificity, ROC-AUC)
- SHAP explainability
- Visualizations cho báo cáo

---

### Phase 2: CBIS-DDSM Dataset (Deep Learning) - **COMING SOON**

#### Step 5: Image Preprocessing
```bash
05_cbis_prepare_images.ipynb
```

#### Step 6: Train ResNet/EfficientNet
```bash
06_cbis_train_resnet.ipynb
```

#### Step 7: Grad-CAM Explainability
```bash
07_cbis_gradcam.ipynb
```

---

## 📦 Dataset Download

### Wisconsin Dataset (Automatic)
Notebook sẽ tự động download từ scikit-learn khi chạy lần đầu.

### CBIS-DDSM Dataset (Manual - for Deep Learning)
**Option 1**: Download từ TCIA
```bash
# Visit: https://wiki.cancerimagingarchive.net/display/Public/CBIS-DDSM
# Download và extract vào: data/raw/CBIS-DDSM/
```

**Option 2**: Kaggle (easier)
```bash
pip install kaggle
kaggle datasets download -d awsaf49/cbis-ddsm-breast-cancer-image-dataset
unzip cbis-ddsm-breast-cancer-image-dataset.zip -d data/raw/CBIS-DDSM/
```

**Note**: CBIS-DDSM cần cho Phase 2 (Deep Learning). Phase 1 không cần.

---

## 🔍 Troubleshooting

### Issue: Import errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Jupyter kernel not found
```bash
python -m ipykernel install --user --name=breast-cancer
```

### Issue: SHAP visualization không hiển thị
```bash
# Trong notebook, thêm:
import shap
shap.initjs()
```

### Issue: Out of memory khi train
```python
# Giảm batch size hoặc sử dụng subset của data
X_train_subset = X_train[:1000]  # Use smaller subset
```

---

## 📊 Expected Results (Wisconsin)

### Model Performance (Approximate)
| Model               | Accuracy | Sensitivity | Specificity | ROC-AUC |
|---------------------|----------|-------------|-------------|---------|
| Logistic Regression | ~0.96    | ~0.95       | ~0.96       | ~0.98   |
| Random Forest       | ~0.97    | ~0.96       | ~0.97       | ~0.99   |
| XGBoost             | ~0.98    | ~0.97       | ~0.98       | ~0.99   |

**Note**: Kết quả có thể khác nhau do random seed.

### Visualizations Generated
- `wisconsin_class_distribution.png`
- `wisconsin_correlation_matrix.png`
- `wisconsin_confusion_matrices.png`
- `wisconsin_roc_curves_comparison.png`
- `shap_summary_xgboost.png`
- `shap_bar_xgboost.png`
- And more...

Tất cả saved trong: `experiments/results/`

---

## 🧪 Quick Test

Chạy test nhanh để verify setup:

```python
# Tạo file test.py
import numpy as np
import pandas as pd
import sklearn
import xgboost
import shap
import torch

print("✅ All core libraries imported successfully!")
print(f"   NumPy: {np.__version__}")
print(f"   Pandas: {pd.__version__}")
print(f"   Scikit-learn: {sklearn.__version__}")
print(f"   XGBoost: {xgboost.__version__}")
print(f"   SHAP: {shap.__version__}")
print(f"   PyTorch: {torch.__version__}")
```

```bash
python test.py
```

---

## 📝 Research Paper Checklist

Sau khi hoàn thành Phase 1, bạn sẽ có:

### Methods Section:
- [x] Dataset description (Wisconsin WDBC)
- [x] Preprocessing pipeline (SMOTE, scaling)
- [x] Model architectures (LR, RF, XGBoost)
- [x] Evaluation metrics (clinical metrics)
- [x] Train/val/test split strategy

### Results Section:
- [x] Performance comparison table
- [x] Confusion matrices
- [x] ROC & PR curves
- [x] Feature importance (SHAP)

### Figures for Paper:
- [x] Class distribution
- [x] Feature correlation heatmap
- [x] Model comparison (bar charts)
- [x] ROC curves (all models)
- [x] SHAP summary plot
- [x] SHAP comparison across models

---

## 🎓 Tips for Success

### 1. **Chạy tuần tự**
   - Không skip notebooks
   - Mỗi notebook depend on outputs của notebook trước

### 2. **Save thường xuyên**
   - Models được auto-save sau training
   - Figures được auto-save trong RESULTS_DIR

### 3. **Comment code**
   - Thêm notes của bạn vào notebooks
   - Giải thích findings cho báo cáo sau này

### 4. **Check outputs**
   - Verify mỗi output trước khi next step
   - Nếu có errors, check Troubleshooting section

### 5. **Document everything**
   - Screenshot important results
   - Copy metric tables vào báo cáo draft
   - Note down observations

---

## 📞 Next Steps

1. ✅ **Run Phase 1** (Wisconsin ML pipeline)
2. ⏳ **Analyze results** và tạo báo cáo draft
3. ⏳ **Phase 2**: Deep Learning với images
4. ⏳ **Phase 3**: Comparative study
5. ⏳ **Phase 4**: Deployment (API, Docker)

---

## 🎯 Questions?

Check:
- README.md (main documentation)
- Code comments in notebooks
- src/ modules documentation
- GitHub issues (if using version control)

---

**Good luck with your research! 🎗️✨**

> "Đề tài không chỉ dừng ở việc dự đoán, mà còn tập trung vào tính giải thích của AI trong môi trường y tế."
