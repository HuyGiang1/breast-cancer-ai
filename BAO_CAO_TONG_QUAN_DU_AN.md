# BÁO CÁO TỔNG QUAN HỌC THUẬT DỰ ÁN BREAST CANCER AI

## 1. Giới thiệu đề tài

### 1.1 Tên đề tài

**Breast Cancer AI Prediction System**  
Hệ thống hỗ trợ sàng lọc ung thư vú bằng trí tuệ nhân tạo, kết hợp **Machine Learning**, **Deep Learning**, **Explainable AI** và **ứng dụng web**.

### 1.2 Bối cảnh và động cơ nghiên cứu

Ung thư vú là một trong những bệnh lý ác tính phổ biến ở phụ nữ, có tỷ lệ mắc cao và ảnh hưởng lớn tới sức khỏe cộng đồng. Trong thực hành lâm sàng, việc phát hiện sớm đóng vai trò rất quan trọng vì giúp tăng khả năng can thiệp kịp thời và cải thiện tiên lượng điều trị. Tuy nhiên, việc đánh giá nguy cơ và hỗ trợ ra quyết định ban đầu vẫn còn phụ thuộc nhiều vào kinh nghiệm chuyên môn, khả năng tiếp cận thiết bị và chất lượng dữ liệu đầu vào.

Trong bối cảnh đó, trí tuệ nhân tạo có thể đóng vai trò như một lớp hỗ trợ bổ sung, giúp:

- phân tích dữ liệu lâm sàng dạng số,
- phân tích ảnh nhũ ảnh,
- cung cấp giải thích cho dự đoán,
- hỗ trợ người dùng và bác sĩ tiếp cận thông tin nhanh hơn.

Từ nhu cầu đó, dự án Breast Cancer AI được xây dựng nhằm phát triển một hệ thống nghiên cứu và ứng dụng có khả năng:

- hỗ trợ sàng lọc ung thư vú trên nhiều loại dữ liệu,
- cung cấp kết quả có thể giải thích,
- tích hợp thành hệ thống web có thể trình diễn, thử nghiệm và mở rộng triển khai.

### 1.3 Mục tiêu đề tài

Mục tiêu chung của đề tài là xây dựng một nền tảng hỗ trợ sàng lọc ung thư vú bằng AI, có khả năng kết hợp nghiên cứu mô hình với triển khai hệ thống thực tế ở mức thử nghiệm.

Các mục tiêu cụ thể gồm:

1. Xây dựng nhánh **Machine Learning** cho dữ liệu lâm sàng có cấu trúc.
2. Xây dựng nhánh **Deep Learning** cho ảnh nhũ ảnh.
3. So sánh hiệu năng giữa các mô hình và giữa các hướng tiếp cận ML, DL.
4. Tăng tính minh bạch của mô hình thông qua **SHAP** và **Grad-CAM**.
5. Tích hợp toàn bộ pipeline vào hệ thống web có:
   - đăng ký, đăng nhập,
   - quản lý bệnh nhân,
   - lưu lịch sử dự đoán,
   - chatbot hỏi đáp,
   - email khôi phục mật khẩu,
   - lời khuyên từ mô hình ngôn ngữ lớn.

### 1.4 Phạm vi đề tài

Đề tài tập trung vào bài toán **phân loại nhị phân**:

- **Benign**: lành tính
- **Malignant**: ác tính

Hệ thống hỗ trợ ba chế độ dự đoán:

- **Dự đoán lâm sàng bằng ML**
- **Dự đoán ảnh nhũ ảnh bằng DL**
- **Dự đoán đa phương thức** bằng cách kết hợp tín hiệu từ ML và DL

Đề tài mang tính chất **hỗ trợ sàng lọc**, không thay thế chẩn đoán xác định của bác sĩ chuyên khoa hoặc các xét nghiệm như sinh thiết, giải phẫu bệnh.

---

## 2. Bài toán nghiên cứu và ý nghĩa học thuật

### 2.1 Bài toán nghiên cứu

Bài toán cốt lõi của đề tài là xây dựng một hệ thống AI có khả năng dự đoán nguy cơ ung thư vú dựa trên:

- dữ liệu lâm sàng dạng số của khối u,
- dữ liệu ảnh nhũ ảnh,
- hoặc kết hợp đồng thời cả hai nguồn tín hiệu.

