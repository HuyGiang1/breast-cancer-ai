from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Dict, Any
from app.api.schemas import PredictionRequest, PredictionResponse, MultiModalResponse
from app.services.prediction import prediction_service
from app.services.prediction_dl import dl_prediction_service
import json
from pathlib import Path

router = APIRouter()


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

@router.post("/predict/", response_model=PredictionResponse)
def predict_diagnosis(request: PredictionRequest, model_name: str = None):
    try:
        result = prediction_service.predict(request, model_name=model_name)
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/image/", response_model=PredictionResponse)
async def predict_diagnosis_image(file: UploadFile = File(...), model_name: str = None):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        image_bytes = await file.read()
        result = dl_prediction_service.predict(image_bytes, model_name=model_name)
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/multimodal/", response_model=MultiModalResponse)
async def predict_multimodal(
    clinical_data: str = Form(...),
    image_file: UploadFile = File(...),
    ml_model: str = Form(None),
    dl_model: str = Form(None)
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
        dl_res = dl_prediction_service.predict(image_bytes, model_name=dl_model)
        
        # 3. Fusion Logic (Weighted Average or Rule-based)
        # Malignant = 1, Benign = 0
        p_ml = ml_res['probability'] if ml_res['prediction'] == 1 else (1 - ml_res['probability'])
        p_dl = dl_res['probability'] if dl_res['prediction'] == 1 else (1 - dl_res['probability'])
        
        # Give more weight to DL for visual evidence, but ML is strong for cellular detail
        combined_p = (p_ml * 0.4) + (p_dl * 0.6)
        is_mal = combined_p >= 0.5
        
        advice = _generate_combined_advice(ml_res, dl_res, combined_p)
        
        return MultiModalResponse(
            ml_result=PredictionResponse(**ml_res),
            dl_result=PredictionResponse(**dl_res),
            combined_diagnosis="Malignant" if is_mal else "Benign",
            combined_confidence=combined_p if is_mal else (1 - combined_p),
            advice=advice
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion error: {str(e)}")

def _generate_combined_advice(ml, dl, combined_p):
    if combined_p > 0.8:
        return "CRITICAL: Both clinical data and image analysis show high risk of malignancy. Recommend biopsy and immediate oncology referral."
    elif combined_p > 0.5:
        return "CAUTION: Mixed or moderate risk signals detected. While one indicator might be lower, the combined score suggests potential malignancy. Further diagnostic imaging (MRI/Ultrasound) is recommended."
    else:
        return "REASSURING: Both analysis modes indicate a low risk profile. Continue routine annual screenings and self-examinations."
