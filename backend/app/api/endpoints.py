from datetime import datetime, timezone
from html import escape
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Header
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from typing import List, Dict, Any, Optional
from app.api.schemas import (
    PredictionRequest,
    PredictionResponse,
    MultiModalResponse,
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    SavedPredictionResponse,
    ChatRequest,
    ChatResponse,
    SavedChatMessage,
    ClinicalExtractionResponse,
)
from app.services.prediction import prediction_service
from app.services.prediction_dl import dl_prediction_service, STATIC_RESULTS_DIR
from app.services.ai_advisor import ai_advisor_service
from app.core.database import db, future_iso, utc_now_iso
from app.core.mailer import send_password_reset_email, send_welcome_email
from app.core.security import (
    hash_password,
    verify_password,
    create_session_token,
    create_password_reset_token,
    get_current_user,
    get_optional_current_user,
)
import base64
import json
import mimetypes
import os
from pathlib import Path

router = APIRouter()

MAX_IMAGE_UPLOAD_BYTES = int(os.getenv("APP_MAX_IMAGE_UPLOAD_MB", "20")) * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


async def _read_validated_image_upload(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_UPLOAD_BYTES:
        max_mb = MAX_IMAGE_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"Image is too large. Max upload size is {max_mb} MB.")
    return image_bytes


def _internal_error(detail: str = "Internal server error") -> HTTPException:
    return HTTPException(status_code=500, detail=detail)


def _serialize_user(row: Dict[str, Any] | Any) -> Dict[str, Any]:
    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
        "full_name": str(row["full_name"]),
        "role": str(row["role"] or "user"),
    }


def _risk_band(probability: float) -> str:
    if probability < 0.35:
        return "Low"
    if probability < 0.65:
        return "Medium"
    return "High"


def _displayed_malignant_probability(result: Dict[str, Any]) -> float:
    probability = float(result.get("probability", 0.0))
    diagnosis = str(result.get("diagnosis") or "")
    if diagnosis == "Benign":
        return 1.0 - probability
    return probability


def _reliability_from_margin(margin: float) -> str:
    if margin < 0.08:
        return "Low"
    if margin < 0.18:
        return "Medium"
    return "High"


def _build_uncertainty_payload(
    *,
    displayed_malignant_probability: float,
    label: str = "kết quả",
    extra_reasons: Optional[list[str]] = None,
) -> Dict[str, Any]:
    p = max(0.0, min(1.0, float(displayed_malignant_probability)))
    margin = abs(p - 0.5)
    reasons = list(extra_reasons or [])
    reliability = _reliability_from_margin(margin)

    if margin < 0.08:
        reasons.insert(
            0,
            f"Xác suất {label} nằm rất gần ngưỡng quyết định 50%, nên cần thận trọng khi diễn giải.",
        )
    elif margin < 0.18:
        reasons.insert(
            0,
            f"Xác suất {label} chưa cách xa ngưỡng quyết định, nên xem đây là tín hiệu hỗ trợ thay vì kết luận chắc chắn.",
        )

    warning = None
    if reasons:
        warning = (
            "Kết quả có độ chắc chắn chưa cao. Nên đối chiếu với triệu chứng, phim chụp, xét nghiệm "
            "và đánh giá của bác sĩ chuyên khoa."
        )
    elif reliability == "High":
        warning = "Tín hiệu mô hình tương đối rõ, nhưng vẫn chỉ có giá trị hỗ trợ sàng lọc."

    return {
        "reliability_label": reliability,
        "uncertainty_warning": warning,
        "uncertainty_reasons": reasons,
    }


def _attach_uncertainty(result: Dict[str, Any], label: str) -> Dict[str, Any]:
    result.update(
        _build_uncertainty_payload(
            displayed_malignant_probability=_displayed_malignant_probability(result),
            label=label,
        )
    )
    return result