Trên phương diện học máy, đây là bài toán **binary classification** có tính chất đặc thù vì:

- yêu cầu độ nhạy cao để hạn chế bỏ sót ca bệnh,
- cần khả năng giải thích để phù hợp với bối cảnh y tế,
- chất lượng dữ liệu đầu vào có ảnh hưởng lớn đến độ tin cậy của dự đoán.

### 2.2 Ý nghĩa học thuật

Đề tài có ý nghĩa ở các khía cạnh sau:

- so sánh hiệu quả giữa **Machine Learning truyền thống** và **Deep Learning**;
- đánh giá mô hình không chỉ bằng accuracy mà còn bằng các chỉ số có ý nghĩa lâm sàng như **Sensitivity**, **Specificity**, **ROC-AUC**;
- áp dụng **Explainable AI** để làm rõ quyết định của mô hình;
- xây dựng một hệ thống có khả năng trình bày như một nghiên cứu hoàn chỉnh, từ dữ liệu thô tới triển khai ứng dụng.

### 2.3 Ý nghĩa thực tiễn

Ở góc độ ứng dụng, hệ thống có thể hỗ trợ:

- người dùng tra cứu kiến thức và định hướng bước tiếp theo,
- bác sĩ hoặc người hướng dẫn minh họa cách AI hỗ trợ sàng lọc,
- nhóm nghiên cứu có một nền tảng tích hợp để tiếp tục thử nghiệm mô hình mới.

---

## 3. Công nghệ và công cụ sử dụng

### 3.1 Ngôn ngữ và nền tảng phát triển

- **Python 3.9+** cho xử lý dữ liệu, huấn luyện mô hình và backend.
- **JavaScript thuần** cho frontend web.
- **HTML/CSS** cho giao diện người dùng.
- **Jupyter Notebook** cho nghiên cứu, EDA, huấn luyện và phân tích kết quả.

### 3.2 Công nghệ học máy và học sâu

- **scikit-learn**: Logistic Regression, Random Forest, preprocessing, metrics.
- **XGBoost**: gradient boosting cho dữ liệu lâm sàng.
- **TensorFlow / Keras**: tải và suy luận với mô hình ảnh `.keras`.
- **PyTorch**: một số thành phần nghiên cứu và explainability.
- **NumPy, Pandas**: xử lý dữ liệu số.
- **OpenCV, Pillow**: xử lý ảnh.
- **imbalanced-learn**: xử lý mất cân bằng dữ liệu bằng SMOTE.

### 3.3 Explainable AI

- **SHAP** cho mô hình ML
- **Grad-CAM** cho mô hình DL

### 3.4 Backend, cấu hình và tích hợp hệ thống

- **FastAPI**: xây dựng API REST.
- **Pydantic**: kiểm tra dữ liệu đầu vào và đầu ra.
- **Uvicorn**: chạy server ASGI.
- **SQLite**: lưu tài khoản, bệnh nhân, lịch sử dự đoán và lịch sử chat.
- **python-dotenv**: nạp cấu hình môi trường từ `.env`.
- **SMTP (Gmail)**: gửi email chào mừng và khôi phục mật khẩu.
- **Docker / Docker Compose**: đóng gói backend ở mức triển khai thử nghiệm.

### 3.5 LLM và lớp tư vấn thông minh

- **Gemini API**: provider chính cho chatbot và lời khuyên AI.
- **OpenAI API**: provider dự phòng khi Gemini không khả dụng.
- **Local rule-based fallback**: lớp dự phòng cuối để hệ thống không bị gián đoạn hoàn toàn.

### 3.6 Công nghệ giao diện

- **HTML/CSS/JavaScript thuần**
- **Google Fonts Manrope**
- frontend dạng **single-page static web app** đặt trong thư mục `frontend/`

---

## 4. Dữ liệu sử dụng trong nghiên cứu

### 4.1 Bộ dữ liệu Wisconsin Diagnostic Breast Cancer (WDBC)

Nhánh Machine Learning sử dụng bộ dữ liệu Wisconsin Diagnostic Breast Cancer, bao gồm:

- khoảng **569 mẫu**,
- **30 đặc trưng số** mô tả hình thái nhân tế bào,
- nhãn đích gồm hai lớp: lành tính và ác tính.

