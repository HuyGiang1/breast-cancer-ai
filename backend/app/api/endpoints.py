from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Header
from fastapi.responses import FileResponse
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
import json
import os
from pathlib import Path

router = APIRouter()


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/image/", response_model=PredictionResponse)
async def predict_diagnosis_image(
    file: UploadFile = File(...),
    model_name: str = None,
    include_explanation: bool = False,
    patient_id: Optional[int] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        image_bytes = await file.read()
        result = dl_prediction_service.predict(
            image_bytes,
            model_name=model_name,
            include_explanation=include_explanation,
        )
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/extract-clinical/", response_model=ClinicalExtractionResponse)
async def extract_clinical_from_report_image(
    file: UploadFile = File(...),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        image_bytes = await file.read()
        result = ai_advisor_service.extract_clinical_features_from_image(
            image_bytes=image_bytes,
            content_type=file.content_type,
        )
        return ClinicalExtractionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        image_bytes = await image_file.read()
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
        
        advice_result = ai_advisor_service.advice_for_multimodal(ml_res, dl_res, combined_p)

        response = MultiModalResponse(
            ml_result=PredictionResponse(**ml_res),
            dl_result=PredictionResponse(**dl_res),
            combined_diagnosis="Malignant" if is_mal else "Benign",
            combined_confidence=combined_p if is_mal else (1 - combined_p),
            combined_risk_band=_risk_band(combined_p),
            advice=advice_result["advice"],
            advice_provider=advice_result["provider"],
            advice_model=advice_result["model"],
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion error: {str(e)}")
