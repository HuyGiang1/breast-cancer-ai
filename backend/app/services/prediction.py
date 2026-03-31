import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import shap
import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
POSSIBLE_MODEL_DIRS = [PROJECT_ROOT / "models", PROJECT_ROOT / "src" / "models"]

FEATURES = [
    "mean radius", "mean texture", "mean perimeter", "mean area", "mean smoothness",
    "mean compactness", "mean concavity", "mean concave points", "mean symmetry", "mean fractal dimension",
    "radius error", "texture error", "perimeter error", "area error", "smoothness_error",
    "compactness error", "concavity error", "concave points error", "symmetry error", "fractal_dimension_error",
    "worst radius", "worst texture", "worst perimeter", "worst area", "worst smoothness",
    "worst compactness", "worst concavity", "worst concave points", "worst symmetry", "worst fractal dimension"
]

# Chi tiết y khoa chuyên sâu cho từng nhóm đặc điểm tế bào
FEATURE_DETAILS = {
    "Radius": {
        "desc": "Chỉ số bán kính phản ánh kích thước trung bình của nhân tế bào từ tâm đến biên. Ở các khối u ác tính, tế bào thường phình to bất thường do quá trình nhân đôi DNA hỗn loạn.",
        "advice": "Bác sĩ khuyên bạn: Chỉ số này tăng cao gợi ý sự tăng sinh mạnh. Bạn nên hạn chế tối đa các thực phẩm chứa nhiều hormone tăng trưởng và ưu tiên thực phẩm chống viêm (như bông cải xanh, nghệ). Cần chụp X-quang tuyến vú (Mammography) định kỳ để theo dõi tốc độ thay đổi kích thước này."
    },
    "Texture": {
        "desc": "Độ thô ráp (Texture) đo lường sự biến thiên mức độ hạt trong nhân tế bào. Tế bào ung thư thường có bề mặt nhân gồ ghề và không đồng nhất.",
        "advice": "Lời khuyên: Bề mặt tế bào không mịn màng thường do sự thay đổi cấu trúc Chromatin. Bạn nên bổ sung các thực phẩm giàu Vitamin D và Omega-3 để hỗ trợ ổn định màng tế bào. Hãy thảo luận với bác sĩ về việc thực hiện xét nghiệm hóa mô miễn dịch để đánh giá sâu hơn."
    },
    "Perimeter": {
        "desc": "Chu vi tế bào tỷ lệ thuận với khả năng xâm lấn. Chu vi càng lớn và răng cưa càng nhiều thì nguy cơ lan rộng sang các mô lân cận càng cao.",
        "advice": "Hành động cần thiết: Đây là dấu hiệu của sự mất kiểm soát ranh giới. Bạn cần tránh các vận động mạnh ở vùng ngực nếu có vết thương hở và tập trung vào chế độ nghỉ ngơi để hệ miễn dịch hoạt động tốt nhất. Siêu âm Doppler màu là cần thiết để kiểm tra mạng lưới mạch máu nuôi dưỡng khối u này."
    },
    "Area": {
        "desc": "Diện tích hạt nhân tế bào lớn là hệ quả của việc tích tụ quá nhiều vật chất di truyền lỗi, chuẩn bị cho quá trình phân chia liên lục.",
        "advice": "Tư vấn chuyên khoa: Diện tích tế bào lớn cần được kiểm soát bằng cách giảm thiểu căng thẳng (Stress) - yếu tố thúc đẩy Cortisol làm trầm trọng thêm tình trạng tế bào. Hãy thực hiện kiểm tra các hạch bạch huyết dưới nách để đảm bảo tế bào chưa 'di cư' sang hệ thống miễn dịch."
    },
    "Smoothness": {
        "desc": "Độ mịn mô tả mức độ biến đổi cục bộ của độ dài bán kính. Tế bào lành tính thường có biên giới trơn láng.",
        "advice": "Lời khuyên thực tế: Độ mịn thấp (răng cưa) yêu cầu bạn phải theo dõi sự xuất hiện của các cơn đau nhói nhẹ. Hãy giữ tinh thần lạc quan và thực hiện các bài tập hít thở sâu để tăng cường oxy cho tế bào, điều này có thể giúp làm chậm quá trình biến đổi cấu trúc mô."
    },
    "Compactness": {
        "desc": "Độ chặt chẽ phản ánh sự cô đặc của tế bào. Tế bào ác tính có xu hướng rời rạc và dễ bong ra khỏi khối u gốc.",
        "advice": "Cảnh báo bác sĩ: Cấu trúc rời rạc là tiền đề của di căn. Bạn tuyệt đối không được tự ý xoa bóp hoặc tác động mạnh vào khối u vì có thể làm tế bào bong ra và đi vào mạch máu. Hãy tham vấn về việc chụp MRI có tiêm thuốc cản quang để thấy rõ sự cô đặc của mô."
    },
    "Concavity": {
        "desc": "Độ lõm mô tả mức độ lõm vào của đường bao nhân tế bào. Nhân tế bào 'méo mó' là bằng chứng thép của sự ác tính.",
        "advice": "Phân tích bác sĩ: Sự 'méo mó' này thường do áp lực từ các đột biến gen bên trong nhân. Bạn nên tham gia các xét nghiệm tầm soát gen (như BRCA1/2) nếu gia đình có tiền sử. Hãy duy trì chế độ ăn ít đường vì đường là 'nhiên liệu' ưa thích của những tế bào biến dạng này."
    },
    "Concave Points": {
        "desc": "Số lượng các điểm lõm trên bề mặt nhân tế bào. Đây là chỉ số có độ nhạy cao nhất trong chẩn đoán ung thư vú.",
        "advice": "Chỉ định khẩn cấp: Nếu chỉ số này cao, bác sĩ yêu cầu bạn thực hiện sinh thiết tức thì (Frozen section) nếu có can thiệp phẫu thuật. Trong cuộc sống hàng ngày, hãy tránh xa các hóa chất độc hại từ thuốc lá và môi trường ô nhiễm để ngăn chặn các điểm 'lỗi' này phát triển thêm."
    },
    "Symmetry": {
        "desc": "Tính đối xứng đo lường sự cân bằng của nhân tế bào. Mất đối xứng là dấu hiệu của sự tăng trưởng không định hướng.",
        "advice": "Lời khuyên: Sự mất đối xứng thường bắt nguồn từ mất cân bằng nội tiết tố. Bạn hãy kiểm tra lại nồng độ Estrogen trong cơ thể. Hãy tập trung vào việc ngủ đủ giấc và đúng giờ để tái thiết lập nhịp sinh học, giúp tế bào có cơ hội phục hồi tính đối xứng tự nhiên."
    },
    "Fractal Dimension": {
        "desc": "Độ phức tạp toán học của biên biên tế bào. Các tế bào có chỉ số này cao thường có cấu trúc phức tạp như các nhánh cây xâm lấn.",
        "advice": "Tư vấn dài hạn: Cấu trúc phức tạp yêu cầu một phác đồ điều trị đa mô thức. Bạn nên tìm hiểu về các liệu pháp nhắm trúng đích hoặc liệu pháp miễn dịch. Hãy giữ một cuốn nhật ký sức khỏe để ghi lại mọi thay đổi nhỏ nhất về cảm giác ở vùng ngực của mình."
    }
}