Bộ dữ liệu này phù hợp để:

- so sánh các mô hình ML cổ điển,
- xây dựng baseline lâm sàng,
- khai thác khả năng giải thích thông qua SHAP.

### 4.2 Bộ dữ liệu CBIS-DDSM

Nhánh Deep Learning sử dụng tập ảnh nhũ ảnh CBIS-DDSM. Đây là bộ dữ liệu ảnh y khoa được dùng phổ biến trong nghiên cứu về ung thư vú.

Vai trò của bộ dữ liệu này trong đề tài:

- huấn luyện mô hình phân tích ảnh,
- thử nghiệm các kiến trúc CNN và transfer learning,
- đánh giá khả năng sinh heatmap giải thích bằng Grad-CAM.

### 4.3 Tổ chức dữ liệu trong dự án

- `data/raw/`: dữ liệu gốc
- `data/processed/`: dữ liệu sau tiền xử lý
- `models/`: mô hình đã huấn luyện và artifact
- `experiments/results/`: biểu đồ, bảng kết quả, tổng hợp nghiên cứu
- `frontend/results/`: ảnh kết quả phục vụ giao diện web

---

## 5. Kiến trúc tổng thể hệ thống

Hệ thống được xây dựng theo mô hình nhiều lớp, tách rõ phần giao diện, dịch vụ API, mô hình dự đoán và lưu trữ dữ liệu.

### 5.1 Lớp giao diện người dùng

Frontend trong thư mục `frontend/` cung cấp các chức năng:

- xem kiến thức và video giáo dục,
- trò chuyện với AI,
- chạy dự đoán ML, DL, multimodal,
- xem thống kê nghiên cứu,
- lưu và xem lại lịch sử dự đoán,
- quản lý bệnh nhân với vai trò bác sĩ.

### 5.2 Lớp dịch vụ backend

Backend FastAPI trong `backend/app/` đảm nhiệm:

- xác thực người dùng,
- quản lý phiên đăng nhập,
- quản lý hồ sơ bệnh nhân,
- xử lý dự đoán ML/DL/Fusion,
- lưu lịch sử dự đoán và chat,
- gửi email khôi phục mật khẩu,
- điều phối AI Advisor và chatbot.

### 5.3 Lớp mô hình và nghiên cứu

Thư mục `src/` và `notebooks/` chứa:

- pipeline tiền xử lý dữ liệu,
- mô hình ML và DL,
- notebook EDA, huấn luyện, đánh giá, giải thích,
- kết quả benchmark và kiểm định thống kê.

### 5.4 Lớp lưu trữ

Hệ thống sử dụng SQLite để lưu:

- tài khoản người dùng,
- phiên đăng nhập,
- token khôi phục mật khẩu,
- hồ sơ bệnh nhân,
- lịch sử dự đoán,
- lịch sử hội thoại với chatbot.

### 5.5 Đánh giá kiến trúc

Kiến trúc hiện tại phù hợp với:

- nghiên cứu học thuật,
- demo end-to-end,
- triển khai thử nghiệm quy mô nhỏ.

Tuy nhiên, để production thực tế ở quy mô lớn, hệ thống vẫn cần thêm các lớp hạ tầng và bảo mật chuyên sâu hơn.

---

## 6. Luồng xử lý nghiệp vụ của hệ thống

### 6.1 Luồng dự đoán lâm sàng bằng Machine Learning

1. Người dùng nhập 30 đặc trưng lâm sàng.
2. Backend kiểm tra dữ liệu bằng schema Pydantic.
3. Prediction service chọn mô hình ML phù hợp.
4. Mô hình trả về xác suất ác tính, nhãn chẩn đoán và mức rủi ro.
5. Hệ thống sinh các yếu tố chính ảnh hưởng tới kết quả.
6. AI Advisor sinh lời khuyên bằng ngôn ngữ tự nhiên.
7. Nếu đã đăng nhập, kết quả được lưu vào lịch sử.

### 6.2 Luồng dự đoán ảnh bằng Deep Learning

