# 🎗️ Breast Cancer Prediction using AI
## Dự đoán ung thư vú sử dụng Machine Learning và Deep Learning

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Giới thiệu

Đề tài nghiên cứu khoa học ứng dụng **Machine Learning** và **Deep Learning** để dự đoán ung thư vú, với trọng tâm vào:

- ✅ **Độ chính xác cao** trong chẩn đoán
- ✅ **Tính giải thích được (Explainable AI)** - SHAP & Grad-CAM
- ✅ **Đánh giá chuẩn y khoa** - Sensitivity, Specificity, ROC-AUC
- ✅ **So sánh đa mô hình** - ML cổ điển vs Deep Learning

---

## 🎯 Mục tiêu nghiên cứu

1. **Hybrid Study**: So sánh hiệu suất giữa ML truyền thống và Deep Learning
2. **Clinical Validation**: Đánh giá theo tiêu chuẩn y khoa
3. **Explainable AI**: Giải thích quyết định của mô hình cho bác sĩ
4. **Deployment Ready**: API production-ready với Docker & ONNX

---

## 📊 Datasets

### 1. Wisconsin Diagnostic Breast Cancer (WDBC)
- **Loại**: Dữ liệu số (30 đặc trưng)
- **Mẫu**: 569 bệnh nhân
- **Mục đích**: So sánh các thuật toán ML cổ điển

### 2. CBIS-DDSM (Curated Breast Imaging Subset of DDSM)
- **Loại**: Hình ảnh X-quang tuyến vú (Mammography)
- **Mẫu**: 2,620+ hình ảnh
- **Mục đích**: Deep Learning với Transfer Learning

---

## 🧠 Models & Techniques

### Machine Learning (Wisconsin Dataset)
- Logistic Regression (Baseline y khoa)
- Random Forest
- XGBoost
- **XAI**: SHAP Values

### Deep Learning (CBIS-DDSM Dataset)
- ResNet50 (Transfer Learning)
- EfficientNet-B0
- **XAI**: Grad-CAM Heatmaps

### Key Techniques
- ⚖️ **Imbalanced Data Handling**: SMOTE, Focal Loss
- 🔒 **Data Leakage Prevention**: Patient-wise splitting
- 📈 **Clinical Metrics**: Sensitivity, Specificity, ROC-AUC, PR Curve

---

## 📁 Project Structure

```
breast-cancer-ai/
│
├── data/
│   ├── raw/                    # Dataset gốc
│   └── processed/              # Dữ liệu đã xử lý
│
├── notebooks/                  # Jupyter notebooks nghiên cứu
│   ├── 01_wisconsin_eda.ipynb
│   ├── 02_wisconsin_preprocessing.ipynb
│   ├── 03_wisconsin_train_models.ipynb
│   ├── 04_wisconsin_evaluation_shap.ipynb
│   ├── 05_cbis_prepare_images.ipynb
│   ├── 06_cbis_train_resnet.ipynb
│   └── 07_cbis_gradcam.ipynb
│
├── src/
│   ├── data_processing/        # Xử lý dữ liệu
│   ├── models/                 # Định nghĩa mô hình
│   ├── evaluation/             # Đánh giá mô hình
│   ├── explainability/         # SHAP, Grad-CAM
│   └── utils/                  # Utilities
│
├── models/                     # Mô hình đã train
│
├── experiments/
│   └── results/                # Biểu đồ, kết quả
│
├── backend/                    # FastAPI
│   └── app/
│
├── frontend/                   # Web UI (React/NextJS)
│
└── requirements.txt
```

---

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/breast-cancer-ai.git
cd breast-cancer-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 📖 Usage

### 1. Data Preparation
```bash
jupyter notebook notebooks/01_wisconsin_eda.ipynb
```

### 2. Train Models
```bash
# Wisconsin ML Models
jupyter notebook notebooks/03_wisconsin_train_models.ipynb

# CBIS-DDSM Deep Learning
jupyter notebook notebooks/06_cbis_train_resnet.ipynb
```