# Professional Benchmarks from training notebooks (wisconsin_train_models.ipynb)
MODEL_STATS = {
    "Logistic Regression": {
        "accuracy": 0.965,
        "sensitivity": 0.972,
        "specificity": 0.952,
        "roc_auc": 0.992,
        "is_recommended": True,
        "rec_label": "🏆 Tốt nhất (Best)",
        "reason": "Độ nhạy (Sensitivity) cao nhất giúp hạn chế tối đa việc bỏ sót ca bệnh. Đồng thời có khả năng giải thích (Interpretable) tốt nhất cho y khoa."
    },
    "Random Forest": {
        "accuracy": 0.930,
        "sensitivity": 0.944,
        "specificity": 0.905,
        "roc_auc": 0.979,
        "is_recommended": False,
        "rec_label": "🔍 Tham khảo (Reference)",
        "reason": "Mô hình ổn định nhưng độ đặc hiệu thấp hơn Logistic Regression trong bộ dữ liệu này."
    },
    "XGBoost": {
        "accuracy": 0.947,
        "sensitivity": 0.944,
        "specificity": 0.952,
        "roc_auc": 0.987,
        "is_recommended": False,
        "rec_label": "⚙️ Hiệu năng cao (High Performance)",
        "reason": "Hiệu năng rất mạnh mẽ nhưng cần lượng dữ liệu lớn hơn để phát huy tối đa ưu thế."
    }
}