1. Người dùng tải ảnh nhũ ảnh lên hệ thống.
2. Backend kiểm tra định dạng file và đọc bytes ảnh.
3. DeepLearningService nạp mô hình `.keras` phù hợp.
4. Hệ thống dự đoán xác suất và nhãn đầu ra.
5. Nếu bật giải thích, hệ thống sinh ảnh minh họa vùng mô hình chú ý.
6. AI Advisor sinh lời khuyên theo ngữ cảnh ảnh.
7. Kết quả được lưu nếu người dùng đang đăng nhập.

### 6.3 Luồng dự đoán đa phương thức

1. Người dùng gửi đồng thời dữ liệu lâm sàng và ảnh.
2. Hệ thống chạy song song nhánh ML và DL.
3. Xác suất hợp nhất được tính theo trọng số.
4. AI Advisor tạo lời khuyên chung cho kết quả fusion.
5. Toàn bộ kết quả được lưu thành bản ghi multimodal.

### 6.4 Luồng chatbot hỗ trợ

1. Người dùng nhập câu hỏi bằng tiếng Việt.
2. Hệ thống trích lịch sử hội thoại gần nhất.
3. Chatbot ưu tiên gọi Gemini.
4. Nếu Gemini lỗi hoặc hết quota, hệ thống fallback sang OpenAI nếu đã cấu hình.
5. Nếu không có provider ngoài, hệ thống trả lời bằng local rule-based fallback.
6. Nếu người dùng đã đăng nhập, nội dung chat được lưu lại.

### 6.5 Luồng quản lý tài khoản và bệnh nhân

1. Người dùng đăng ký hoặc đăng nhập.
2. Hệ thống sinh session token.
3. Với tài khoản bác sĩ, người dùng có thể tạo hồ sơ bệnh nhân.
4. Các kết quả dự đoán có thể gắn với từng bệnh nhân cụ thể.
5. Lịch sử được truy xuất theo user hoặc theo patient.

### 6.6 Luồng quên mật khẩu và email

1. Người dùng gửi yêu cầu quên mật khẩu.
2. Backend sinh reset token có thời hạn.
3. Token được gửi qua email hoặc ghi file tùy chế độ cấu hình.
4. Người dùng dùng token để đặt lại mật khẩu.

---

## 7. Tiền xử lý dữ liệu và kiểm soát chất lượng

### 7.1 Pipeline dữ liệu cho nhánh ML

Module `src/data_processing/__init__.py` triển khai:

- tải dữ liệu Wisconsin,
- chia train/validation/test theo stratified split,
- chuẩn hóa dữ liệu bằng `StandardScaler`,
- xử lý mất cân bằng bằng **SMOTE** trên tập train,
- tránh data leakage bằng cách chỉ fit scaler trên train.

### 7.2 Kiểm soát mất cân bằng lớp

Mất cân bằng dữ liệu được xử lý bằng nhiều kỹ thuật:

- **SMOTE** cho dữ liệu số,
- **class_weight** cho một số mô hình ML,
- **Focal Loss** và weighting cho DL,
- hiệu chỉnh ngưỡng theo mục tiêu sensitivity/specificity.

### 7.3 ROI và fine-tuning ảnh

Đề tài có nhánh nghiên cứu ROI preprocessing và fine-tuning ảnh nhũ ảnh để:

- tập trung vào vùng tổn thương quan trọng,
- cải thiện độ ổn định dự đoán,
- nâng cao khả năng giải thích của mô hình ảnh.

### 7.4 Kiểm soát chất lượng artifact

Trong hệ thống triển khai, backend còn có các cơ chế:

- phát hiện artifact ML không ổn định,
- loại bỏ artifact DL chất lượng thấp,
- nạp calibration profile,
- chọn mô hình/artefact có ưu tiên cao hơn dựa trên metadata và profile nghiên cứu.

---

## 8. Phân hệ Machine Learning

### 8.1 Các mô hình được sử dụng

Nhánh ML hiện sử dụng ba mô hình chính:

- **Logistic Regression**
- **Random Forest**
- **XGBoost**

### 8.2 Vai trò của từng mô hình

- **Logistic Regression**: baseline y khoa, dễ diễn giải, phù hợp với dữ liệu cấu trúc.
- **Random Forest**: ensemble method có tính ổn định và khả năng khái quát tốt.
- **XGBoost**: boosting model hiệu năng cao trên dữ liệu tabular.

### 8.3 Kết quả benchmark hiện có

Theo benchmark đã được ghi trong mã nguồn:

| Mô hình | Accuracy | Sensitivity | Specificity | ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.965 | 0.972 | 0.952 | 0.992 |
| Random Forest | 0.930 | 0.944 | 0.905 | 0.979 |
| XGBoost | 0.947 | 0.944 | 0.952 | 0.987 |

### 8.4 Nhận xét học thuật

Các số liệu cho thấy:

- Logistic Regression là một baseline rất mạnh trong dữ liệu lâm sàng này.
- XGBoost cho hiệu năng rất cao, phù hợp để so sánh nâng cao.
- Nhánh ML trong đề tài hiện mạnh hơn nhánh DL về mức ổn định tổng thể.

### 8.5 Vai trò trong hệ thống web

Trong giao diện triển khai, nhánh ML trả về:

- nhãn chẩn đoán,
- xác suất,
- risk band,
- các yếu tố chính,
- lời khuyên từ AI.

---

## 9. Phân hệ Deep Learning

### 9.1 Các kiến trúc được nghiên cứu

Đề tài đã thử nghiệm các hướng DL chính:

- **EfficientNet-B0**
- **ResNet50**
- **Custom CNN**
- **Custom CNN v2 / ROI-tuned**

### 9.2 Cơ chế nạp mô hình trong backend

Backend có thể tự dò model `.keras` trong các thư mục:

- `models/deep_learning/`
- `src/models/deep_learning/`
- `backend/`

Ngoài ra hệ thống còn hỗ trợ:

- warmup khi khởi động,
- chọn target size theo mô hình,
- nạp calibration profile ngoài,
- phân biệt model chính và model thử nghiệm.

### 9.3 Benchmark hiện có trong giao diện nghiên cứu

| Mô hình | Accuracy | Sensitivity | Specificity | ROC-AUC |
|---|---:|---:|---:|---:|
| EfficientNet-B0 | 0.419689 | 1.000000 | 0.000000 | 0.500000 |
| ResNet50 | 0.458549 | 0.956790 | 0.098214 | 0.546737 |
| Custom CNN | 0.476684 | 0.956790 | 0.129464 | 0.604608 |
| Custom CNN v2 | 0.505181 | 0.950617 | 0.183036 | 0.583636 |

### 9.4 Nhận xét học thuật

Kết quả cho thấy:

- nhánh DL có sensitivity khá cao,
- specificity còn thấp,
- mô hình có xu hướng báo động quá mức,
- hướng cải tiến chính là ROI tuning, calibration và tinh chỉnh artifact tốt hơn.

### 9.5 Vai trò trong hệ thống web

Trong giao diện, nhánh DL hiện hiển thị:

- kết quả chẩn đoán,
- xác suất,
- risk band,
- ảnh giải thích,
- lời khuyên từ AI.

---

## 10. Explainable AI và giải thích kết quả

### 10.1 SHAP cho Machine Learning

Module `src/explainability/shap_explainer.py` hỗ trợ:

- `TreeExplainer`
- `LinearExplainer`
- `KernelExplainer`
- summary plot
- bar plot
- waterfall plot
- force plot

### 10.2 Grad-CAM cho Deep Learning

Module `src/explainability/gradcam.py` hỗ trợ:

- trích gradient tại layer mục tiêu,
- tạo heatmap,
- chồng heatmap lên ảnh gốc,
- xuất hình minh họa phục vụ báo cáo và trình diễn.

### 10.3 Ý nghĩa học thuật và ứng dụng

Explainability giúp đề tài tránh trở thành một hộp đen thuần túy. Hệ thống có thể trả lời các câu hỏi như:

- đặc trưng nào làm tăng nguy cơ,
- vùng nào trên ảnh làm mô hình chú ý,
- dự đoán có phù hợp với hiểu biết y học hay không.

### 10.4 Phân biệt giữa lớp nghiên cứu và lớp triển khai web

Để báo cáo trung thực, cần phân biệt:

- **Lớp nghiên cứu**: notebook có thể hiển thị đầy đủ SHAP plots và Grad-CAM analysis.
- **Lớp triển khai web**: giao diện tập trung vào các yếu tố chính, ảnh giải thích và lời khuyên AI để tối ưu trải nghiệm sử dụng.

Điều này cho thấy hệ thống web là lớp ứng dụng hóa của kết quả nghiên cứu, không thay thế toàn bộ notebook phân tích sâu.