### 3. Run API Server
```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Docker Deployment
```bash
docker build -t breast-cancer-ai .
docker run -p 8000:8000 breast-cancer-ai
```

---

## 📊 Results Preview

### Comparative Study

| Model               | Dataset   | ROC-AUC | Sensitivity | Specificity |
|---------------------|-----------|---------|-------------|-------------|
| Logistic Regression | Wisconsin | TBD     | TBD         | TBD         |
| Random Forest       | Wisconsin | TBD     | TBD         | TBD         |
| XGBoost             | Wisconsin | TBD     | TBD         | TBD         |
| ResNet50            | CBIS-DDSM | TBD     | TBD         | TBD         |
| EfficientNet-B0     | CBIS-DDSM | TBD     | TBD         | TBD         |

*(Kết quả sẽ được cập nhật sau khi training)*

---

## 🔬 Key Features for Scientific Research

### 1. ⚖️ Imbalanced Data Handling
- SMOTE cho dữ liệu số
- Class weighting & Focal Loss cho ảnh

### 2. 🔍 Explainable AI (XAI)
- **SHAP**: Feature importance cho ML models
- **Grad-CAM**: Vùng ảnh ảnh hưởng đến quyết định

### 3. 🏥 Clinical Evaluation
- ROC-AUC Curve
- Precision-Recall Curve
- Confusion Matrix với ngưỡng tối ưu
- Sensitivity (True Positive Rate)
- Specificity (True Negative Rate)

### 4. 🔒 Data Leakage Prevention
- Patient-wise train/val/test split
- Stratified splitting để giữ cân bằng class

---

## 🛠️ Tech Stack

| Category      | Technologies                      |
|---------------|-----------------------------------|
| ML            | Scikit-learn, XGBoost             |
| DL            | PyTorch, TensorFlow               |
| XAI           | SHAP, Grad-CAM                    |
| Imbalance     | SMOTE, Focal Loss                 |
| Backend       | FastAPI, Uvicorn                  |
| Deployment    | Docker, ONNX                      |
| Visualization | Matplotlib, Seaborn, Plotly       |

---

## 📚 Research Methodology

### Phase 1: Literature Review
- Các nghiên cứu hiện tại về AI trong chẩn đoán ung thư vú
- Baseline methods trong y khoa

### Phase 2: Data Collection & Preprocessing
- Wisconsin WDBC từ UCI ML Repository
- CBIS-DDSM từ TCIA
- Preprocessing chuẩn y tế

### Phase 3: Model Development
- ML: Traditional algorithms
- DL: Transfer Learning với pretrained models

### Phase 4: Evaluation & Comparison
- Clinical metrics
- Comparative analysis
- Statistical significance testing

### Phase 5: Explainability
- SHAP values
- Grad-CAM visualization

### Phase 6: Deployment
- REST API
- Docker containerization
- ONNX optimization

---

## ⚠️ Ethical Considerations

- Dữ liệu y tế được sử dụng chỉ cho mục đích nghiên cứu
- Tuân thủ HIPAA và các quy định về quyền riêng tư
- Mô hình phục vụ hỗ trợ bác sĩ, không thay thế chẩn đoán y khoa

---

## 🎓 Citation

Nếu bạn sử dụng công trình này trong nghiên cứu, vui lòng trích dẫn:

```bibtex
@misc{breast-cancer-ai-2026,
  author = {Giang Nguyen Huy},
  title = {Breast Cancer Prediction using Machine Learning and Deep Learning with Explainable AI},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/yourusername/breast-cancer-ai}
}
```

---

## 📝 Future Work

- [ ] Thu thập dữ liệu từ bệnh viện Việt Nam
- [ ] Mở rộng sang các loại ung thư khác
- [ ] Tích hợp với hệ thống PACS y tế
- [ ] Mobile app (iOS/Android)
- [ ] Real-time inference optimization

---

## 👨‍🔬 Author

**Giang Nguyen Huy**
- Đề tài: Dự đoán ung thư vú sử dụng AI
- Email: your.email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Wisconsin Diagnostic Breast Cancer Database (UCI ML Repository)
- CBIS-DDSM dataset (The Cancer Imaging Archive)
- PyTorch & TensorFlow communities
- SHAP & Grad-CAM libraries

---

**⚡ Status**: 🚧 Under Active Development

*"Đề tài không chỉ dừng ở việc dự đoán, mà còn tập trung vào tính giải thích của AI trong môi trường y tế, đảm bảo mô hình có thể được bác sĩ tin tưởng sử dụng."*
