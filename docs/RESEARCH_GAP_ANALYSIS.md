# Research Gap Analysis

## Project hiện tại đủ để bảo vệ nghiên cứu khoa học chưa?

NO.

Project đã đủ mạnh để trình diễn một demo AI y tế có backend/frontend thật, nhưng chưa đủ để bảo vệ như một nghiên cứu ML/DL/multimodal hoàn chỉnh. Lý do chính không nằm ở web, mà ở scientific validity: DL split có dấu hiệu leakage theo study-prefix và multimodal fusion hiện là heuristic.

## Điểm mạnh

- Có hệ thống demo thực tế: FastAPI backend, static frontend, Docker Compose, Nginx.
- Có nhiều thành phần nghiên cứu: ML clinical, DL image, Grad-CAM, SHAP/top features, calibration profile, bootstrap/statistical artifacts.
- ML trên WDBC có script retrain calibrated: `scripts/train_ml_calibrated.py`.
- DL có pipeline fine-tuning/calibration: `scripts/train_dl_finetune_calibrated.py`.
- API có history, report export, patient flow, AI advisor, research dashboard.
- Project đã bắt đầu tách cảnh báo uncertainty/reliability cho kết quả prediction.

## Điểm yếu

- README cũ mô tả sai frontend là React/NextJS và còn nhiều metric `TBD`.
- `endpoints.py` đang quá lớn, gom auth/patient/prediction/chat/research/model vào một file.
- Model weights, dataset images, cache `.pyc` từng được Git track, không phù hợp public repo.
- `.gitignore` cũ ignore quá rộng, làm docs/scripts/assets cần thiết bị bỏ qua.
- CI/test chưa có trước audit.
- Docker artifact strategy chưa rõ: image build không nên chứa toàn bộ model/dataset nặng.

## Scientific Blockers

1. DATA LEAKAGE: kiểm tra prefix trước `__` trong `data/cbis_ddsm/processed/images` phát hiện 90 study-prefix xuất hiện ở nhiều split. Metrics DL hiện tại không được dùng làm kết luận cuối.
2. MULTIMODAL VALIDITY: endpoint `POST /predict/multimodal/` đang dùng `combined_probability = ML * 0.4 + DL * 0.6`. Chưa có validation-set tuning, paired dataset, hay ablation chứng minh multimodal tốt hơn ML-only/DL-only.
3. PAIRED DATA: WDBC clinical features và CBIS-DDSM images là hai nguồn dữ liệu khác bản chất. Nếu không có sample-level pairing, multimodal chỉ là product demo, không phải contribution nghiên cứu được chứng minh.
4. CALIBRATION CLAIMS: có calibrated artifacts, nhưng cần report Brier/calibration curve/ECE sau split hợp lệ.
5. GENERALIZATION: chưa có external validation độc lập; phải ghi rõ limitation.

## Những Thứ BẮT BUỘC Bổ Sung

- Tạo split manifest theo patient/study cho CBIS-DDSM và verify không cross-split duplicate.
- Re-run DL evaluation trên split hợp lệ.
- Tạo paired validation/test dataset hoặc tuyên bố multimodal là demo heuristic, không phải kết quả nghiên cứu chính.
- Nếu có paired data: tune fusion weights trên validation only, khóa test set cho đánh giá cuối.
- Ablation tối thiểu: ML-only, DL-only, multimodal heuristic, multimodal tuned.
- Report metrics: Accuracy, Precision, Sensitivity/Recall, Specificity, F1, ROC-AUC, PR-AUC, Balanced Accuracy, Confusion Matrix.
- Report false negatives riêng vì bài toán ung thư.
- Tạo model card, data card, deployment guide, README đúng thực tế.
- Dọn Git tracking trước khi public.

## Những Thứ NÊN Bổ Sung

- Bootstrap 95% CI cho các metric chính.
- Calibration: Brier score, calibration curve, ECE nếu có đủ sample.
- SHAP/coefficient explanation cho ML model chính.
- Grad-CAM sanity examples cho DL, nhưng không thổi phồng như bằng chứng chẩn đoán.
- Health/readiness endpoint và CI tối thiểu.
- Router split sau khi các blocker nghiên cứu được xử lý.

## Những Thứ KHÔNG CẦN Làm Lúc Này

- Không chuyển static frontend sang React/NextJS.
- Không nâng chatbot/AI advisor thành contribution nghiên cứu chính.
- Không thêm DenseNet/ResNet/EfficientNet chỉ để tăng số lượng model.
- Không migrate PostgreSQL nếu demo ít user và chưa có yêu cầu public multi-user thật.
- Không thêm animation/UI polish khi leakage và multimodal validity chưa xong.

## Product Features Không Tăng Giá Trị Khoa Học Nhiều

- AI chat/advice text.
- Product/care recommendation content.
- Avatar/dropdown/account polish.
- Extra marketing-like sections.
- Video/education content, trừ khi mục tiêu có thêm usability study.