def _require_patient_ownership(user_id: int, patient_id: Optional[int]) -> Optional[dict]:
    if patient_id is None:
        return None

    row = db.fetch_one(
        "SELECT * FROM patients WHERE id = ? AND user_id = ?",
        (patient_id, user_id),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(row)


def _require_doctor(current_user: dict) -> None:
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Doctor role required")


def _serialize_row(row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _serialize_saved_prediction(row) -> SavedPredictionResponse:
    input_payload = json.loads(row["input_payload"]) if row["input_payload"] else {}
    response_payload = json.loads(row["response_payload"]) if row["response_payload"] else {}
    return SavedPredictionResponse(
        id=int(row["id"]),
        patient_id=row["patient_id"],
        prediction_type=str(row["prediction_type"]),
        model_name=row["model_name"],
        diagnosis=row["diagnosis"],
        probability=row["probability"],
        raw_probability=row["raw_probability"],
        calibration_mode=row["calibration_mode"],
        risk_band=row["risk_band"],
        advice=row["advice"],
        advice_provider=response_payload.get("advice_provider"),
        advice_model=response_payload.get("advice_model"),
        created_at=str(row["created_at"]),
        input_payload=input_payload,
        response_payload=response_payload,
    )


def _serialize_saved_chat(row) -> SavedChatMessage:
    return SavedChatMessage(
        id=int(row["id"]),
        question=str(row["question"]),
        answer=str(row["answer"]),
        created_at=str(row["created_at"]),
    )


def _fetch_owned_prediction(prediction_id: int, current_user: dict) -> dict:
    row = db.fetch_one(
        """
        SELECT * FROM predictions
        WHERE id = ? AND user_id = ?
        """,
        (prediction_id, current_user["id"]),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return _serialize_row(row)


def _format_report_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _html_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.6g}"
    return escape(str(value))


def _report_table(title: str, rows: list[tuple[str, Any]]) -> str:
    if not rows:
        return ""
    body = "".join(
        f"<tr><th>{escape(label)}</th><td>{_html_value(value)}</td></tr>"
        for label, value in rows
    )
    return f"<section><h2>{escape(title)}</h2><table>{body}</table></section>"


def _clinical_input_rows(payload: Dict[str, Any]) -> list[tuple[str, Any]]:
    clinical_data = payload.get("clinical_data")
    source = clinical_data if isinstance(clinical_data, dict) else payload
    if not isinstance(source, dict):
        return []

    return [
        (key.replace("_", " ").title(), value)
        for key, value in source.items()
        if isinstance(value, (int, float, str)) and key not in {"filename", "content_type"}
    ][:40]


def _top_features_html(response_payload: Dict[str, Any]) -> str:
    top_features = response_payload.get("top_features")
    if not isinstance(top_features, list) or not top_features:
        return "<p>Không có dữ liệu SHAP/top feature cho lần dự đoán này.</p>"

    items = []
    for item in top_features[:10]:
        if not isinstance(item, dict):
            continue
        feature = escape(str(item.get("feature", "Unknown feature")))
        value = _html_value(item.get("value"))
        impact = _html_value(item.get("impact", item.get("importance")))
        items.append(f"<li><strong>{feature}</strong>: value {value}, impact {impact}</li>")
    return f"<ol>{''.join(items)}</ol>" if items else "<p>Không có dữ liệu SHAP/top feature hợp lệ.</p>"


def _explanation_image_html(response_payload: Dict[str, Any]) -> str:
    explanation_image = response_payload.get("explanation_image")
    if not explanation_image:
        dl_result = response_payload.get("dl_result")
        if isinstance(dl_result, dict):
            explanation_image = dl_result.get("explanation_image")

    if not explanation_image:
        return "<p>Không có ảnh Grad-CAM cho lần dự đoán này.</p>"

    src = str(explanation_image)
    if src.startswith("/results/"):
        result_path = STATIC_RESULTS_DIR / Path(src).name
        if result_path.exists() and result_path.is_file():
            mime_type = mimetypes.guess_type(result_path.name)[0] or "image/png"
            encoded = base64.b64encode(result_path.read_bytes()).decode("ascii")
            src = f"data:{mime_type};base64,{encoded}"

    src = escape(src)
    return (
        "<p>Ảnh Grad-CAM/vùng chú ý của mô hình:</p>"
        f"<img class=\"heatmap\" src=\"{src}\" alt=\"Grad-CAM explanation\">"
    )


def _build_prediction_report_html(row: dict, current_user: dict) -> str:
    input_payload = json.loads(row["input_payload"]) if row.get("input_payload") else {}
    response_payload = json.loads(row["response_payload"]) if row.get("response_payload") else {}
    patient = None
    if row.get("patient_id") is not None:
        patient = db.fetch_one(
            "SELECT full_name, date_of_birth, gender FROM patients WHERE id = ? AND user_id = ?",
            (row["patient_id"], current_user["id"]),
        )

    prediction_type = str(row.get("prediction_type") or "unknown").upper()
    diagnosis = str(row.get("diagnosis") or "N/A")
    title = f"BreastCare Mint - AI Prediction Report #{int(row['id'])}"
    patient_rows = [
        ("Người xuất báo cáo", current_user.get("full_name")),
        ("Email", current_user.get("email")),
        ("Vai trò", current_user.get("role")),
    ]
    if patient is not None:
        patient_rows.extend(
            [
                ("Bệnh nhân", patient["full_name"]),
                ("Ngày sinh", patient["date_of_birth"]),
                ("Giới tính", patient["gender"]),
            ]
        )

    summary_rows = [
        ("Mã dự đoán", row.get("id")),
        ("Loại dự đoán", prediction_type),
        ("Chẩn đoán AI", diagnosis),
        ("Xác suất hiển thị", _format_report_percent(row.get("probability"))),
        ("Xác suất gốc", _format_report_percent(row.get("raw_probability"))),
        ("Mức nguy cơ", row.get("risk_band")),
        ("Độ tin cậy diễn giải", response_payload.get("reliability_label")),
        ("Mô hình", row.get("model_name")),
        ("Hiệu chỉnh", row.get("calibration_mode")),
        ("Thời gian tạo", row.get("created_at")),
    ]

    clinical_rows = _clinical_input_rows(input_payload)
    advice = row.get("advice") or response_payload.get("advice") or ""
    analysis_text = row.get("analysis_text") or response_payload.get("analysis_text") or ""
    uncertainty_warning = response_payload.get("uncertainty_warning")
    uncertainty_reasons = response_payload.get("uncertainty_reasons")
    if not isinstance(uncertainty_reasons, list):
        uncertainty_reasons = []
    uncertainty_html = ""
    if uncertainty_warning or uncertainty_reasons:
        reason_items = "".join(f"<li>{escape(str(reason))}</li>" for reason in uncertainty_reasons)
        uncertainty_html = f"""
  <section>
    <h2>Độ tin cậy và cảnh báo diễn giải</h2>
    <div class="note">{escape(str(uncertainty_warning or "Cần thận trọng khi diễn giải kết quả."))}</div>
    {f"<ul>{reason_items}</ul>" if reason_items else ""}
  </section>"""

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #173331; line-height: 1.55; margin: 36px; }}
    h1 {{ color: #134d39; margin-bottom: 4px; }}
    h2 {{ color: #145e43; border-bottom: 1px solid #bbf7e0; padding-bottom: 6px; margin-top: 28px; }}
    .meta {{ color: #5f766f; margin-bottom: 24px; }}
    .badge {{ display: inline-block; padding: 6px 10px; border-radius: 8px; background: #dcfdf0; color: #138259; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #d6eee6; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ width: 32%; background: #f0fdf8; color: #145e43; }}
    .note {{ background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 12px; }}
    .block {{ white-space: pre-wrap; background: #f8fffc; border: 1px solid #d6eee6; border-radius: 8px; padding: 12px; }}
    .heatmap {{ max-width: 100%; border: 1px solid #d6eee6; border-radius: 8px; margin-top: 10px; }}
    @media print {{ body {{ margin: 18mm; }} }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class="meta">Báo cáo hỗ trợ nghiên cứu và sàng lọc, tạo từ dữ liệu dự đoán đã lưu.</div>
  <p><span class="badge">{escape(diagnosis)}</span></p>
  {_report_table("Thông tin người dùng/bệnh nhân", patient_rows)}
  {_report_table("Tóm tắt kết quả AI", summary_rows)}
  {uncertainty_html}
  {_report_table("Dữ liệu đầu vào lâm sàng", clinical_rows)}
  <section>
    <h2>Yếu tố giải thích / SHAP</h2>
    {_top_features_html(response_payload)}
  </section>
  <section>
    <h2>Ảnh giải thích / Grad-CAM</h2>
    {_explanation_image_html(response_payload)}
  </section>
  <section>
    <h2>Nhận định</h2>
    <div class="block">{escape(str(analysis_text or "Chưa có nhận định chi tiết."))}</div>
  </section>
  <section>
    <h2>Lời khuyên</h2>
    <div class="block">{escape(str(advice or "Chưa có lời khuyên cho lần dự đoán này."))}</div>
  </section>
  <section>
    <h2>Giới hạn sử dụng</h2>
    <div class="note">
      Kết quả AI chỉ có giá trị hỗ trợ sàng lọc và nghiên cứu. Báo cáo này không thay thế
      chẩn đoán, sinh thiết, giải phẫu bệnh hoặc quyết định điều trị của bác sĩ chuyên khoa.
    </div>
  </section>
</body>
</html>"""


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _metric_percent(value: Any) -> Optional[float]:
    try:
        return round(float(value) * 100.0, 1)
    except (TypeError, ValueError):
        return None


def _best_ablation_condition(rows: Any, metric: str) -> Optional[Dict[str, Any]]:
    if not isinstance(rows, list):
        return None
    candidates = [row for row in rows if isinstance(row, dict) and row.get(metric) is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda row: float(row.get(metric, 0.0)))


def _build_research_evidence() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    phase2 = _load_json_file(root / "experiments/results/phase2_summary.json") or {}
    phase3 = _load_json_file(root / "experiments/results/phase3_statistical_analysis.json") or {}
    ml_retrain = _load_json_file(root / "models/ml_retrain_report_20260404.json") or {}

    ablation_rows = phase3.get("ablation_study", [])
    best_auc = _best_ablation_condition(ablation_rows, "roc_auc")
    best_sensitivity = _best_ablation_condition(ablation_rows, "sensitivity")
    phase2_best = phase2.get("best_model", {}) if isinstance(phase2.get("best_model"), dict) else {}
    key_findings = phase2.get("key_findings", {}) if isinstance(phase2.get("key_findings"), dict) else {}

    ml_rows = []
    for model_name, payload in ml_retrain.items():
        if not isinstance(payload, dict):
            continue
        ml_rows.append(
            {
                "model": model_name,
                "roc_auc_percent": _metric_percent(payload.get("roc_auc")),
                "artifact": payload.get("saved_model"),
            }
        )
    ml_rows.sort(key=lambda row: row.get("roc_auc_percent") or 0.0, reverse=True)

    highlights = []
    if ml_rows:
        highlights.append(
            {
                "label": "ML clinical",
                "value": f"{ml_rows[0]['roc_auc_percent']}%" if ml_rows[0].get("roc_auc_percent") is not None else "N/A",
                "title": f"{ml_rows[0]['model']} có ROC-AUC cao nhất sau retrain",
                "text": "Dữ liệu lâm sàng Wisconsin vẫn là nhánh mạnh, ổn định và dễ giải thích bằng SHAP/top features.",
            }
        )
    if phase2_best:
        highlights.append(
            {
                "label": "DL screening",
                "value": _metric_percent(phase2_best.get("sensitivity")),
                "title": str(phase2_best.get("name", "Best DL model")),
                "text": "Nhánh ảnh ưu tiên sensitivity để giảm bỏ sót ca nghi ngờ, đổi lại specificity còn thấp và cần bác sĩ xác nhận.",
            }
        )
    if key_findings:
        highlights.append(
            {
                "label": "Clinical safety",
                "value": key_findings.get("false_negative_rate", "N/A"),
                "title": "Tỷ lệ bỏ sót ca ác tính được theo dõi riêng",
                "text": "Dashboard tách false negative và ca cần kiểm tra thêm, phù hợp cách đánh giá hệ thống AI y tế.",
            }
        )

    return {
        "sources": {
            "phase2_summary": "experiments/results/phase2_summary.json" if phase2 else None,
            "phase3_statistical_analysis": "experiments/results/phase3_statistical_analysis.json" if phase3 else None,
            "ml_retrain_report": "models/ml_retrain_report_20260404.json" if ml_retrain else None,
        },
        "highlights": highlights,
        "ml_retrain": ml_rows,
        "dl_best_model": {
            "name": phase2_best.get("name"),
            "threshold": phase2_best.get("threshold"),
            "accuracy_percent": _metric_percent(phase2_best.get("accuracy")),
            "sensitivity_percent": _metric_percent(phase2_best.get("sensitivity")),
            "specificity_percent": _metric_percent(phase2_best.get("specificity")),
            "roc_auc_percent": _metric_percent(phase2_best.get("roc_auc")),
        } if phase2_best else None,
        "ablation": {
            "best_auc_condition": best_auc,
            "best_sensitivity_condition": best_sensitivity,
            "rows": ablation_rows if isinstance(ablation_rows, list) else [],
        },
        "clinical_interpretation": [
            "Sensitivity cao được ưu tiên trong sàng lọc ung thư vú để giảm nguy cơ bỏ sót ca ác tính.",
            "Specificity thấp nghĩa là hệ thống có thể báo động quá mức; kết quả AI cần được bác sĩ và xét nghiệm xác nhận.",
            "ML lâm sàng phù hợp để giải thích bằng đặc trưng tế bào; DL ảnh nhũ ảnh phù hợp làm tín hiệu hình ảnh bổ sung.",
        ],
    }


@router.post("/auth/register/", response_model=AuthResponse)
def register(request: RegisterRequest):
    existing = db.fetch_one("SELECT id FROM users WHERE email = ?", (request.email.lower(),))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    now = utc_now_iso()
    user_id = db.execute(
        """
        INSERT INTO users (email, full_name, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            request.email.lower(),
            request.full_name.strip(),
            hash_password(request.password),
            request.role,
            now,
            now,
        ),
    )
    token = create_session_token()
    db.execute(
        """
        INSERT INTO sessions (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token, future_iso(24 * 14), now),
    )
    try:
        send_welcome_email(
            email=request.email.lower(),
            full_name=request.full_name.strip(),
        )
    except Exception as exc:
        print(f"Welcome email skipped: {exc}")
    return AuthResponse(
        access_token=token,
        user={
            "id": user_id,
            "email": request.email.lower(),
            "full_name": request.full_name.strip(),
            "role": request.role,
        },
    )


@router.post("/auth/login/", response_model=AuthResponse)
def login(request: LoginRequest):
    row = db.fetch_one("SELECT * FROM users WHERE email = ?", (request.email.lower(),))
    if row is None or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_session_token()
    db.execute(
        """
        INSERT INTO sessions (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (int(row["id"]), token, future_iso(24 * 14), utc_now_iso()),
    )
    return AuthResponse(
        access_token=token,
        user=_serialize_user(row),
    )


@router.get("/auth/me/", response_model=Dict[str, Any])
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/auth/logout/", response_model=Dict[str, str])
def logout(current_user: dict = Depends(get_current_user), authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"message": "Logged out successfully."}


@router.post("/auth/logout-all/", response_model=Dict[str, str])
def logout_all(current_user: dict = Depends(get_current_user)):
    db.execute("DELETE FROM sessions WHERE user_id = ?", (current_user["id"],))
    return {"message": "Logged out from all sessions."}


@router.put("/auth/profile/", response_model=Dict[str, Any])
def update_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    full_name = request.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="Full name cannot be empty")
    db.execute(
        "UPDATE users SET full_name = ?, updated_at = ? WHERE id = ?",
        (full_name, utc_now_iso(), current_user["id"]),
    )
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": full_name,
        "role": current_user.get("role", "user"),
    }


@router.post("/auth/change-password/", response_model=Dict[str, str])
def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    row = db.fetch_one("SELECT password_hash FROM users WHERE id = ?", (current_user["id"],))
    if row is None or not verify_password(request.current_password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    db.execute(
        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (hash_password(request.new_password), utc_now_iso(), current_user["id"]),
    )
    return {"message": "Password changed successfully."}


@router.post("/auth/forgot-password/", response_model=ForgotPasswordResponse)
def forgot_password(request: ForgotPasswordRequest):
    row = db.fetch_one("SELECT id FROM users WHERE email = ?", (request.email.lower(),))
    if row is None:
        return ForgotPasswordResponse(message="If the email exists, a reset token has been created.")

    token = create_password_reset_token()
    expires_at = future_iso(2)
    db.execute(
        """
        INSERT INTO password_reset_tokens (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (int(row["id"]), token, expires_at, utc_now_iso()),
    )
    send_password_reset_email(
        email=request.email.lower(),
        reset_token=token,
        expires_at=expires_at,
    )
    return ForgotPasswordResponse(
        message="Email dat lai mat khau da duoc gui neu tai khoan ton tai.",
        reset_token=token if os.getenv("APP_MAIL_MODE", "file").strip().lower() == "file" else None,
        expires_at=expires_at,
    )


@router.post("/auth/reset-password/", response_model=Dict[str, str])
def reset_password(request: ResetPasswordRequest):
    row = db.fetch_one(
        """
        SELECT * FROM password_reset_tokens
        WHERE token = ? AND used_at IS NULL
        """,
        (request.token,),
    )
    if row is None:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token expired")

    db.execute(
        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (hash_password(request.new_password), utc_now_iso(), int(row["user_id"])),
    )
    db.execute(
        "UPDATE password_reset_tokens SET used_at = ? WHERE id = ?",
        (utc_now_iso(), int(row["id"])),
    )
    return {"message": "Password updated successfully."}


@router.get("/patients/", response_model=List[PatientResponse])
def list_patients(current_user: dict = Depends(get_current_user)):
    _require_doctor(current_user)
    rows = db.fetch_all(
        "SELECT * FROM patients WHERE user_id = ? ORDER BY updated_at DESC",
        (current_user["id"],),
    )
    return [PatientResponse(**_serialize_row(row)) for row in rows]


@router.post("/patients/", response_model=PatientResponse)
def create_patient(request: PatientCreateRequest, current_user: dict = Depends(get_current_user)):
    _require_doctor(current_user)
    now = utc_now_iso()
    patient_id = db.execute(
        """
        INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user["id"],
            request.full_name.strip(),
            request.date_of_birth,
            request.gender,
            request.notes,
            now,
            now,
        ),
    )
    row = db.fetch_one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    return PatientResponse(**_serialize_row(row))


@router.put("/patients/{patient_id}/", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    request: PatientUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    _require_doctor(current_user)
    _require_patient_ownership(current_user["id"], patient_id)
    db.execute(
        """
        UPDATE patients
        SET full_name = ?, date_of_birth = ?, gender = ?, notes = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            request.full_name.strip(),
            request.date_of_birth,
            request.gender,
            request.notes,
            utc_now_iso(),
            patient_id,
            current_user["id"],
        ),
    )
    row = db.fetch_one("SELECT * FROM patients WHERE id = ? AND user_id = ?", (patient_id, current_user["id"]))
    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse(**_serialize_row(row))


@router.delete("/patients/{patient_id}/", response_model=Dict[str, str])
def delete_patient(patient_id: int, current_user: dict = Depends(get_current_user)):
    _require_doctor(current_user)
    _require_patient_ownership(current_user["id"], patient_id)
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM patients WHERE id = ? AND user_id = ?",
            (patient_id, current_user["id"]),
        )
    return {"message": "Patient deleted successfully."}


@router.get("/predictions/history/", response_model=List[SavedPredictionResponse])
def list_prediction_history(
    patient_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    if patient_id is not None:
        _require_doctor(current_user)
        _require_patient_ownership(current_user["id"], patient_id)
        rows = db.fetch_all(
            """
            SELECT * FROM predictions
            WHERE user_id = ? AND patient_id = ?
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (current_user["id"], patient_id),
        )
    else:
        rows = db.fetch_all(
            """
            SELECT * FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (current_user["id"],),
        )
    return [_serialize_saved_prediction(row) for row in rows]


@router.get("/predictions/{prediction_id}/report/")
def export_prediction_report(
    prediction_id: int,
    current_user: dict = Depends(get_current_user),
):
    row = _fetch_owned_prediction(prediction_id, current_user)
    html = _build_prediction_report_html(row, current_user)
    filename = f"breastcare_prediction_report_{prediction_id}.html"
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/chat/ask/", response_model=ChatResponse)
def ask_chatbot(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history_payload = [item.model_dump() for item in request.history]
    chat_result = ai_advisor_service.chat_about_breast_cancer(message=message, history=history_payload)
    created_at = utc_now_iso()

    if current_user is not None:
        db.execute(
            """
            INSERT INTO chat_messages (user_id, question, answer, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (current_user["id"], message, chat_result["answer"], created_at),
        )

    return ChatResponse(
        answer=chat_result["answer"],
        provider=chat_result["provider"],
        model=chat_result["model"],
        created_at=created_at,
    )


@router.get("/chat/history/", response_model=List[SavedChatMessage])
def get_chat_history(current_user: dict = Depends(get_current_user)):
    rows = db.fetch_all(
        """
        SELECT * FROM chat_messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (current_user["id"],),
    )
    return [_serialize_saved_chat(row) for row in rows]


@router.get("/research/summary/", response_model=Dict[str, Any])
def get_research_summary():
    """Return the latest Phase 3 statistical summary for frontend dashboards."""
    project_root = Path(__file__).resolve().parents[3]
    candidate_paths = [
        project_root / "experiments/results/phase3_statistical_analysis.json",
        project_root / "experiments/results/statistical_significance_ablation.json",
    ]

    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            return {
                "source": path.name,
                "generated_from": str(path),
                "data": payload,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read {path.name}: {exc}") from exc

    raise HTTPException(
        status_code=404,
        detail="No statistical summary found. Run the notebook export step first.",
    )


@router.get("/research/evidence/", response_model=Dict[str, Any])
def get_research_evidence():
    """Return compact research evidence extracted from saved experiment artifacts."""
    return _build_research_evidence()


@router.get("/models/", response_model=List[str])
def list_available_models():
    return prediction_service.get_available_models()

@router.get("/models/benchmarks/", response_model=Dict[str, Any])
def get_model_benchmarks():
    return prediction_service.get_model_benchmarks()

@router.get("/models/dl/", response_model=List[str])
def list_available_dl_models():
    return dl_prediction_service.get_available_models()


@router.get("/models/dl/status/", response_model=Dict[str, Any])
def get_dl_model_status():
    return dl_prediction_service.get_model_status()


@router.post("/models/dl/warmup/", response_model=Dict[str, Any])
def warmup_dl_models(model_name: Optional[str] = None):
    return dl_prediction_service.preload_models(model_name=model_name)


@router.get("/results/{filename}")
def get_result_image(filename: str):
    safe_name = Path(filename).name
    file_path = STATIC_RESULTS_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Result image not found")
    return FileResponse(file_path)

@router.post("/predict/", response_model=PredictionResponse)
def predict_diagnosis(
    request: PredictionRequest,
    model_name: str = None,
    patient_id: Optional[int] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    try:
        result = prediction_service.predict(request, model_name=model_name)
        _attach_uncertainty(result, "ML lâm sàng")
        advice_result = ai_advisor_service.advice_for_single(result, mode="ml")
        result["advice"] = advice_result["advice"]
        result["advice_provider"] = advice_result["provider"]
        result["advice_model"] = advice_result["model"]
        result["analysis_text"] = f"{result.get('analysis_text', '')}\n\n{advice_result['advice']}".strip()
        if current_user is not None:
            if patient_id is not None:
                _require_doctor(current_user)
            _require_patient_ownership(current_user["id"], patient_id)
            db.save_prediction(
                user_id=current_user["id"],
                patient_id=patient_id,
                prediction_type="ml",
                model_name=result.get("model_name"),
                diagnosis=result.get("diagnosis"),
                probability=result.get("probability"),
                raw_probability=result.get("raw_probability"),
                calibration_mode=result.get("calibration_mode"),
                risk_band=result.get("risk_band"),
                advice=result.get("advice"),
                analysis_text=result.get("analysis_text"),
                input_payload=request.model_dump(),
                response_payload=result,
            )
        return PredictionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Prediction error: {e}")
        raise _internal_error("Prediction failed.")

@router.post("/predict/image/", response_model=PredictionResponse)
async def predict_diagnosis_image(
    file: UploadFile = File(...),
    model_name: str = None,
    include_explanation: bool = False,
    patient_id: Optional[int] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    try:
        image_bytes = await _read_validated_image_upload(file)
        result = dl_prediction_service.predict(
            image_bytes,
            model_name=model_name,
            include_explanation=include_explanation,
        )
        _attach_uncertainty(result, "DL ảnh nhũ ảnh")
        advice_result = ai_advisor_service.advice_for_single(result, mode="dl")
        result["advice"] = advice_result["advice"]
        result["advice_provider"] = advice_result["provider"]
        result["advice_model"] = advice_result["model"]
        result["analysis_text"] = f"{result.get('analysis_text', '')}\n\n{advice_result['advice']}".strip()
        if current_user is not None:
            if patient_id is not None:
                _require_doctor(current_user)
            _require_patient_ownership(current_user["id"], patient_id)
            db.save_prediction(
                user_id=current_user["id"],
                patient_id=patient_id,
                prediction_type="dl",
                model_name=result.get("model_name"),
                diagnosis=result.get("diagnosis"),
                probability=result.get("probability"),
                raw_probability=result.get("raw_probability"),
                calibration_mode=result.get("calibration_mode"),
                risk_band=result.get("risk_band"),
                advice=result.get("advice"),
                analysis_text=result.get("analysis_text"),
                input_payload={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "include_explanation": include_explanation,
                },
                response_payload=result,
            )
        return PredictionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image prediction error: {e}")
        raise _internal_error("Image prediction failed.")


@router.post("/predict/extract-clinical/", response_model=ClinicalExtractionResponse)
async def extract_clinical_from_report_image(
    file: UploadFile = File(...),
):
    try:
        image_bytes = await _read_validated_image_upload(file)
        result = ai_advisor_service.extract_clinical_features_from_image(
            image_bytes=image_bytes,
            content_type=file.content_type,
        )
        return ClinicalExtractionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Clinical extraction error: {e}")
        raise _internal_error("Clinical extraction failed.")

@router.post("/predict/multimodal/", response_model=MultiModalResponse)
async def predict_multimodal(
    clinical_data: str = Form(...),
    image_file: UploadFile = File(...),
    ml_model: str = Form(None),
    dl_model: str = Form(None),
    include_explanation: bool = Form(False),
    patient_id: Optional[int] = Form(None),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """
    Combined diagnosis using both Clinical Data (ML) and X-ray Image (DL).
    """
    try:
        # 1. Process Clinical Data
        data_json = json.loads(clinical_data)
        request = PredictionRequest(**data_json)
        ml_res = prediction_service.predict(request, model_name=ml_model)
        
        # 2. Process Image
        image_bytes = await _read_validated_image_upload(image_file)
        dl_res = dl_prediction_service.predict(
            image_bytes,
            model_name=dl_model,
            include_explanation=include_explanation,
        )
        
        # 3. Fusion Logic
        # Both services return malignant probability in [0, 1].
        p_ml = float(ml_res['probability'])
        p_dl = float(dl_res['probability'])
        
        # Give more weight to DL for visual evidence, but ML is strong for cellular detail
        combined_p = (p_ml * 0.4) + (p_dl * 0.6)
        is_mal = combined_p >= 0.5
        extra_uncertainty_reasons: list[str] = []
        if ml_res.get("diagnosis") != dl_res.get("diagnosis"):
            extra_uncertainty_reasons.append(
                "Nhánh ML lâm sàng và nhánh DL ảnh nhũ ảnh đang đưa ra kết luận khác nhau."
            )
        
        advice_result = ai_advisor_service.advice_for_multimodal(ml_res, dl_res, combined_p)
        uncertainty_payload = _build_uncertainty_payload(
            displayed_malignant_probability=combined_p,
            label="đa phương thức",
            extra_reasons=extra_uncertainty_reasons,
        )

        response = MultiModalResponse(
            ml_result=PredictionResponse(**ml_res),
            dl_result=PredictionResponse(**dl_res),
            combined_diagnosis="Malignant" if is_mal else "Benign",
            combined_confidence=combined_p if is_mal else (1 - combined_p),
            combined_risk_band=_risk_band(combined_p),
            advice=advice_result["advice"],
            advice_provider=advice_result["provider"],
            advice_model=advice_result["model"],
            **uncertainty_payload,
        )
        if current_user is not None:
            if patient_id is not None:
                _require_doctor(current_user)
            _require_patient_ownership(current_user["id"], patient_id)
            db.save_prediction(
                user_id=current_user["id"],
                patient_id=patient_id,
                prediction_type="multimodal",
                model_name=f"ML:{ml_res.get('model_name')}|DL:{dl_res.get('model_name')}",
                diagnosis=response.combined_diagnosis,
                probability=response.combined_confidence,
                raw_probability=None,
                calibration_mode="fusion_weighted_average",
                risk_band=response.combined_risk_band,
                advice=response.advice,
                analysis_text=response.advice,
                input_payload={
                    "clinical_data": data_json,
                    "ml_model": ml_model,
                    "dl_model": dl_model,
                    "image_filename": image_file.filename,
                },
                response_payload=response.model_dump(),
            )
        return response
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid clinical_data JSON.")
    except ValidationError as e:
        print(f"Fusion clinical validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid clinical_data payload.")
    except Exception as e:
        print(f"Fusion prediction error: {e}")
        raise _internal_error("Fusion prediction failed.")