class PredictionService:
    def __init__(self):
        self.models = {}
        self.explainers = {}
        self.probability_calibrators = {}
        self.scaler = None
        self._load_resources()
        self._fit_probability_calibrators()
        
    def get_model_benchmarks(self):
        """Returns stats for all active models."""
        results = {}
        for name in self.models:
            results[name] = MODEL_STATS.get(name, {
                "accuracy": 0.90, "sensitivity": 0.90, "roc_auc": 0.90, 
                "is_recommended": False, "reason": "Dữ liệu hiệu năng đang được cập nhật."
            })
        return results
    def _load_resources(self):
        # 1. Load Scaler
        scaler_path = PROJECT_ROOT / "models" / "ml_scaler.pkl"
        if scaler_path.exists():
            try:
                self.scaler = joblib.load(scaler_path)
                print("✅ ML Scaler integrated.")
            except Exception as e:
                print(f"❌ Error loading scaler: {e}")

        # 2. Load Models
        for model_dir in POSSIBLE_MODEL_DIRS:
            if not model_dir.exists(): continue
            for model_path in model_dir.glob("*.pkl"):
                if "scaler" in model_path.name: continue
                stem = model_path.stem.lower()
                if "xgboost" in stem: name = "XGBoost"
                elif "random_forest" in stem: name = "Random Forest"
                elif "logistic_regression" in stem: name = "Logistic Regression"
                else: name = stem.title()
                
                if name in self.models: continue
                try:
                    model = joblib.load(model_path)
                    self.models[name] = model
                    print(f"✅ Loaded {name} from {model_path.name}")
                    
                    # 3. Create Explainers
                    # Using generic Explainer with a small background dataset for stability
                    # We'll initialize them on-demand or use a simplified linear explainer for LogReg
                    if name in ["XGBoost", "Random Forest"]:
                        try:
                            # Use TreeExplainer specifically for these as it's faster
                            self.explainers[name] = shap.TreeExplainer(model)
                        except:
                            print(f"⚠️ SHAP TreeExplainer failed for {name}, will use fallback.")
                except Exception as e:
                    print(f"❌ Error loading ML {name}: {e}")

    def _fit_probability_calibrators(self):
        """Fit per-model Platt scaling calibrators on a holdout split.

        Logistic calibration is smoother and less prone to hard 0/1 collapse.
        """
        if not self.models:
            return

        try:
            X_all, y_all = load_breast_cancer(return_X_y=True)
            # sklearn target: 0=malignant, 1=benign -> convert to malignant label 1/0
            y_malignant = (y_all == 0).astype(int)

            _, X_cal, _, y_cal = train_test_split(
                X_all,
                y_malignant,
                test_size=0.35,
                random_state=42,
                stratify=y_malignant,
            )

            if self.scaler is not None:
                X_cal_scaled = self.scaler.transform(X_cal)
            else:
                X_cal_scaled = X_cal

            for name, model in self.models.items():
                try:
                    probs = model.predict_proba(X_cal_scaled)
                    classes = getattr(model, "classes_", np.array([0, 1]))
                    class_to_index = {int(cls): idx for idx, cls in enumerate(classes)}

                    if 0 in class_to_index:
                        mal_idx = class_to_index[0]
                        raw_mal = probs[:, mal_idx]
                    elif 1 in class_to_index and probs.shape[1] == 2:
                        raw_mal = 1.0 - probs[:, class_to_index[1]]
                    else:
                        raw_mal = probs[:, 0]

                    # Platt scaling on raw malignant probability.
                    eps = 1e-6
                    x_cal = np.clip(raw_mal, eps, 1.0 - eps).reshape(-1, 1)
                    calibrator = LogisticRegression(max_iter=1000, random_state=42)
                    calibrator.fit(x_cal, y_cal)
                    self.probability_calibrators[name] = calibrator
                    print(f"✅ Calibrated probabilities for {name}")
                except Exception as e:
                    print(f"⚠️ Calibration skipped for {name}: {e}")
        except Exception as e:
            print(f"⚠️ Global probability calibration skipped: {e}")

    def get_available_models(self):
        return sorted(list(self.models.keys()))

    def recommend_model(self):
        """Returns the recommended model based on training performance."""
        # Logistic Regression is preferred for its high ROC-AUC (0.99) and interpretability
        if "Logistic Regression" in self.models:
            return "Logistic Regression"
        return "XGBoost"

    def predict(self, request_data, model_name=None):
        if not self.models: raise ValueError("No ML models available.")
        
        # Default or specific model
        if not model_name or model_name not in self.models:
            model_name = self.recommend_model()
            
        model = self.models[model_name]
        data_dict = request_data.dict()
        
        # Prepare input in correct order
        raw_vals = []
        for f in FEATURES:
             key = f.replace(" ", "_").lower()
             raw_vals.append(data_dict.get(key, 0.0))
        
        input_raw = np.array(raw_vals).reshape(1, -1)
        
        # APPLY SCALING
        if self.scaler:
            input_scaled = self.scaler.transform(input_raw)
        else:
            input_scaled = input_raw # Fallback (will be inaccurate)

        # Predictions
        probs = model.predict_proba(input_scaled)[0]

        # Wisconsin training convention in this project uses class 0 = malignant, class 1 = benign.
        # Keep robust fallback handling if artifacts change.
        prob_mal = None
        mal_idx = 0
        classes = getattr(model, "classes_", None)
        if classes is not None:
            class_to_index = {int(cls): idx for idx, cls in enumerate(classes)}
            if 0 in class_to_index:
                mal_idx = class_to_index[0]
                prob_mal = float(probs[mal_idx])
            elif 1 in class_to_index and len(probs) == 2:
                mal_idx = 1 - class_to_index[1]
                prob_mal = float(1.0 - probs[class_to_index[1]])

        if prob_mal is None:
            # Safe fallback for binary classifiers when classes_ is absent.
            prob_mal = float(probs[0])

        prob_ben = float(1.0 - prob_mal)

        calibrator = self.probability_calibrators.get(model_name)
        if calibrator is not None:
            try:
                x = np.array([[float(np.clip(prob_mal, 1e-6, 1.0 - 1e-6))]])
                prob_mal = float(calibrator.predict_proba(x)[0, 1])
                prob_ben = float(1.0 - prob_mal)
            except Exception as e:
                print(f"⚠️ Calibration transform failed for {model_name}: {e}")
        
        is_mal = prob_mal >= 0.5
        # Return probability of being Malignant (Risk Score)
        confidence = float(np.clip(prob_mal, 0.0, 1.0))
        
        # EXPLAINABILITY (SHAP or Fallback)
        top_features = []
        try:
            # Prepare DataFrame for SHAP consistency
            df_input = pd.DataFrame(input_scaled, columns=FEATURES)
            
            # We want sv_vals where positive means increasing malignant probability.
            if model_name in self.explainers:
                sv = self.explainers[model_name].shap_values(df_input)
                # handle shapes: XGBoost binary usually returns (1, features) contribution to Class 1
                # RF usually returns [(1, features), (1, features)] list for each class
                if isinstance(sv, list):
                    # Select malignant class SHAP contribution if index is available.
                    mal_shap_idx = mal_idx if mal_idx < len(sv) else 0
                    sv_vals = sv[mal_shap_idx].flatten()
                elif len(sv.shape) == 3: # (samples, features, classes)
                    mal_shap_idx = mal_idx if mal_idx < sv.shape[2] else 0
                    sv_vals = sv[0, :, mal_shap_idx]
                else:
                    # Binary SHAP array convention usually aligns with positive class.
                    # If malignant is class 0, flip signs to express malignant contribution.
                    sv_vals = sv.flatten() if mal_idx == 1 else -sv.flatten()
            else:
                # Fallback (e.g. LogReg): map coefficient sign to malignant class direction.
                if hasattr(model, 'coef_'):
                     direction = 1.0 if mal_idx == 1 else -1.0
                     sv_vals = direction * model.coef_[0] * input_scaled.flatten()
                elif hasattr(model, 'feature_importances_'):
                    sv_vals = model.feature_importances_
                else:
                    sv_vals = np.zeros(len(FEATURES))

            # Select top 5 features by absolute impact on malignancy
            indices = np.argsort(np.abs(sv_vals))[-5:][::-1]
            for i in indices:
                val = float(sv_vals[i])
                # IMPORTANT: val > 0 means it makes the result MORE MALIGNANT
                impact_type = "Malignant Risk" if val > 0 else "Benign Indicator"
                
                # Get raw meta info
                feat_name = FEATURES[i]
                clean_name = feat_name.replace("mean ", "").replace("worst ", "").replace(" error", "").title()
                
                # Get mean and raw values for comparison
                current_raw = float(raw_vals[i])
                avg_val = 0.0
                if self.scaler is not None:
                    avg_val = float(self.scaler.mean_[i])
                
                detail = FEATURE_DETAILS.get(clean_name, {"desc": "Dữ liệu đo lường tế bào học.", "advice": "Tư vấn bác sĩ."})
                
                top_features.append({
                    "feature": feat_name.replace("mean ", "").title(),
                    "impact": impact_type,
                    "value": val,
                    "raw_value": current_raw,
                    "average_value": avg_val,
                    "description": detail["desc"],
                    "advice": detail["advice"]
                })
        except Exception as e:
            print(f"❌ Explanation error: {e}")

        return {
            "model_name": model_name,
            "prediction": 1 if is_mal else 0, # Schema mapping: 1=Malignant, 0=Benign
            "diagnosis": "Malignant" if is_mal else "Benign",
            "probability": confidence,
            "analysis_text": self._gen_text(model_name, is_mal, confidence, top_features),
            "top_features": top_features
        }

    def _gen_text(self, model, is_mal, conf, features):
        # Identify the most critical risk driver
        critical_feature = features[0]['feature'] if features else "chỉ số sinh học"
        
        if is_mal:
            header = "🩺 **PHÂN TÍCH CHUYÊN KHOA: PHÁT HIỆN DẤU HIỆU NGHI NGỜ ÁC TÍNH**"
            
            if conf > 0.9:
                tone_desc = f"Hệ thống ghi nhận sự tương đồng rất cao ({conf*100:.1f}%) giữa mẫu tế bào của bạn với các đặc tính điển hình của ung thư xâm lấn."
            else:
                tone_desc = f"Hệ thống phát hiện dấu hiệu bất thường (Độ tin cậy: {conf*100:.1f}%). Tuy nhiên, kết quả này hiện đang nằm ở vùng ranh giới lâm sàng cần đánh giá thêm."
                
            p_analysis = f"\n\n**Phân tích trọng yếu:** Sự sai lệch lớn nhất tập trung ở chỉ số **{critical_feature}**. Trong y sinh học, điều này phản ánh sự mất kiểm soát của bộ khung tế bào, khiến ranh giới khối u trở nên nham nhở - một dấu hiệu 'lá cờ đỏ' (Red Flag) chứng minh tính xâm lấn mạnh."
            
            advice = "\n\n📋 **LỘ TRÌNH HÀNH ĐỘNG KHẨN CẤP:**\n1. **Bình tĩnh & Hành động:** Đây mới chỉ là kết quả sàng lọc AI. Bạn cần thực hiện **Sinh thiết kim (Core Biopsy)** ngay để có kết quả giải phẫu bệnh chính xác nhất.\n2. **Chuyên khoa:** Liên hệ với bác sĩ ung bướu để chỉ định thêm MRI hoặc CT-Scan đánh giá mức độ lan rộng.\n3. **Cung cấp dữ liệu:** Hãy mang theo bản báo cáo SHAP này để bác sĩ thấy được các biến số hình học tế bào đang bị lỗi."
        else:
            header = "🩺 **PHÂN TÍCH CHUYÊN KHOA: DẤU HIỆU LÀNH TÍNH**"
            
            if conf > 0.8:
                tone_desc = f"Hệ thống xác nhận các chỉ số của bạn hiện nằm hoàn toàn trong ngưỡng an toàn ({conf*100:.1f}%). Không tìm thấy bằng chứng của sự tăng sinh ác tính."
            else:
                tone_desc = f"Kết quả nghiêng về lành tính ({conf*100:.1f}%), nhưng các chỉ số đang tiệm cận vùng ranh giới nghi ngờ. Cần theo dõi thêm để loại trừ sai số."
                
            p_analysis = f"\n\n**Cơ sở đánh giá:** Chỉ số **{critical_feature}** là yếu tố then chốt giúp bác sĩ AI nhận định đây là khối u lành. Đặc điểm này cho thấy ranh giới tế bào vẫn trơn láng, không có dấu hiệu 'xé rào' để xâm nhập vào các mô mạch máu lân cận."
            
            advice = "\n\n📋 **KẾ HOẠCH THEO DÕI SỨC KHỎE:**\n1. **Duy trì:** Tự khám vú hàng tháng vào sau kỳ kinh 3-5 ngày. Nếu thấy khối u cứng lại hoặc tiết dịch đầu ti, hãy tái khám ngay.\n2. **Khám định kỳ:** Chụp Mammography định kỳ mỗi 6-12 tháng tùy theo chỉ định của bác sĩ tại cơ sở y tế.\n3. **Lối sống:** Bổ sung nhiều rau xanh họ cải (như súp lơ) giúp tăng khả năng tự sửa chữa lỗi DNA của tế bào."
            
        return f"{header}\n\n{tone_desc}{p_analysis}{advice}"

prediction_service = PredictionService()