---

## 11. Backend FastAPI và hệ thống API

### 11.1 Cấu trúc backend

Entry point của backend nằm tại `backend/app/main.py`, thực hiện:

- nạp biến môi trường từ `.env`,
- khởi tạo FastAPI,
- bật CORS,
- mount thư mục kết quả tĩnh,
- khởi tạo cơ sở dữ liệu khi startup,
- preload mô hình DL nếu cấu hình cho phép.

### 11.2 Các nhóm API chính

Hệ thống hiện có các nhóm endpoint:

- **Auth**
- **Patient management**
- **Prediction history**
- **Chatbot**
- **Research summary**
- **Model listing / benchmarks / warmup**
- **Prediction ML / DL / multimodal**

Các endpoint tiêu biểu:

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/forgot-password/`
- `POST /api/v1/predict/`
- `POST /api/v1/predict/image/`
- `POST /api/v1/predict/multimodal/`
- `POST /api/v1/chat/ask/`
- `GET /api/v1/predictions/history/`
- `GET /api/v1/models/benchmarks/`

### 11.3 Bảo mật và quản lý phiên

Backend hiện hỗ trợ:

- xác thực bằng bearer token,
- phân quyền theo vai trò `user` và `doctor`,
- hash mật khẩu bằng PBKDF2-HMAC-SHA256,
- session token có thời hạn,
- reset token có thời hạn,
- kiểm tra quyền sở hữu bệnh nhân trước khi thao tác dữ liệu.

### 11.4 AI Advisor và chatbot tư vấn

AI Advisor Service chịu trách nhiệm:

- sinh lời khuyên cho kết quả ML,
- sinh lời khuyên cho kết quả DL,
- sinh lời khuyên cho kết quả multimodal,
- trả lời câu hỏi trong chatbot.

Luồng provider:

1. **Gemini** là provider ưu tiên
2. **OpenAI** là provider fallback nếu Gemini không khả dụng
3. **local rule-based** là fallback cuối

Hệ thống cũng lưu `advice_provider` và `advice_model` để biết rõ lời khuyên đang đến từ nguồn nào.

---

## 12. Cơ sở dữ liệu và quản lý người dùng

### 12.1 Hệ quản trị dữ liệu

Đề tài sử dụng **SQLite** nhằm:

- đơn giản hóa triển khai,
- phù hợp môi trường học tập và demo,
- giảm độ phức tạp hạ tầng trong giai đoạn đầu.

### 12.2 Các bảng dữ liệu chính

- `users`
- `sessions`
- `password_reset_tokens`
- `patients`
- `predictions`
- `chat_messages`

### 12.3 Vai trò của từng bảng

- `users`: lưu thông tin tài khoản
- `sessions`: lưu phiên đăng nhập
- `password_reset_tokens`: phục vụ quên mật khẩu
- `patients`: hồ sơ bệnh nhân cho bác sĩ
- `predictions`: lịch sử dự đoán ML, DL, multimodal
- `chat_messages`: lịch sử hỏi đáp với AI

### 12.4 Phân quyền người dùng

Hệ thống hỗ trợ hai vai trò:

- **user**: chạy dự đoán, hỏi AI, xem lịch sử cá nhân
- **doctor**: ngoài các quyền trên còn có thể tạo và quản lý hồ sơ bệnh nhân, gắn kết quả vào từng bệnh nhân

### 12.5 Email thật và khôi phục mật khẩu

Hệ thống đã có khả năng gửi email thật thông qua SMTP:

- email chào mừng khi đăng ký,
- email khôi phục mật khẩu,
- hỗ trợ Gmail SMTP thông qua cấu hình `.env`

Đây là thành phần cho thấy dự án không chỉ là mô hình AI mà còn là một ứng dụng web có workflow hoàn chỉnh.

---

## 13. Giao diện người dùng và khả năng trình diễn

### 13.1 Đặc điểm giao diện

Frontend được xây dựng theo phong cách web app hiện đại, định hướng trình bày rõ ràng, dễ thao tác và phù hợp cho demo học thuật.

### 13.2 Các trang chức năng chính

- Trang chủ
- Kiến thức
- Chăm sóc
- Video
- Hỏi AI
- Dự đoán
- Thống kê
- Lịch sử
- Bệnh nhân
- Về chúng tôi
- Đăng nhập / Đăng ký / Khôi phục mật khẩu / Hồ sơ cá nhân

### 13.3 Giá trị trình diễn với giảng viên

Giao diện hiện có thể demo rõ:

- đăng ký, đăng nhập,
- tạo bệnh nhân,
- nhập dữ liệu lâm sàng,
- tải ảnh nhũ ảnh,
- xem kết quả dự đoán,
- xem lịch sử,
- hỏi chatbot,
- tra cứu thống kê nghiên cứu.

---

## 14. Hệ thống notebook và quy trình nghiên cứu

### 14.1 Vai trò của notebook trong đề tài

Notebook là phần quan trọng nhất để chứng minh đề tài không chỉ là một website AI, mà là một quá trình nghiên cứu bài bản từ dữ liệu thô đến mô hình và kết quả.

### 14.2 Nhóm notebook Wisconsin

| Notebook | Mục đích |
|---|---|
| `01_wisconsin_eda.ipynb` | Khám phá dữ liệu lâm sàng |
| `02_wisconsin_preprocessing.ipynb` | Tiền xử lý dữ liệu |
| `03_wisconsin_train_models.ipynb` | Huấn luyện ML |
| `04_wisconsin_evaluation_shap.ipynb` | Giải thích bằng SHAP |
| `05_wisconsin_cross_validation.ipynb` | Kiểm chứng độ ổn định |
| `06_wisconsin_error_analysis.ipynb` | Phân tích lỗi |
| `07_wisconsin_feature_engineering.ipynb` | Nghiên cứu đặc trưng |

### 14.3 Nhóm notebook CBIS-DDSM

| Notebook | Mục đích |
|---|---|
| `08_cbis_download_prepare.ipynb` | Chuẩn bị dữ liệu ảnh |
| `09_cbis_cnn_training.ipynb` | Huấn luyện DL |
| `10_cbis_gradcam_explainability.ipynb` | Giải thích bằng Grad-CAM |
| `12_roi_preprocessing_and_finetuning.ipynb` | ROI và fine-tuning |

### 14.4 Notebook so sánh và kiểm định

| Notebook | Mục đích |
|---|---|
| `11_ml_vs_dl_comparative_study.ipynb` | So sánh ML và DL |
| `11_comparative_study_ml_vs_dl.ipynb` | Bản so sánh bổ sung |
| `13_statistical_significance_ablation.ipynb` | Kiểm định thống kê và ablation |

### 14.5 Giá trị học thuật

Chuỗi notebook tạo thành pipeline nghiên cứu hoàn chỉnh:

1. khám phá dữ liệu,
2. tiền xử lý,
3. huấn luyện,
4. đánh giá,
5. giải thích,
6. so sánh,
7. kiểm định thống kê.

---

## 15. Script tự động hóa và vận hành

Thư mục `scripts/` cho thấy dự án đã có lớp tự động hóa thay vì chỉ thao tác thủ công trong notebook.

Một số script tiêu biểu:

- `train_ml_calibrated.py`
- `train_dl_finetune_calibrated.py`
- `run_dl_retrain_pipeline.py`
- `promote_best_dl_model.py`
- `export_dl_calibration_profile.py`
- `select_best_dl_model.py`
- `compare_dl_summaries.py`
- `smoke_test_api.py`
- `diagnose_ml_calibration.py`

Ý nghĩa của lớp script:

- huấn luyện lại mô hình,
- chọn artifact tốt nhất,
- xuất calibration profile,
- kiểm tra nhanh API,
- hỗ trợ quy trình nghiên cứu và triển khai thử nghiệm.

---

## 16. Triển khai và chạy thực tế

### 16.1 Chạy local

Quy trình local ở mức cơ bản:

1. tạo virtual environment,
2. cài dependencies,
3. cấu hình `.env`,
4. chạy backend FastAPI,
5. mở frontend.

### 16.2 Docker

`docker-compose.yml` hiện cho phép chạy backend trong container và mount thư mục model để không cần build lại image mỗi lần retrain. Tuy nhiên, Docker hiện mới ở mức **demo/trial deployment**, chưa phải production stack hoàn chỉnh.

### 16.3 Kết quả tĩnh

Ảnh kết quả và một số tài nguyên tĩnh được phục vụ từ thư mục static, giúp thuận tiện cho giao diện web và cho việc lấy ảnh đưa vào báo cáo.

### 16.4 Mức độ sẵn sàng triển khai hiện tại

Hệ thống hiện có thể đánh giá như sau:

- **Research-ready**: sẵn sàng cho mục đích nghiên cứu và báo cáo học thuật
- **Demo-ready**: sẵn sàng để trình diễn end-to-end cho giảng viên
- **Chưa production-ready hoàn chỉnh**: cần thêm hardening về bảo mật, hạ tầng và vận hành trước khi mở rộng triển khai thực tế

---

## 17. Đánh giá kết quả và nhận xét kỹ thuật

### 17.1 Điểm mạnh của hệ thống

- Có cả ML, DL và multimodal
- Có explainability cho cả hai nhánh
- Có backend, frontend, auth, patient management, history
- Có chatbot và AI Advisor tích hợp LLM
- Có luồng email thật cho reset password
- Có benchmark nghiên cứu và notebook đầy đủ
- Có lớp script hỗ trợ vận hành và tái huấn luyện

### 17.2 Hạn chế hiện tại

- Nhánh DL vẫn cần cải thiện specificity
- Một số artifact DL còn cho chất lượng thấp
- Chất lượng đầu vào ảnh ảnh hưởng mạnh tới kết quả
- SQLite phù hợp demo nhưng chưa tối ưu cho nhiều người dùng đồng thời
- CORS hiện còn mở rộng để phục vụ phát triển
- Session token phía frontend cần tăng cường bảo mật nếu deploy Internet công khai
- Docker và tài liệu triển khai chưa bao phủ đầy đủ toàn bộ production stack
- Nội dung tư vấn AI chỉ mang tính hỗ trợ, không thay thế khuyến nghị lâm sàng chính thức

### 17.3 Hướng phát triển

- Thu thập thêm dữ liệu trong bối cảnh Việt Nam
- Cải thiện specificity cho nhánh DL
- Tối ưu inference bằng ONNX
- Tích hợp PACS hoặc hệ thống bệnh viện
- Xây dựng ứng dụng di động
- Nâng cấp hạ tầng deploy với reverse proxy, monitoring và backup
- Tăng cường bảo mật cho auth, session và reset flow
- Viết thêm test tự động end-to-end

---

## 18. Kết luận

Dự án Breast Cancer AI là một hệ thống nghiên cứu và ứng dụng tương đối hoàn chỉnh, kết hợp:

- dữ liệu lâm sàng có cấu trúc,
- ảnh y khoa,
- Machine Learning,
- Deep Learning,
- Explainable AI,
- API backend,
- giao diện web,
- quản lý tài khoản và bệnh nhân,
- chatbot hỗ trợ bằng AI,
- email khôi phục mật khẩu,
- khả năng triển khai thử nghiệm thực tế.

Về mặt học thuật, đề tài chứng minh được cách tiếp cận kết hợp giữa nghiên cứu mô hình và xây dựng hệ thống ứng dụng. Về mặt thực hành, hệ thống đã có đủ thành phần để trình diễn trực tiếp cho giảng viên dưới dạng một sản phẩm end-to-end, không chỉ là tập hợp các notebook rời rạc.

Đề tài cũng cho thấy tiềm năng tiếp tục phát triển theo hướng ứng dụng y tế số, nơi AI không chỉ dừng ở dự đoán mà còn hỗ trợ giải thích, lưu vết, giao tiếp với người dùng và tích hợp dần vào quy trình nghiệp vụ thực tế.

---

## 19. Tài liệu tham khảo nội bộ trong dự án

- `README.md`
- `PROJECT_STATUS.md`
- `QUICKSTART.md`
- `RESEARCH_PAPER.md`
- `backend/app/main.py`
- `backend/app/api/endpoints.py`
- `backend/app/services/prediction.py`
- `backend/app/services/prediction_dl.py`
- `backend/app/services/ai_advisor.py`
- `backend/app/core/database.py`
- `backend/app/core/security.py`
- `backend/app/core/mailer.py`
- `src/data_processing/__init__.py`
- `src/models/wisconsin_models.py`
- `src/explainability/shap_explainer.py`
- `src/explainability/gradcam.py`

